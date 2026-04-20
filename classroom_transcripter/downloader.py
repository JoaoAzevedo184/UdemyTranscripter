"""Lógica principal de download e salvamento de transcrições."""

import json
import time
from pathlib import Path

# #5: Separação explícita entre os dois clientes HTTP usados no módulo.
#
# Este módulo usa DOIS clientes HTTP intencionalmente:
#
#   • curl_cffi (via UdemyClient) — para chamadas à API da Udemy.
#     Necessário para imitar o TLS fingerprint do Chrome e passar pelo
#     Cloudflare. Usado em client.py; não importado diretamente aqui.
#
#   • requests (padrão) — para baixar os arquivos VTT de legenda.
#     Os VTTs são servidos por CDNs externos (ex: udemy-captions.s3.amazonaws.com)
#     sem proteção Cloudflare, então requests simples é suficiente e mais leve.
#
# Alterar _fetch_and_convert para usar curl_cffi seria desnecessário e
# adicionaria complexidade sem benefício real.
import requests

from .client import UdemyClient
from .config import DOWNLOAD_DELAY
from .exceptions import NoCaptionsError
from .formatters import BaseFormatter, PlainTextFormatter
from .models import DownloadResult, Lecture, Section
from .utils import pick_caption, sanitize_filename
from .vtt import to_plain_text, to_timestamped_text


def list_available_captions(client: UdemyClient, slug: str) -> dict[str, dict]:
    """Lista os idiomas de legenda disponíveis no curso.

    Returns:
        Dict mapeando locale -> {"label": str, "count": int}
    """
    course_id, title = client.get_course_info(slug)
    print(f"\n🎓 {title}")

    sections = client.get_curriculum(course_id)
    langs: dict[str, dict] = {}

    for section in sections:
        for lecture in section.lectures:
            for cap in lecture.captions:
                if cap.locale not in langs:
                    langs[cap.locale] = {"label": cap.label, "count": 0}
                langs[cap.locale]["count"] += 1

    if not langs:
        print("  Nenhuma legenda disponível.")
        return langs

    print("  Idiomas disponíveis:")
    for locale, info in sorted(langs.items(), key=lambda x: -x[1]["count"]):
        print(f"    • {info['label']} ({locale}) — {info['count']} aulas")

    return langs


def download_transcripts(
    client: UdemyClient,
    slug: str,
    output_dir: str = "./udemy_transcripts",
    lang: str | None = None,
    with_timestamps: bool = False,
    merge: bool = False,
    formatter: BaseFormatter | None = None,
    resume: bool = False,
) -> DownloadResult:
    """Baixa todas as transcrições de um curso.

    Args:
        client: Cliente autenticado da Udemy (usa curl_cffi internamente).
        slug: Slug do curso.
        output_dir: Diretório raiz de saída.
        lang: Idioma preferido (ex: "pt", "en").
        with_timestamps: Se True, inclui timestamps [HH:MM:SS].
        merge: Se True, gera arquivo mesclado.
        formatter: Formatador de saída (padrão: PlainTextFormatter).
        resume: Se True, pula aulas cujo arquivo já existe em disco.
                Permite retomar downloads interrompidos.

    Returns:
        DownloadResult com estatísticas do download.

    Raises:
        NoCaptionsError: Se nenhuma legenda estiver disponível.
    """
    if formatter is None:
        formatter = PlainTextFormatter()

    print(f"\n🎓 Buscando informações do curso: {slug}")
    course_id, course_title = client.get_course_info(slug)
    print(f"   Título: {course_title}")
    print(f"   ID: {course_id}")

    print("\n📚 Carregando grade curricular...")
    sections = client.get_curriculum(course_id)
    total_lectures = sum(len(s.lectures) for s in sections)
    lectures_with_caps = sum(
        1 for s in sections for lec in s.lectures if lec.captions
    )
    print(f"   {len(sections)} seções, {total_lectures} aulas")
    print(f"   {lectures_with_caps} aulas com transcrição disponível")

    if lectures_with_caps == 0:
        raise NoCaptionsError()

    if resume:
        print("   ▶ Modo --resume: aulas já baixadas serão puladas")

    course_dir = Path(output_dir) / sanitize_filename(course_title)
    course_dir.mkdir(parents=True, exist_ok=True)

    downloaded, skipped, errors, transcripts = _download_sections(
        sections=sections,
        course_dir=course_dir,
        lang=lang,
        with_timestamps=with_timestamps,
        formatter=formatter,
        course_title=course_title,
        slug=slug,
        resume=resume,
    )

    if merge and transcripts:
        merged_content = formatter.format_merged(
            sections=sections,
            transcripts=transcripts,
            course_title=course_title,
            total_downloaded=downloaded,
        )
        merged_path = course_dir / formatter.get_merged_filename()
        merged_path.write_text(merged_content, encoding="utf-8")
        print(f"\n📄 Arquivo completo: {merged_path}")

    formatter.save_extras(
        course_dir=course_dir,
        sections=sections,
        transcripts=transcripts,
        course_title=course_title,
        slug=slug,
    )

    _save_metadata(
        course_dir, course_id, course_title, slug,
        len(sections), total_lectures, downloaded, lang,
    )

    print("\n✓ Concluído!")
    print(f"  Transcrições baixadas: {downloaded}")
    if skipped:
        print(f"  Já existiam (puladas): {skipped}")
    if errors:
        print(f"  Erros: {errors}")
    print(f"  Diretório: {course_dir}")

    return DownloadResult(
        course_title=course_title,
        course_id=course_id,
        slug=slug,
        total_sections=len(sections),
        total_lectures=total_lectures,
        downloaded=downloaded,
        errors=errors,
        output_dir=str(course_dir),
    )


