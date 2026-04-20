"""Enriquecimento de transcrições com IA.

Lê arquivos .md gerados pelo Obsidian formatter, envia para uma LLM
e reescreve com foco educativo: estrutura visual, seções escaneáveis,
blocos de código, emojis nos headings, perguntas de revisão.

Providers suportados:
- Ollama (local, gratuito)
- Groq (nuvem, gratuito, ultra-rápido)
- Gemini (nuvem, gratuito, Google)
- Claude API (Anthropic, pago)
"""

from __future__ import annotations

import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# ─── Resultado ──────────────────────────────────────────────────────────────


@dataclass
class EnrichResult:
    """Resultado do enriquecimento."""

    total_files: int
    enriched: int
    skipped: int
    errors: int


# ─── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Você é um assistente educacional especializado em transformar transcrições brutas \
de aulas em notas de estudo visualmente claras, didáticas e fáceis de escanear.

## Sua tarefa

Receba a transcrição (gerada a partir de áudio) de uma aula e reescreva como uma nota \
de estudo completa em Markdown, seguindo o formato visual descrito abaixo.

## Regras obrigatórias

1. **Mantenha o frontmatter YAML** (bloco `---`) EXATAMENTE como está, sem alterar
2. **Mantenha o callout de navegação** (`> [!tip] Navegação`) se existir
3. **Idioma**: responda no mesmo idioma da transcrição original
4. **Limpeza da fala**: remova vícios de linguagem (né, ahn, hum), repetições, frases \
incompletas e gaguejos. Transforme a linguagem oral em texto escrito claro e direto
5. **Não invente** informações que não estão na transcrição (zero alucinação)
6. **Não perca** conteúdo relevante — a nota deve ser exaustiva
7. Entregue APENAS o Markdown final. Sem introduções como "Aqui está a nota" ou "Claro"

## Formato visual obrigatório

