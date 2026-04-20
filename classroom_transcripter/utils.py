"""Funções utilitárias compartilhadas."""

import re

from .config import LANG_PRIORITY
from .models import Caption


def extract_slug(url_or_slug: str) -> str:
    """Extrai o slug do curso a partir de uma URL ou slug direto.

    Delega para UdemyPlatform por compatibilidade. Para suporte a outras
    plataformas, use platforms.detect_platform(url).extract_slug(url).

    >>> extract_slug("https://www.udemy.com/course/docker-basico/")
    'docker-basico'
    >>> extract_slug("docker-basico")
    'docker-basico'
    """
    # Importação local para evitar dependência circular (platforms → utils → platforms)
    from .platforms import UdemyPlatform
    return UdemyPlatform().extract_slug(url_or_slug)


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Remove caracteres inválidos para nomes de arquivo.

    >>> sanitize_filename('Aula 1: Introdução ao "Docker"')
    'Aula 1 Introdução ao Docker'
    """
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:max_length]


def pick_caption(
    captions: list[Caption],
    preferred_lang: str | None = None,
) -> Caption | None:
    """Escolhe a melhor legenda disponível baseado na preferência de idioma.

    Prioridade: idioma explícito > LANG_PRIORITY > primeira disponível.
    """
    if not captions:
        return None

    if preferred_lang:
        for cap in captions:
            if cap.locale.lower().startswith(preferred_lang.lower()):
                return cap

    for lang in LANG_PRIORITY:
        for cap in captions:
            if cap.locale.lower().startswith(lang.lower()):
                return cap

    return captions[0]