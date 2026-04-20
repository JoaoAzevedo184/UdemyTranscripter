"""Parser de arquivos WebVTT (legendas)."""

import re
from dataclasses import dataclass


@dataclass
class VTTEntry:
    """Entrada individual de uma legenda VTT."""

    start: str
    end: str
    text: str


def parse_vtt(content: str) -> list[VTTEntry]:
    """Faz parse de um arquivo VTT e retorna lista de entradas."""
    entries = []

    for block in re.split(r"\n\n+", content.strip()):
        lines = block.strip().split("\n")
        timestamp_line = None
        text_lines = []

        for line in lines:
            if "-->" in line:
                timestamp_line = line
            elif timestamp_line and line.strip():
                text_lines.append(line.strip())

        if timestamp_line and text_lines:
            parts = timestamp_line.split("-->")
            entries.append(VTTEntry(
                start=parts[0].strip(),
                end=parts[1].strip().split(" ")[0],
                text=" ".join(text_lines),
            ))

    return entries


def _clean_html_tags(text: str) -> str:
    """Remove tags HTML do texto."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _deduplicate(entries: list[VTTEntry]) -> list[tuple[VTTEntry, str]]:
    """Retorna entradas com texto limpo, sem duplicatas."""
    seen: set[str] = set()
    results = []
    for entry in entries:
        clean = _clean_html_tags(entry.text)
        if clean and clean not in seen:
            seen.add(clean)
            results.append((entry, clean))
    return results


def to_plain_text(vtt_content: str) -> str:
    """Converte VTT em texto corrido, removendo duplicatas."""
    pairs = _deduplicate(parse_vtt(vtt_content))
    return " ".join(text for _, text in pairs)


def to_timestamped_text(vtt_content: str) -> str:
    """Converte VTT em texto com timestamps [HH:MM:SS]."""
    pairs = _deduplicate(parse_vtt(vtt_content))
    lines = []
    for entry, text in pairs:
        ts = entry.start.split(".")[0]  # Remove milissegundos
        lines.append(f"[{ts}] {text}")
    return "\n".join(lines)