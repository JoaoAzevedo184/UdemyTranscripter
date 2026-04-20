"""Formatadores de saída para transcrições.

Cada formatador define como os arquivos são estruturados e salvos.
Permite extensão futura (ex: Notion, Anki, HTML).
"""

from __future__ import annotations

import re  # #3: import movido para o topo (estava duplicado dentro de funções)
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

from .models import Lecture, Section
from .utils import sanitize_filename


class BaseFormatter(ABC):
    """Interface base para formatadores de saída."""

    @abstractmethod
    def file_extension(self) -> str:
        """Extensão dos arquivos gerados (ex: '.txt', '.md')."""

    @abstractmethod
    def format_lecture(
        self,
        lecture: Lecture,
        section: Section,
        transcript: str,
        course_title: str,
        slug: str,
        prev_lecture: Lecture | None = None,
        next_lecture: Lecture | None = None,
    ) -> str:
        """Formata o conteúdo de uma aula individual."""

    @abstractmethod
    def format_merged(
        self,
        sections: list[Section],
        transcripts: dict[int, str],
        course_title: str,
        total_downloaded: int,
    ) -> str:
        """Formata o arquivo mesclado com todo o curso."""

    def save_extras(
        self,
        course_dir: Path,
        sections: list[Section],
        transcripts: dict[int, str],
        course_title: str,
        slug: str,
    ) -> None:
        """Hook para salvar arquivos extras (MOC, índices, etc.).

        Implementação padrão não faz nada.
        """

    def get_lecture_filename(self, lecture: Lecture) -> str:
        """Nome do arquivo para uma aula."""
        name = f"{lecture.object_index:03d} - {sanitize_filename(lecture.title)}"
        return f"{name}{self.file_extension()}"

    def get_section_dirname(self, section: Section) -> str:
        """Nome do diretório para uma seção."""
        return f"{section.index:02d} - {sanitize_filename(section.title)}"

    def get_merged_filename(self) -> str:
        """Nome do arquivo mesclado."""
        return f"_CURSO_COMPLETO{self.file_extension()}"


# ─── Plain Text ─────────────────────────────────────────────────────────────


class PlainTextFormatter(BaseFormatter):
    """Formatador de texto simples (.txt). Comportamento original."""

    def file_extension(self) -> str:
        return ".txt"

    def format_lecture(
        self,
        lecture: Lecture,
        section: Section,
        transcript: str,
        course_title: str,
        slug: str,
        prev_lecture: Lecture | None = None,
        next_lecture: Lecture | None = None,
    ) -> str:
        return transcript

    def format_merged(
        self,
        sections: list[Section],
        transcripts: dict[int, str],
        course_title: str,
        total_downloaded: int,
    ) -> str:
        parts = [
            f"Curso: {course_title}",
            f"Total de aulas transcritas: {total_downloaded}",
            "=" * 60,
        ]

        for section in sections:
            section_lectures = [
                lec for lec in section.lectures if lec.id in transcripts
            ]
            if not section_lectures:
                continue

            parts.append(f"\n{'=' * 60}")
            parts.append(f"SEÇÃO: {section.title}")
            parts.append(f"{'=' * 60}\n")

            for lecture in section_lectures:
                parts.append(f"\n--- {lecture.title} ---\n")
                parts.append(transcripts[lecture.id])
                parts.append("")

        return "\n".join(parts)


# ─── Obsidian Markdown ──────────────────────────────────────────────────────