### Emojis nos headings
Use emojis temáticos no início de cada seção principal (nível #):
- `# 📚 Visão Geral da Aula` — resumo do tema
- `# 🎯 Objetivos` — o que o aluno vai aprender
- `# 🧠 Conceitos` — conteúdo principal
- `# 🧾 Resumo da Aula` — pontos-chave
- `# 🔁 Perguntas para Revisão` — fixação
- `# ✍️ Anotações` — espaço do aluno (manter vazio)
- Use outros emojis quando apropriado (👨‍🏫, ⚙️, 🧩, 👥, etc.)

### Separadores visuais
Use `---` (horizontal rule) entre TODAS as seções principais para criar \
separação visual clara. Cada bloco `#` deve ser precedido por `---`.

### Estrutura das seções
- **Seções curtas e escaneáveis** — máximo 5-8 linhas por bloco
- **Um conceito por subseção** — se a aula fala sobre 5 conceitos, crie 5 subseções \
separadas com `##` ou `###`, cada uma com sua explicação breve
- **Bullet points curtos** — use listas com termos em **negrito** seguidos de explicação
- **Listas de checagem** — use ✅ e ❌ para indicar "foco do curso" vs "fora do escopo"

### Estrutura obrigatória do documento

```
[frontmatter YAML — não alterar]
[callout de navegação — se existir]
---
# 📚 Visão Geral da Aula
[1-2 parágrafos resumindo o tema central]
---
# 🎯 Objetivos / O que será aprendido
[lista de bullet points]
---
# 🧠 [Seções de conteúdo com emojis]
[conteúdo organizado por tópicos, com subsections ###]
[cada conceito em sua própria subseção]
[blocos de código quando houver comandos/código]
---
# 🧾 Resumo da Aula
[3-5 bullet points com as lições principais]
---
# 🔁 Perguntas para Revisão
[3-5 perguntas numeradas para fixação]
---
# ✍️ Anotações
> [!note] Espaço para suas anotações
>
> -
> -
> -
```

### Enriquecimento
- **Termos-chave** em negrito na primeira ocorrência
- **Blocos de código** (`bash`, `yaml`, `dockerfile`, etc.) quando a aula mencionar comandos
- **Callouts do Obsidian** quando agregar valor:
  - `> [!tip]` para dicas práticas
  - `> [!warning]` para pontos de atenção
  - `> [!info]` para conceitos fundamentais
  - `> [!example]` para exemplos e analogias
- Se a aula apresentar uma pessoa (instrutor), crie uma seção `# 👨‍🏫 Sobre o Instrutor`

### O que NÃO fazer
- Não use parágrafos longos — quebre em blocos curtos
- Não use a seção `## Transcrição` — reorganize todo o conteúdo por tópicos
- Não altere o frontmatter YAML
- Não adicione código incorreto ou inventado
- Não use o formato TL;DR — use `# 📚 Visão Geral da Aula` no lugar
"""

ENRICH_USER_TEMPLATE = """\
## Contexto do curso
- **Curso**: {course_title}
- **Seção**: {section_title}
- **Aula**: {lecture_title}

## Transcrição original (nota Obsidian)

{content}

---

Reescreva esta nota seguindo o formato visual com emojis nos headings, \
separadores entre seções, blocos curtos e escaneáveis. \
Reorganize TODO o conteúdo por tópicos — não mantenha a seção "## Transcrição"."""


# ─── Providers ──────────────────────────────────────────────────────────────


class LLMProvider(ABC):
    """Interface para provedores de LLM."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Envia prompt e retorna resposta da LLM."""

    @abstractmethod
    def name(self) -> str:
        """Nome do provider para logs."""


class OllamaProvider(LLMProvider):
    """Provider local via Ollama API."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        timeout: int = 900,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def name(self) -> str:
        return f"ollama/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_ctx": 16384,
                },
            },
            timeout=self.timeout,
        )

        if not resp.ok:
            try:
                error_msg = resp.json().get("error", resp.text[:500])
            except Exception:
                error_msg = resp.text[:500]
            raise RuntimeError(f"Ollama {resp.status_code}: {error_msg}")

        return resp.json()["message"]["content"]


class ClaudeProvider(LLMProvider):
    """Provider via Anthropic Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        raw_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        # Limpa aspas que podem vir do .env
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else None
        self.model = model
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY não encontrada. "
                "Defina via --api-key ou no .env."
            )

    def name(self) -> str:
        return f"claude/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 8192,
                "system": system,
                "messages": [
                    {"role": "user", "content": user},
                ],
            },
            timeout=300,
        )

        # Mostra erro real da API em vez de "400 Bad Request"
        if not resp.ok:
            try:
                error_data = resp.json()
                error_msg = error_data.get("error", {}).get("message", resp.text)
                error_type = error_data.get("error", {}).get("type", "unknown")
            except Exception:
                error_msg = resp.text[:500]
                error_type = "unknown"

            raise RuntimeError(
                f"Claude API {resp.status_code} ({error_type}): {error_msg}"
            )

        data = resp.json()
        return data["content"][0]["text"]


