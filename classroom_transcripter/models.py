"""Modelos de dados do domínio."""

from dataclasses import dataclass, field


@dataclass
class Caption:
    """Legenda/transcrição de uma aula."""

    locale: str
    url: str
    label: str


@dataclass
class Lecture:
    """Aula individual dentro de uma seção."""

    id: int
    title: str
    object_index: int
    captions: list[Caption] = field(default_factory=list)


@dataclass
class Section:
    """Seção (capítulo) de um curso."""

    title: str
    index: int
    lectures: list[Lecture] = field(default_factory=list)


@dataclass
class DownloadResult:
    """Resultado de um download de transcrições."""

    course_title: str
    course_id: int
    slug: str
    total_sections: int
    total_lectures: int
    downloaded: int
    errors: int
    output_dir: str