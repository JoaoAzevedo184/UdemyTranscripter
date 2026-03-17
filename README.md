# 🎓 Udemy Transcripter

Ferramenta CLI que extrai transcrições de cursos da Udemy e transforma em material de estudo com IA.

**Pipeline:** `download` → `format` → `enrich`

## Quick Start

```bash
# Instalar
git clone https://github.com/JoaoAzevedo184/UdemyTranscripter.git
cd UdemyTranscripter
pip install -e .

# Configurar cookies da Udemy (uma vez)
python -m udemy_transcripter --setup

# Baixar transcrições formatadas para Obsidian
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --merge

# Enriquecer com IA (Groq gratuito)
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider groq
```

## Providers de IA

| Provider | Custo | Velocidade | Setup |
|----------|:---:|:---:|---|
| **Groq** | Gratuito | Ultra-rápido | [console.groq.com](https://console.groq.com) |
| **Gemini** | Gratuito | Rápido | [aistudio.google.com](https://aistudio.google.com) |
| **Ollama** | Gratuito | Local | `ollama pull llama3.1` |
| **Claude** | Pago | Rápido | [console.anthropic.com](https://console.anthropic.com) |

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [Configuração](docs/configuracao.md) | Cookies, API keys, `.env` |
| [Uso](docs/uso.md) | Download, enriquecimento, pipeline completo |
| [Obsidian](docs/obsidian.md) | Formato de saída, estrutura, estilo das notas |
| [Referência](docs/referencia.md) | Todas as flags da CLI, uso como biblioteca |
| [FAQ](docs/faq.md) | Perguntas frequentes e troubleshooting |

## Estrutura do projeto

```
udemy_transcripter/
├── udemy_transcripter/        # Pacote principal
│   ├── cli.py                 # Interface de linha de comando
│   ├── client.py              # Cliente HTTP (Cloudflare bypass)
│   ├── downloader.py          # Download e salvamento
│   ├── enricher.py            # Enriquecimento com IA
│   ├── formatters.py          # Formatadores (txt, obsidian)
│   ├── vtt.py                 # Parser de legendas WebVTT
│   └── ...
├── tests/                     # 69 testes unitários
├── docs/                      # Documentação
├── .env.example
├── pyproject.toml
└── README.md
```

## Testes

```bash
pip install -e ".[dev]"
pytest -v
```

## Notas

- Só funciona com cursos **que você comprou**
- Depende das legendas/captions disponibilizadas pelo instrutor
- Cookies expiram — se der 403, copie novos do navegador
- Respeite os termos de uso da Udemy (uso pessoal para estudo)