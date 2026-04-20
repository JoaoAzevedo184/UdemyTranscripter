"""Cliente HTTP para a API interna da Udemy.

Usa curl_cffi para imitar o TLS fingerprint do Chrome,
necessário para passar pela proteção Cloudflare.
"""

import sys

from curl_cffi import requests as cffi_requests

from .config import API_BASE, CURRICULUM_PAGE_SIZE, HEADERS_BASE
from .exceptions import AuthenticationError, CloudflareBlockError
from .models import Caption, Lecture, Section


class UdemyClient:
    """Cliente autenticado para a API da Udemy."""

    def __init__(self, cookie_data: str, debug: bool = False):
        self.session = cffi_requests.Session(impersonate="chrome")
        self.debug = debug
        self._setup_auth(cookie_data)

    # ─── Autenticação ───────────────────────────────────────────────────

    def _setup_auth(self, cookie_data: str) -> None:
        """Configura headers de autenticação a partir dos cookies."""
        cookie_data = cookie_data.strip()
        if cookie_data.lower().startswith("cookie:"):
            cookie_data = cookie_data[7:].strip()

        # Remove caracteres non-ASCII que quebram curl_cffi
        # (ex: … U+2026 de strings truncadas no terminal)
        cookie_data = cookie_data.encode("ascii", errors="ignore").decode("ascii")

        headers = dict(HEADERS_BASE)

        if ";" in cookie_data:
            # Cookie string completa do navegador
            headers["Cookie"] = cookie_data
            access_token = self._extract_cookie_value(cookie_data, "access_token")
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
                headers["X-Udemy-Authorization"] = f"Bearer {access_token}"
            else:
                print("✗ Erro: access_token não encontrado nos cookies.")
                print("  A cookie string pode ter sido truncada ao colar no terminal.")
                print("  Dicas:")
                print("    - No navegador, clique com botão direito no valor → 'Copy value'")
                print("    - Ou cole o cookie direto no arquivo .env manualmente")
                print("    - Verifique se o .env contém 'access_token=' na string")
                sys.exit(1)
        else:
            # Token simples
            token = cookie_data.strip('"').strip("'")
            headers["Authorization"] = f"Bearer {token}"
            headers["X-Udemy-Authorization"] = f"Bearer {token}"
            headers["Cookie"] = f"access_token={token}"

        self.session.headers.update(headers)

    @staticmethod
    def _extract_cookie_value(cookie_string: str, name: str) -> str | None:
        """Extrai o valor de um cookie específico da string."""
        for pair in cookie_string.split(";"):
            pair = pair.strip()
            if pair.startswith(f"{name}="):
                raw = pair.partition("=")[2].strip()
                if raw.startswith('"') and raw.endswith('"'):
                    raw = raw[1:-1]
                return raw
        return None

    # ─── HTTP ───────────────────────────────────────────────────────────

    def _get(self, url: str, params: dict | None = None) -> dict:
        """Executa GET autenticado com tratamento de erros."""
        if self.debug:
            print(f"  [DEBUG] GET {url}")
            if params:
                print(f"  [DEBUG] Params: {params}")

        resp = self.session.get(url, params=params)

        if self.debug:
            print(f"  [DEBUG] Status: {resp.status_code}")
            if resp.status_code >= 400:
                print(f"  [DEBUG] Response: {resp.text[:500]}")

        if resp.status_code == 403:
            raise CloudflareBlockError()
        if resp.status_code == 401:
            raise AuthenticationError()

        resp.raise_for_status()
        return resp.json()

    # ─── Endpoints ──────────────────────────────────────────────────────

    def get_course_info(self, slug: str) -> tuple[int, str]:
        """Retorna (course_id, title) a partir do slug do curso."""
        data = self._get(
            f"{API_BASE}/courses/{slug}/",
            params={"fields[course]": "id,title,locale"},
        )
        return data["id"], data["title"]

    def get_curriculum(self, course_id: int) -> list[Section]:
        """Busca toda a grade curricular organizada por seções."""
        sections: list[Section] = []
        current_section = Section(title="Introdução", index=0)

        page_url = f"{API_BASE}/courses/{course_id}/subscriber-curriculum-items/"
        params: dict | None = {
            "page_size": CURRICULUM_PAGE_SIZE,
            "fields[lecture]": "id,title,object_index,asset",
            "fields[chapter]": "title,object_index",
            "fields[asset]": "captions",
        }

        while page_url:
            data = self._get(page_url, params=params)
            params = None  # Próximas páginas já têm params na URL

            for item in data.get("results", []):
                item_class = item.get("_class")

                if item_class == "chapter":
                    if current_section.lectures:
                        sections.append(current_section)
                    current_section = Section(
                        title=item.get("title", "Sem título"),
                        index=item.get("object_index", 0),
                    )
                elif item_class == "lecture":
                    lecture = self._parse_lecture(item)
                    current_section.lectures.append(lecture)

            page_url = data.get("next")

        if current_section.lectures:
            sections.append(current_section)

        return sections

    @staticmethod
    def _parse_lecture(item: dict) -> Lecture:
        """Converte um item da API em um objeto Lecture."""
        captions = [
            Caption(
                locale=cap.get("locale_id", "unknown"),
                url=cap.get("url", ""),
                label=cap.get("title", cap.get("locale_id", "")),
            )
            for cap in item.get("asset", {}).get("captions", [])
        ]
        return Lecture(
            id=item["id"],
            title=item.get("title", "Sem título"),
            object_index=item.get("object_index", 0),
            captions=captions,
        )