class GroqProvider(LLMProvider):
    """Provider via Groq API (OpenAI-compatible).

    Groq usa LPUs (Language Processing Units) para inferência ultra-rápida
    de modelos open source. Tem tier gratuito sem cartão de crédito.

    Modelos recomendados:
    - llama-3.3-70b-versatile (padrão, melhor qualidade)
    - llama-3.1-8b-instant (mais rápido)
    - deepseek-r1-distill-llama-70b (raciocínio/código)
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        raw_key = api_key or os.getenv("GROQ_API_KEY")
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else None
        self.model = model
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY não encontrada. "
                "Obtenha em console.groq.com e defina via --api-key ou no .env."
            )

    def name(self) -> str:
        return f"groq/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        max_retries = 3
        for attempt in range(max_retries + 1):
            resp = requests.post(
                self.GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.3,
                    "max_completion_tokens": 8192,
                },
                timeout=300,
            )

            # Rate limit — espera e tenta novamente
            if resp.status_code == 429 and attempt < max_retries:
                retry_after = resp.headers.get("retry-after", "60")
                wait = min(int(float(retry_after)), 120)
                print(f"\n   ⏳ Rate limit atingido. Aguardando {wait}s... ", end="", flush=True)
                time.sleep(wait)
                print("retomando")
                continue

            if not resp.ok:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get("error", {}).get("message", resp.text[:500])
                except Exception:
                    error_msg = resp.text[:500]

                if resp.status_code == 429:
                    raise RuntimeError(
                        f"Groq rate limit excedido após {max_retries} tentativas. "
                        "Aumente --delay ou tente novamente amanhã (limites resetam diariamente)."
                    )
                raise RuntimeError(f"Groq API {resp.status_code}: {error_msg}")

            data = resp.json()
            return data["choices"][0]["message"]["content"]

        raise RuntimeError("Groq: número máximo de tentativas excedido.")


class GeminiProvider(LLMProvider):
    """Provider via Google Gemini API (OpenAI-compatible endpoint).

    Tier gratuito sem cartão de crédito. API key em aistudio.google.com.

    Modelos recomendados:
    - gemini-2.5-flash (padrão, melhor custo-benefício no free tier)
    - gemini-2.5-pro (mais capaz, limite menor: 5 RPM / 100 RPD)
    - gemini-2.5-flash-lite (mais leve, limites mais altos)
    """

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ):
        raw_key = api_key or os.getenv("GEMINI_API_KEY")
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else None
        self.model = model
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY não encontrada. "
                "Obtenha em aistudio.google.com e defina via --api-key ou no .env."
            )

    def name(self) -> str:
        return f"gemini/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        max_retries = 3
        for attempt in range(max_retries + 1):
            resp = requests.post(
                self.GEMINI_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.3,
                    "max_completion_tokens": 8192,
                },
                timeout=300,
            )

            # Rate limit — espera e tenta novamente
            if resp.status_code == 429 and attempt < max_retries:
                retry_after = resp.headers.get("retry-after", "60")
                wait = min(int(float(retry_after)), 120)
                print(f"\n   ⏳ Rate limit atingido. Aguardando {wait}s... ", end="", flush=True)
                time.sleep(wait)
                print("retomando")
                continue

            if not resp.ok:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get("error", {}).get("message", resp.text[:500])
                except Exception:
                    error_msg = resp.text[:500]

                if resp.status_code == 429:
                    raise RuntimeError(
                        f"Gemini rate limit excedido após {max_retries} tentativas. "
                        "Aumente --delay ou tente novamente amanhã."
                    )
                raise RuntimeError(f"Gemini API {resp.status_code}: {error_msg}")

            data = resp.json()
            return data["choices"][0]["message"]["content"]

        raise RuntimeError("Gemini: número máximo de tentativas excedido.")


def create_provider(
    provider_name: str,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: int = 900,
) -> LLMProvider:
    """Cria um provider de LLM pelo nome.

    Args:
        provider_name: "ollama", "claude", "groq" ou "gemini"
        model: Modelo a usar (padrão depende do provider)
        api_key: API key (necessário para claude, groq e gemini)
        base_url: URL base (para ollama customizado)
        timeout: Timeout por requisição em segundos (relevante para ollama)
    """
    if provider_name == "ollama":
        kwargs: dict = {"timeout": timeout}
        if model:
            kwargs["model"] = model
        if base_url:
            kwargs["base_url"] = base_url
        return OllamaProvider(**kwargs)

    elif provider_name == "claude":
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return ClaudeProvider(**kwargs)

    elif provider_name == "groq":
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return GroqProvider(**kwargs)

    elif provider_name == "gemini":
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return GeminiProvider(**kwargs)

    else:
        raise ValueError(
            f"Provider '{provider_name}' não suportado. "
            "Use 'ollama', 'claude', 'groq' ou 'gemini'."
        )


# ─── Lógica de Enriquecimento ──────────────────────────────────────────────


_ENRICHED_MARKER = "<!-- enriched-by:"


def is_enriched(content: str) -> bool:
    """Verifica se o arquivo já foi enriquecido."""
    return _ENRICHED_MARKER in content


def _extract_frontmatter(content: str) -> tuple[str, str]:
    """Separa frontmatter YAML do corpo.

    Returns:
        (frontmatter_com_delimitadores, corpo)
    """
    if not content.startswith("---"):
        return "", content

    end = content.find("---", 3)
    if end == -1:
        return "", content

    end += 3
    return content[:end], content[end:]


def _extract_metadata_from_frontmatter(frontmatter: str) -> dict[str, str]:
    """Extrai campos básicos do frontmatter para contexto."""
    meta = {}
    for line in frontmatter.splitlines():
        for key in ("course", "section"):
            if line.strip().startswith(f"{key}:"):
                val = line.split(":", 1)[1].strip().strip('"').strip("'")
                meta[key] = val
    return meta


def enrich_file(
    file_path: Path,
    provider: LLMProvider,
    dry_run: bool = False,
) -> bool:
    """Enriquece um único arquivo .md com IA.

    Args:
        file_path: Caminho do arquivo.
        provider: Provider de LLM.
        dry_run: Se True, não salva (apenas mostra o que faria).

    Returns:
        True se enriqueceu, False se pulou.
    """
    content = file_path.read_text(encoding="utf-8")

    # Pula se já enriquecido
    if is_enriched(content):
        return False

    # Pula arquivos especiais
    if file_path.name.startswith("_"):
        return False

    # Extrai metadados para contexto
    frontmatter, body = _extract_frontmatter(content)
    meta = _extract_metadata_from_frontmatter(frontmatter)

    # Extrai título da aula do heading
    title_match = re.search(r"^# (.+)$", body, re.MULTILINE)
    lecture_title = title_match.group(1) if title_match else file_path.stem

    # Monta o prompt
    user_prompt = ENRICH_USER_TEMPLATE.format(
        course_title=meta.get("course", "Desconhecido"),
        section_title=meta.get("section", "Desconhecida"),
        lecture_title=lecture_title,
        content=content,
    )

    if dry_run:
        print(f"   [DRY RUN] Enviaria {file_path.name} para {provider.name()}")
        return True

    # Chama a LLM
    enriched = provider.complete(SYSTEM_PROMPT, user_prompt)

    # Garante que o frontmatter original foi preservado
    # (a LLM pode ter alterado — reconstrói se necessário)
    if frontmatter and not enriched.strip().startswith("---"):
        enriched = frontmatter + "\n" + enriched

    # Adiciona marcador de enriquecimento
    marker = f"{_ENRICHED_MARKER} {provider.name()} -->\n"
    enriched = enriched.rstrip() + "\n\n" + marker

    # Salva
    file_path.write_text(enriched, encoding="utf-8")
    return True


def enrich_directory(
    directory: Path,
    provider: LLMProvider,
    delay: float = 1.0,
    dry_run: bool = False,
) -> EnrichResult:
    """Enriquece todos os .md de um diretório de curso.

    Args:
        directory: Diretório raiz do curso (saída do download).
        provider: Provider de LLM.
        delay: Delay entre chamadas (segundos).
        dry_run: Se True, não salva alterações.

    Returns:
        EnrichResult com estatísticas.
    """
    md_files = sorted(directory.rglob("*.md"))

    # Filtra arquivos especiais (_MOC.md, _index.md, _CURSO_COMPLETO.md)
    md_files = [f for f in md_files if not f.name.startswith("_")]

    total = len(md_files)
    enriched = 0
    skipped = 0
    errors = 0

    print(f"\n🤖 Enriquecendo {total} notas com {provider.name()}")
    if dry_run:
        print("   [DRY RUN] Nenhum arquivo será alterado\n")

    for i, file_path in enumerate(md_files, 1):
        relative = file_path.relative_to(directory)
        print(f"   [{i}/{total}] {relative}", end="")

        try:
            if is_enriched(file_path.read_text(encoding="utf-8")):
                print(" (já enriquecido, pulando)")
                skipped += 1
                continue

            result = enrich_file(file_path, provider, dry_run=dry_run)
            if result:
                enriched += 1
                print(" ✓")
            else:
                skipped += 1
                print(" (pulado)")

            if not dry_run and i < total:
                time.sleep(delay)

        except Exception as e:
            errors += 1
            print(f" ✗ {e}")

    print("\n✓ Enriquecimento concluído!")
    print(f"  Enriquecidos: {enriched}")
    if skipped:
        print(f"  Pulados: {skipped}")
    if errors:
        print(f"  Erros: {errors}")

    return EnrichResult(
        total_files=total,
        enriched=enriched,
        skipped=skipped,
        errors=errors,
    )