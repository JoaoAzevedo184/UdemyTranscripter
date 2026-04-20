"""Interface de linha de comando."""

import argparse
from pathlib import Path

from .client import UdemyClient
from .config import load_config, resolve_cookies
from .downloader import download_transcripts, list_available_captions
from .enricher import create_provider, enrich_directory
from .exceptions import UdemyTranscripterError
from .formatters import FORMATTERS, get_formatter
from .setup import setup_env
from .utils import extract_slug


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos."""
    available_formats = ", ".join(FORMATTERS.keys())

    parser = argparse.ArgumentParser(
        prog="udemy_transcripter",
        description="Extrai transcrições de cursos online (Udemy e mais)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Exemplos:
  # Configurar cookies (primeira vez)
  python -m udemy_transcripter --setup

  # Baixar como Markdown para Obsidian
  python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --format obsidian

  # Retomar download interrompido
  python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --resume

  # Enriquecer notas com Ollama (local)
  python -m udemy_transcripter --enrich ./udemy_transcripts/MeuCurso --provider ollama

  # Enriquecer com modelo específico do Ollama
  python -m udemy_transcripter --enrich ./udemy_transcripts/MeuCurso \\
    --provider ollama --model qwen2.5:14b

  # Enriquecer com Claude API
  python -m udemy_transcripter --enrich ./udemy_transcripts/MeuCurso --provider claude

  # Enriquecer com Groq (gratuito, ultra-rápido)
  python -m udemy_transcripter --enrich ./udemy_transcripts/MeuCurso --provider groq

  # Enriquecer com Gemini (gratuito, sem cartão)
  python -m udemy_transcripter --enrich ./udemy_transcripts/MeuCurso --provider gemini

  # Preview do enriquecimento (sem alterar arquivos)
  python -m udemy_transcripter --enrich ./udemy_transcripts/MeuCurso --provider ollama --dry-run

Formatos disponíveis: {available_formats}
        """,
    )

    # ─── Download ───────────────────────────────────────────────────────
    parser.add_argument(
        "--cookie", "-c", default=None,
        help="String completa de cookies do navegador (opcional se usar .env)",
    )
    parser.add_argument(
        "--url", "-u", default=None,
        help="URL do curso ou slug (ex: python-bootcamp)",
    )
    parser.add_argument(
        "--output", "-o", default="./udemy_transcripts",
        help="Diretório de saída (padrão: ./udemy_transcripts)",
    )
    parser.add_argument(
        "--format", "-f", default="txt", choices=FORMATTERS.keys(),
        help="Formato de saída: txt (padrão) ou obsidian",
    )
    parser.add_argument(
        "--lang", "-l", default=None,
        help="Idioma preferido (ex: pt, en, es)",
    )
    parser.add_argument(
        "--timestamps", "-t", action="store_true",
        help="Incluir timestamps no texto",
    )
    parser.add_argument(
        "--merge", "-m", action="store_true",
        help="Gerar arquivo único com todo o curso (ideal para IA)",
    )
    parser.add_argument(
        "--resume", "-r", action="store_true",
        help="Retomar download interrompido (pula aulas já baixadas)",
    )
    parser.add_argument(
        "--list-langs", action="store_true",
        help="Apenas listar idiomas de legenda disponíveis",
    )

    # ─── Enriquecimento com IA ──────────────────────────────────────────
    parser.add_argument(
        "--enrich", metavar="DIR", default=None,
        help="Enriquecer notas .md do diretório com IA",
    )
    parser.add_argument(
        "--provider", default="ollama", choices=["ollama", "claude", "groq", "gemini"],
        help="Provider de IA: ollama (padrão), claude, groq ou gemini",
    )
    parser.add_argument(
        "--model", default=None,
        help="Modelo (ex: llama3.1, llama-3.3-70b-versatile, claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="API key (para claude: ANTHROPIC_API_KEY, para groq: GROQ_API_KEY)",
    )
    parser.add_argument(
        "--ollama-url", default=None,
        help="URL do Ollama (padrão: http://localhost:11434)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Delay entre chamadas de IA em segundos (padrão: 1.0)",
    )
    parser.add_argument(
        "--timeout", type=int, default=900,
        help="Timeout por requisição em segundos (padrão: 900, relevante para Ollama local)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview do enriquecimento sem alterar arquivos",
    )

    # ─── Geral ──────────────────────────────────────────────────────────
    parser.add_argument(
        "--setup", action="store_true",
        help="Criar/atualizar arquivo .env interativamente",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Exibir detalhes das requisições para depuração",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal da CLI.

    Args:
        argv: Argumentos (usa sys.argv se None).

    Returns:
        Código de saída (0 = sucesso, 1 = erro).
    """
    load_config()
    parser = build_parser()
    args = parser.parse_args(argv)

    # ─── Setup interativo ───────────────────────────────────────────────
    if args.setup:
        setup_env()
        return 0

    # ─── Enriquecimento com IA ──────────────────────────────────────────
    if args.enrich:
        return _handle_enrich(args)

    # ─── Download ───────────────────────────────────────────────────────
    return _handle_download(args, parser)


def _handle_enrich(args: argparse.Namespace) -> int:
    """Executa o enriquecimento de notas com IA."""
    enrich_dir = Path(args.enrich)
    if not enrich_dir.is_dir():
        print(f"✗ Diretório não encontrado: {enrich_dir}")
        return 1

    try:
        provider = create_provider(
            provider_name=args.provider,
            model=args.model,
            api_key=args.api_key,
            base_url=args.ollama_url,
            timeout=args.timeout,
        )
    except ValueError as e:
        print(f"✗ {e}")
        return 1

    try:
        enrich_directory(
            directory=enrich_dir,
            provider=provider,
            delay=args.delay,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"\n✗ Erro no enriquecimento: {e}")
        if args.debug:
            raise
        return 1

    return 0


def _handle_download(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Executa o download de transcrições."""
    cookie_data = resolve_cookies(args.cookie)

    if not cookie_data:
        print("✗ Cookies não encontrados.")
        print("  Opções:")
        print("    1. Crie um .env:  python -m udemy_transcripter --setup")
        print("    2. Passe via CLI: --cookie 'SUA_COOKIE_STRING'")
        return 1

    if not args.url:
        parser.error("--url é obrigatório (a menos que use --setup ou --enrich)")

    slug = extract_slug(args.url)
    client = UdemyClient(cookie_data, debug=args.debug)
    formatter = get_formatter(args.format)

    if args.debug:
        display = cookie_data[:30] + "..." if len(cookie_data) > 30 else cookie_data
        print(f"[DEBUG] Cookie data: {display} ({len(cookie_data)} chars)")
        print(f"[DEBUG] Slug: {slug}")
        print(f"[DEBUG] Formato: {args.format}")
        print(f"[DEBUG] Resume: {args.resume}")
        print()

    try:
        if args.list_langs:
            list_available_captions(client, slug)
        else:
            download_transcripts(
                client=client,
                slug=slug,
                output_dir=args.output,
                lang=args.lang,
                with_timestamps=args.timestamps,
                merge=args.merge,
                formatter=formatter,
                resume=args.resume,
            )
    except UdemyTranscripterError as e:
        print(f"\n✗ {e}")
        if args.debug:
            raise
        return 1

    return 0