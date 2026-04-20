"""ClassroomTranscripter — extrai transcrições de cursos online (Udemy e mais).

Pipeline: download → format → enrich

Plataformas suportadas: Udemy (mais em breve: Alura, DIO)
"""

from .client import UdemyClient
from .downloader import download_transcripts, list_available_captions
from .formatters import BaseFormatter, ObsidianFormatter, PlainTextFormatter, get_formatter
from .models import Caption, DownloadResult, Lecture, Section
from .platforms import BasePlatform, UdemyPlatform, detect_platform, get_platform

__all__ = [
    # Cliente
    "UdemyClient",
    # Download
    "download_transcripts",
    "list_available_captions",
    # Formatadores
    "BaseFormatter",
    "PlainTextFormatter",
    "ObsidianFormatter",
    "get_formatter",
    # Modelos
    "Caption",
    "DownloadResult",
    "Lecture",
    "Section",
    # Plataformas
    "BasePlatform",
    "UdemyPlatform",
    "get_platform",
    "detect_platform",
]