class ObsidianFormatter(BaseFormatter):
    """Formatador Markdown para Obsidian.

    Gera notas com:
    - Frontmatter YAML (tags, metadados do curso)
    - Wikilinks de navegação entre aulas ([[prev]] / [[next]])
    - MOC (Map of Content) com links para todas as notas
    - Índice por seção
    - Callouts do Obsidian para navegação
    """

    def file_extension(self) -> str:
        return ".md"

    def format_lecture(
        self,
        lecture: Lecture,
        section: Section,
        transcript: str,
        course_title: str,
        slug: str,
        prev_lecture: Lecture | None = None,
        next_lecture: Lecture | None = None,
    ) -> str:
        course_tag = _slugify_tag(course_title)
        section_tag = _slugify_tag(section.title)

        lines = [
            "---",
            f'course: "{course_title}"',
            f'section: "{section.title}"',
            f"lecture: {lecture.object_index}",
            f"udemy_id: {lecture.id}",
            f"date: {date.today().isoformat()}",
            "tags:",
            "  - udemy",
            f"  - curso/{course_tag}",
            f"  - secao/{section_tag}",
            "---",
            "",
            f"# {lecture.title}",
            "",
        ]

        nav = _build_nav_callout(lecture, prev_lecture, next_lecture)
        lines.append(nav)
        lines.append("")

        lines.append("## Transcrição")
        lines.append("")

        paragraphs = _split_into_paragraphs(transcript)
        for paragraph in paragraphs:
            lines.append(paragraph)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Anotações")
        lines.append("")
        lines.append("> [!note] Espaço para suas anotações")
        lines.append("> ")
        lines.append("")

        return "\n".join(lines)

    def format_merged(
        self,
        sections: list[Section],
        transcripts: dict[int, str],
        course_title: str,
        total_downloaded: int,
    ) -> str:
        lines = [
            "---",
            f'course: "{course_title}"',
            "tags:",
            "  - udemy",
            f"  - curso/{_slugify_tag(course_title)}",
            "  - resumo",
            "---",
            "",
            f"# {course_title} — Transcrição Completa",
            "",
            f"> [!info] {total_downloaded} aulas transcritas",
            "",
        ]

        for section in sections:
            section_lectures = [
                lec for lec in section.lectures if lec.id in transcripts
            ]
            if not section_lectures:
                continue

            lines.append(f"## {section.title}")
            lines.append("")

            for lecture in section_lectures:
                lines.append(f"### {lecture.title}")
                lines.append("")
                lines.append(transcripts[lecture.id])
                lines.append("")

        return "\n".join(lines)

    def save_extras(
        self,
        course_dir: Path,
        sections: list[Section],
        transcripts: dict[int, str],
        course_title: str,
        slug: str,
    ) -> None:
        """Gera MOC e índices de seção para o Obsidian."""
        self._save_moc(course_dir, sections, transcripts, course_title, slug)
        self._save_section_indexes(course_dir, sections, transcripts, course_title)
        print("   📝 MOC e índices de seção gerados")

    def _save_moc(
        self,
        course_dir: Path,
        sections: list[Section],
        transcripts: dict[int, str],
        course_title: str,
        slug: str,
    ) -> None:
        """Gera o Map of Content (MOC) do curso."""
        lines = [
            "---",
            f'course: "{course_title}"',
            "type: moc",
            f"date: {date.today().isoformat()}",
            "tags:",
            "  - udemy",
            f"  - curso/{_slugify_tag(course_title)}",
            "  - moc",
            "---",
            "",
            f"# 🎓 {course_title}",
            "",
            "> [!info] Map of Content",
            f"> Curso: [{course_title}](https://www.udemy.com/course/{slug}/)",
            "",
        ]

        total = sum(1 for lec_id in transcripts)
        lines.append(f"**{total} aulas transcritas** | {len(sections)} seções")
        lines.append("")

        for section in sections:
            section_lectures = [
                lec for lec in section.lectures if lec.id in transcripts
            ]
            if not section_lectures:
                continue

            section_dir = self.get_section_dirname(section)
            lines.append(f"## {section.title}")
            lines.append("")

            for lecture in section_lectures:
                fname = self.get_lecture_filename(lecture)
                link_target = f"{section_dir}/{fname}".removesuffix(".md")
                lines.append(f"- [[{link_target}|{lecture.title}]]")

            lines.append("")

        moc_path = course_dir / "_MOC.md"
        moc_path.write_text("\n".join(lines), encoding="utf-8")

    def _save_section_indexes(
        self,
        course_dir: Path,
        sections: list[Section],
        transcripts: dict[int, str],
        course_title: str,
    ) -> None:
        """Gera índice para cada seção."""
        for section in sections:
            section_lectures = [
                lec for lec in section.lectures if lec.id in transcripts
            ]
            if not section_lectures:
                continue

            section_dir = course_dir / self.get_section_dirname(section)
            section_dir.mkdir(exist_ok=True)

            lines = [
                "---",
                f'course: "{course_title}"',
                f'section: "{section.title}"',
                "tags:",
                "  - udemy",
                f"  - curso/{_slugify_tag(course_title)}",
                f"  - secao/{_slugify_tag(section.title)}",
                "---",
                "",
                f"# {section.title}",
                "",
                f"> [!abstract] Seção {section.index} — {len(section_lectures)} aulas",
                "",
            ]

            for lecture in section_lectures:
                fname = self.get_lecture_filename(lecture).removesuffix(".md")
                lines.append(f"1. [[{fname}|{lecture.title}]]")

            lines.append("")

            index_path = section_dir / "_index.md"
            index_path.write_text("\n".join(lines), encoding="utf-8")


