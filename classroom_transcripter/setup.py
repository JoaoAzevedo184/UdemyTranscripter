"""Configuração interativa do .env."""

from pathlib import Path


def setup_env() -> None:
    """Cria ou atualiza o arquivo .env interativamente."""
    env_path = Path(".env")
    existing = _load_existing_env(env_path)

    if env_path.exists():
        print(f"📄 Arquivo .env encontrado em: {env_path.resolve()}")
        current = existing.get("UDEMY_COOKIES", existing.get("UDEMY_ACCESS_TOKEN", ""))
        if current:
            print(f"   Cookies atuais: {current[:30]}... ({len(current)} chars)")
    else:
        print("📄 Criando novo arquivo .env")

    _print_instructions()
    cookies = input("Cole a string completa de cookies (Enter para manter): ").strip()

    if not cookies:
        if existing.get("UDEMY_COOKIES") or existing.get("UDEMY_ACCESS_TOKEN"):
            print("✓ Cookies mantidos.")
            return
        print("✗ Nenhum cookie fornecido.")
        return

    # Limpa e salva
    if cookies.lower().startswith("cookie:"):
        cookies = cookies[7:].strip()

    # Valida se a string parece completa
    if "access_token=" not in cookies:
        print("⚠ Aviso: 'access_token' não encontrado na cookie string.")
        print("  A string pode ter sido truncada ao colar no terminal.")
        print("  Dica: cole diretamente no arquivo .env com um editor de texto.")
        confirm = input("  Salvar mesmo assim? (s/N): ").strip().lower()
        if confirm != "s":
            print("  Cancelado.")
            return

    existing.pop("UDEMY_ACCESS_TOKEN", None)
    existing["UDEMY_COOKIES"] = cookies

    _write_env_file(env_path, existing)
    _ensure_gitignore()

    print(f"✓ Cookies salvos em: {env_path.resolve()}")
    print("  Agora você pode rodar sem --cookie:")
    print("  python -m udemy_transcripter --url 'https://udemy.com/course/meu-curso/'")


def _print_instructions() -> None:
    """Exibe instruções de como obter os cookies."""
    print()
    print("  Como obter os cookies:")
    print("    1. Abra a Udemy no navegador (logado)")
    print("    2. DevTools (F12) → aba Network")
    print("    3. Recarregue a página do curso")
    print("    4. Clique em alguma requisição para 'www.udemy.com'")
    print("    5. Em 'Request Headers', copie o valor do header 'Cookie'")
    print()


def _load_existing_env(path: Path) -> dict[str, str]:
    """Lê pares chave=valor de um .env existente."""
    existing: dict[str, str] = {}
    if not path.exists():
        return existing

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            existing[key.strip()] = value.strip()

    return existing


def _write_env_file(path: Path, data: dict[str, str]) -> None:
    """Escreve o .env com os dados fornecidos."""
    lines = [
        "# Udemy Transcript Extractor - Configuração",
        "# Obtenha os cookies em: DevTools (F12) → Network → Request Headers → Cookie",
        "# IMPORTANTE: Os cookies expiram. Se der erro 403, gere novos.",
        "",
    ]
    for key, value in data.items():
        # Usa aspas simples — a cookie string contém aspas duplas internas
        if ";" in value or " " in value or '"' in value:
            lines.append(f"{key}='{value}'")
        else:
            lines.append(f"{key}={value}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ensure_gitignore() -> None:
    """Garante que .env esteja no .gitignore."""
    gitignore = Path(".gitignore")

    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".env" not in content:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write("\n.env\n")
            print("   Adicionado .env ao .gitignore")
    else:
        gitignore.write_text(".env\n", encoding="utf-8")
        print("   Criado .gitignore com .env")