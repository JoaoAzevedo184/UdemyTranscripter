"""Exceções customizadas do projeto."""


class UdemyTranscripterError(Exception):
    """Erro base do projeto."""


class AuthenticationError(UdemyTranscripterError):
    """Erro de autenticação (401)."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message
            or "Token inválido ou expirado. Gere novos cookies no navegador."
        )


class CloudflareBlockError(UdemyTranscripterError):
    """Bloqueio do Cloudflare (403 com challenge page)."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message
            or (
                "Acesso negado (Cloudflare). Possíveis causas:\n"
                "  1. Cookies expirados — copie novos do navegador\n"
                "  2. Curso não comprado — verifique se você tem acesso\n"
                "  3. cf_clearance ausente — copie TODOS os cookies do header Cookie"
            )
        )


class NoCaptionsError(UdemyTranscripterError):
    """Curso sem legendas/transcrições disponíveis."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message
            or "Nenhuma transcrição encontrada neste curso."
        )