# ─── Helpers ────────────────────────────────────────────────────────────────


def _slugify_tag(text: str) -> str:
    """Converte texto em tag amigável para Obsidian.

    >>> _slugify_tag("Docker - Zero a Profissional")
    'docker-zero-a-profissional'
    """
    # #3: re já importado no topo — sem import local aqui
    tag = text.lower().strip()
    tag = re.sub(r"[^\w\s-]", "", tag)
    tag = re.sub(r"[\s_]+", "-", tag)
    tag = re.sub(r"-+", "-", tag).strip("-")
    return tag


def _build_nav_callout(
    current: Lecture,
    prev_lec: Lecture | None,
    next_lec: Lecture | None,
) -> str:
    """Constrói callout de navegação com wikilinks."""
    parts = []

    if prev_lec:
        prev_name = f"{prev_lec.object_index:03d} - {sanitize_filename(prev_lec.title)}"
        parts.append(f"⬅ [[{prev_name}|Anterior]]")

    if next_lec:
        next_name = f"{next_lec.object_index:03d} - {sanitize_filename(next_lec.title)}"
        parts.append(f"[[{next_name}|Próxima]] ➡")

    if not parts:
        return ""

    nav_text = " | ".join(parts)
    return f"> [!tip] Navegação\n> {nav_text}"


def _split_into_paragraphs(text: str, sentences_per_paragraph: int = 4) -> list[str]:
    """Quebra texto corrido em parágrafos para melhor leitura no Obsidian.

    Agrupa frases em blocos para evitar paredes de texto.
    Se o texto já tem quebras de linha (timestamped), mantém como está.
    """
    if "\n" in text.strip():
        return [text]

    # #3: re já importado no topo — sem import local aqui
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) <= sentences_per_paragraph:
        return [text]

    paragraphs = []
    for i in range(0, len(sentences), sentences_per_paragraph):
        chunk = sentences[i : i + sentences_per_paragraph]
        paragraphs.append(" ".join(chunk))

    return paragraphs


# ─── Registry ──────────────────────────────────────────────────────────────


FORMATTERS: dict[str, type[BaseFormatter]] = {
    "txt": PlainTextFormatter,
    "obsidian": ObsidianFormatter,
}


def get_formatter(name: str) -> BaseFormatter:
    """Retorna uma instância do formatador pelo nome.

    Args:
        name: "txt" ou "obsidian".

    Raises:
        ValueError: Se o formatador não existe.
    """
    cls = FORMATTERS.get(name)
    if cls is None:
        available = ", ".join(FORMATTERS.keys())
        raise ValueError(f"Formatador '{name}' não encontrado. Disponíveis: {available}")
    return cls()