# ─── Funções internas ──────────────────────────────────────────────────────


def _build_lecture_navigation(
    sections: list[Section],
) -> dict[int, tuple[Lecture | None, Lecture | None]]:
    """Constrói mapa de navegação (prev, next) para cada lecture.

    Returns:
        Dict de lecture.id -> (prev_lecture, next_lecture)
    """
    all_lectures: list[Lecture] = []
    for section in sections:
        for lecture in section.lectures:
            if lecture.captions:
                all_lectures.append(lecture)

    nav: dict[int, tuple[Lecture | None, Lecture | None]] = {}
    for i, lecture in enumerate(all_lectures):
        prev_lec = all_lectures[i - 1] if i > 0 else None
        next_lec = all_lectures[i + 1] if i < len(all_lectures) - 1 else None
        nav[lecture.id] = (prev_lec, next_lec)

    return nav


def _download_sections(
    sections: list[Section],
    course_dir: Path,
    lang: str | None,
    with_timestamps: bool,
    formatter: BaseFormatter,
    course_title: str,
    slug: str,
    resume: bool = False,
) -> tuple[int, int, int, dict[int, str]]:
    """Itera sobre seções/aulas e baixa as legendas.

    Returns:
        Tupla (downloaded, skipped, errors, transcripts).
        transcripts mapeia lecture.id -> texto da transcrição.
    """
    downloaded = 0
    skipped = 0
    errors = 0
    transcripts: dict[int, str] = {}

    nav = _build_lecture_navigation(sections)

    for section in sections:
        section_dir = course_dir / formatter.get_section_dirname(section)
        section_dir.mkdir(exist_ok=True)

        for lecture in section.lectures:
            caption = pick_caption(lecture.captions, lang)
            if not caption:
                continue

            filename = formatter.get_lecture_filename(lecture)
            file_path = section_dir / filename
            display_name = filename.removesuffix(formatter.file_extension())

            # #7: modo --resume — pula se o arquivo já existe
            if resume and file_path.exists():
                print(f"   ↷ {display_name} (já existe, pulando)")
                # Carrega conteúdo existente para poder gerar o merge
                try:
                    transcripts[lecture.id] = file_path.read_text(encoding="utf-8")
                except Exception:
                    pass
                skipped += 1
                continue

            print(f"   ⬇ {display_name} [{caption.label}]")

            try:
                raw_text = _fetch_and_convert(caption.url, with_timestamps)
                transcripts[lecture.id] = raw_text

                prev_lec, next_lec = nav.get(lecture.id, (None, None))
                content = formatter.format_lecture(
                    lecture=lecture,
                    section=section,
                    transcript=raw_text,
                    course_title=course_title,
                    slug=slug,
                    prev_lecture=prev_lec,
                    next_lecture=next_lec,
                )

                file_path.write_text(content, encoding="utf-8")

                downloaded += 1
                time.sleep(DOWNLOAD_DELAY)

            except Exception as e:
                print(f"   ✗ Erro: {e}")
                errors += 1

    return downloaded, skipped, errors, transcripts


def _fetch_and_convert(url: str, with_timestamps: bool) -> str:
    """Baixa um arquivo VTT de CDN externo e converte para texto.

    Usa requests (não curl_cffi) pois os VTTs são servidos por CDNs sem
    proteção Cloudflare. Ver comentário no topo do módulo para detalhes.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    vtt_content = resp.text

    if with_timestamps:
        return to_timestamped_text(vtt_content)
    return to_plain_text(vtt_content)


def _save_metadata(
    course_dir: Path,
    course_id: int,
    course_title: str,
    slug: str,
    total_sections: int,
    total_lectures: int,
    downloaded: int,
    lang: str | None,
) -> None:
    """Salva metadados do curso em JSON."""
    meta = {
        "course_id": course_id,
        "title": course_title,
        "slug": slug,
        "sections": total_sections,
        "total_lectures": total_lectures,
        "transcribed": downloaded,
        "language": lang or "auto",
    }
    meta_path = course_dir / "_metadata.json"
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )