# 📖 Referência

## Flags da CLI

### Download

| Flag | Descrição |
|------|-----------|
| `--url`, `-u` | URL ou slug do curso |
| `--format`, `-f` | Formato: `txt` (padrão) ou `obsidian` |
| `--output`, `-o` | Diretório de saída (padrão: `./udemy_transcripts`) |
| `--lang`, `-l` | Idioma preferido (`pt`, `en`, `es`) |
| `--timestamps`, `-t` | Incluir timestamps `[HH:MM:SS]` |
| `--merge`, `-m` | Gerar arquivo único com todo o curso |
| `--list-langs` | Listar idiomas de legenda disponíveis |
| `--cookie`, `-c` | Cookie string (opcional se usar `.env`) |

### Enriquecimento com IA

| Flag | Descrição |
|------|-----------|
| `--enrich DIR` | Diretório com notas `.md` para enriquecer |
| `--provider` | `ollama` (padrão), `groq`, `gemini` ou `claude` |
| `--model` | Modelo (ex: `llama-3.3-70b-versatile`, `gemini-2.5-flash`) |
| `--api-key` | API key do provider (ou use `.env`) |
| `--ollama-url` | URL do Ollama (padrão: `http://localhost:11434`) |
| `--delay` | Delay entre chamadas em segundos (padrão: `1.0`) |
| `--dry-run` | Preview sem alterar arquivos |

### Geral

| Flag | Descrição |
|------|-----------|
| `--setup` | Configurar `.env` interativamente |
| `--debug` | Exibir detalhes das requisições |

---

## Uso como biblioteca

```python
from udemy_transcripter import (
    UdemyClient,
    download_transcripts,
    ObsidianFormatter,
)
from udemy_transcripter.enricher import create_provider, enrich_directory
from pathlib import Path

# Download
client = UdemyClient("access_token=...; cf_clearance=...")
result = download_transcripts(
    client,
    slug="docker-basico",
    formatter=ObsidianFormatter(),
    merge=True,
)

# Enriquecimento
provider = create_provider("groq", api_key="gsk_...")
enrich_directory(Path(result.output_dir), provider)
```

### API pública (`__init__.py`)

```python
from udemy_transcripter import (
    # Client
    UdemyClient,

    # Download
    download_transcripts,
    list_available_captions,

    # Formatadores
    BaseFormatter,
    PlainTextFormatter,
    ObsidianFormatter,
    get_formatter,

    # Modelos
    Caption,
    Lecture,
    Section,
    DownloadResult,
)
```

### Providers disponíveis

```python
from udemy_transcripter.enricher import create_provider

# Groq (gratuito)
provider = create_provider("groq", api_key="gsk_...")

# Gemini (gratuito)
provider = create_provider("gemini", api_key="AIzaSy_...")

# Ollama (local)
provider = create_provider("ollama", model="qwen3.5:9b")

# Claude (pago)
provider = create_provider("claude", api_key="sk-ant-...")

# Modelo customizado
provider = create_provider("groq", model="llama-3.1-8b-instant")
```

---

## Estrutura do projeto

```
udemy_transcripter/
├── udemy_transcripter/        # Pacote principal
│   ├── __init__.py            # API pública
│   ├── __main__.py            # python -m udemy_transcripter
│   ├── cli.py                 # Interface de linha de comando
│   ├── client.py              # Cliente HTTP (Cloudflare bypass via curl_cffi)
│   ├── config.py              # Constantes e carregamento de .env
│   ├── downloader.py          # Download e salvamento
│   ├── enricher.py            # Enriquecimento com IA (4 providers)
│   ├── exceptions.py          # Exceções customizadas
│   ├── formatters.py          # Formatadores (txt, obsidian)
│   ├── models.py              # Dataclasses do domínio
│   ├── setup.py               # Configuração interativa do .env
│   ├── utils.py               # Funções utilitárias
│   └── vtt.py                 # Parser de legendas WebVTT
├── tests/                     # 69 testes unitários
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_enricher.py
│   ├── test_formatters.py
│   ├── test_utils.py
│   └── test_vtt.py
├── docs/                      # Documentação
│   ├── configuracao.md
│   ├── uso.md
│   ├── obsidian.md
│   ├── referencia.md
│   └── faq.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```