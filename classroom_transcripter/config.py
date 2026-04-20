"""Configurações, constantes e carregamento de variáveis de ambiente."""

import os
from pathlib import Path

from dotenv import load_dotenv

# ─── Constantes da API ──────────────────────────────────────────────────────

BASE_URL = "https://www.udemy.com"
API_BASE = f"{BASE_URL}/api-2.0"

HEADERS_BASE = {
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL,
}

# #4: LANG_PRIORITY agora é configurável via .env (LANG_PRIORITY=pt,en,es)
# Fallback para a lista padrão se a variável não estiver definida.
_DEFAULT_LANG_PRIORITY = ["pt", "pt-BR", "en", "en_US", "en_GB", "es"]


def get_lang_priority() -> list[str]:
    """Retorna a ordem de preferência de idiomas para legendas.

    Lê de LANG_PRIORITY no .env (ex: LANG_PRIORITY=pt,en,es).
    Se não definida, usa o padrão: pt, pt-BR, en, en_US, en_GB, es.
    """
    raw = os.getenv("LANG_PRIORITY", "")
    if raw.strip():
        return [lang.strip() for lang in raw.split(",") if lang.strip()]
    return list(_DEFAULT_LANG_PRIORITY)


# Mantém compatibilidade com imports diretos de LANG_PRIORITY existentes
# (ex: from .config import LANG_PRIORITY em utils.py).
# O valor é resolvido na inicialização; para comportamento dinâmico, use get_lang_priority().
LANG_PRIORITY = get_lang_priority()

# Rate limiting entre downloads de legendas (em segundos)
DOWNLOAD_DELAY = 0.3

# Tamanho de página para busca de currículo
CURRICULUM_PAGE_SIZE = 200


# ─── Carregamento do .env ───────────────────────────────────────────────────

def load_config() -> None:
    """Carrega variáveis do .env (se existir) e atualiza LANG_PRIORITY."""
    global LANG_PRIORITY
    load_dotenv()
    # Reavalia LANG_PRIORITY após carregar o .env para capturar o valor definido lá
    LANG_PRIORITY = get_lang_priority()


def resolve_cookies(cli_cookie: str | None = None) -> str | None:
    """Resolve cookies na ordem: CLI > .env (UDEMY_COOKIES) > .env (UDEMY_ACCESS_TOKEN).

    Inclui fallback de leitura direta do .env para casos onde
    o python-dotenv não consegue parsear aspas internas.
    """
    if cli_cookie:
        return cli_cookie

    cookie_data = os.getenv("UDEMY_COOKIES") or os.getenv("UDEMY_ACCESS_TOKEN")

    if not cookie_data or (";" not in cookie_data and len(cookie_data) < 50):
        fallback = (
            _read_env_raw("UDEMY_COOKIES")
            or _read_env_raw("UDEMY_ACCESS_TOKEN")
        )
        if fallback and len(fallback) > len(cookie_data or ""):
            cookie_data = fallback

    return cookie_data


def _read_env_raw(key: str) -> str | None:
    """Lê um valor do .env diretamente, sem depender do python-dotenv.

    Útil quando o valor contém aspas internas que confundem o parser
    (ex: access_token="abc..." dentro de aspas duplas).
    """
    env_path = Path(".env")
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            v = v.strip()
            if (v.startswith("'") and v.endswith("'")) or \
               (v.startswith('"') and v.endswith('"')):
                v = v[1:-1]
            return v

    return None