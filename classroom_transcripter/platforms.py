"""Abstração de plataformas de cursos online.

Permite que o ClassroomTranscripter suporte múltiplas plataformas
(Udemy, Alura, DIO, etc.) através de uma interface comum.

Como adicionar uma nova plataforma:
1. Crie uma subclasse de BasePlatform
2. Implemente os métodos abstratos
3. Registre no dicionário PLATFORMS ao final deste arquivo

Atualmente implementado:
- UdemyPlatform (padrão)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PlatformInfo:
    """Metadados de uma plataforma suportada."""

    name: str
    base_url: str
    description: str
    requires_auth: bool = True


class BasePlatform(ABC):
    """Interface base para plataformas de cursos online.

    Cada plataforma deve saber:
    - Extrair um slug/identificador de curso a partir de uma URL
    - Fornecer suas informações básicas (nome, URL, etc.)
    - Indicar se requer autenticação por cookies
    """

    @abstractmethod
    def info(self) -> PlatformInfo:
        """Retorna metadados da plataforma."""

    @abstractmethod
    def extract_slug(self, url: str) -> str:
        """Extrai o slug/identificador do curso a partir de uma URL.

        Args:
            url: URL completa do curso ou slug direto.

        Returns:
            Slug/identificador do curso.
        """

    @abstractmethod
    def matches_url(self, url: str) -> bool:
        """Verifica se a URL pertence a esta plataforma.

        Args:
            url: URL a verificar.

        Returns:
            True se a URL pertence a esta plataforma.
        """


class UdemyPlatform(BasePlatform):
    """Implementação para a plataforma Udemy."""

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="Udemy",
            base_url="https://www.udemy.com",
            description="Plataforma de cursos online com autenticação por cookies",
            requires_auth=True,
        )

    def extract_slug(self, url: str) -> str:
        """Extrai o slug do curso a partir de uma URL da Udemy ou slug direto.

        >>> UdemyPlatform().extract_slug("https://www.udemy.com/course/docker-basico/")
        'docker-basico'
        >>> UdemyPlatform().extract_slug("docker-basico")
        'docker-basico'
        """
        import re
        match = re.search(r"udemy\.com/course/([^/?#]+)", url)
        if match:
            return match.group(1)
        return url.strip("/")

    def matches_url(self, url: str) -> bool:
        """Verifica se a URL pertence à Udemy."""
        return "udemy.com" in url


# ─── Registry de plataformas ────────────────────────────────────────────────

PLATFORMS: dict[str, type[BasePlatform]] = {
    "udemy": UdemyPlatform,
    # Futuras plataformas:
    # "alura": AluraPlatform,
    # "dio": DioPlatform,
}


def get_platform(name: str) -> BasePlatform:
    """Retorna uma instância da plataforma pelo nome.

    Args:
        name: Nome da plataforma (ex: "udemy").

    Raises:
        ValueError: Se a plataforma não for suportada.
    """
    cls = PLATFORMS.get(name.lower())
    if cls is None:
        available = ", ".join(PLATFORMS.keys())
        raise ValueError(
            f"Plataforma '{name}' não suportada. Disponíveis: {available}"
        )
    return cls()


def detect_platform(url: str) -> BasePlatform:
    """Detecta automaticamente a plataforma a partir da URL.

    Itera sobre as plataformas registradas e retorna a primeira que
    reconhecer a URL. Retorna UdemyPlatform como fallback.

    Args:
        url: URL do curso.

    Returns:
        Instância da plataforma detectada.
    """
    for cls in PLATFORMS.values():
        platform = cls()
        if platform.matches_url(url):
            return platform
    # Fallback para Udemy (comportamento original)
    return UdemyPlatform()