"""Closed, user-selected university directory from DatosLab (2026-10-25)."""

from __future__ import annotations

from dataclasses import dataclass

from shared.contracts import SourceInput

DATOSLAB_HOST = "uninews.datoslab.cl"
DETAIL_PATTERN = r"^https://uninews\.datoslab\.cl/detalle/[0-9]+$"


@dataclass(frozen=True)
class UniversityProfile:
    slug: str
    name: str
    official_hosts: tuple[str, ...]
    content_selector: str = "article"
    title_selector: str = "h1"
    date_selector: str = 'meta[property="article:published_time"], time[datetime], time'


DATOSLAB_PROFILES: tuple[UniversityProfile, ...] = (
    UniversityProfile("PUCV", "Pontificia Universidad Católica de Valparaíso", ("www.pucv.cl",), ".CUERPO", "#contenido-ppal", "p.fecha"),
    UniversityProfile("UNAP", "Universidad Arturo Prat", ("www.unap.cl",), ".CUERPO", "h1.titular", "span.date"),
    UniversityProfile("UACH", "Universidad Austral de Chile", ("diario.uach.cl",), ".inner-post-entry", "article h1", "article .post-box-meta-single > span:nth-child(2)"),
    UniversityProfile("UCT", "Universidad Católica de Temuco", ("www.uct.cl",), ".single-article .wysiwyg", ".single-article h2.oscuro"),
    UniversityProfile("UCSC", "Universidad Católica de la Santísima Concepción", ("www.ucsc.cl", "ucsc.cl"), "main"),
    UniversityProfile("UCM", "Universidad Católica del Maule", ("portal.ucm.cl",)),
    UniversityProfile("UCN", "Universidad Católica del Norte", ("www.noticias.ucn.cl",)),
    UniversityProfile("UTFSM", "Universidad Técnica Federico Santa María", ("noticias.usm.cl",)),
    UniversityProfile("UA", "Universidad de Antofagasta", ("www.comunicacionesua.cl",)),
    UniversityProfile("UDA", "Universidad de Atacama", ("uda.cl",)),
    UniversityProfile("UAYSEN", "Universidad de Aysén", ("uaysen.cl",), "article .entry-content", "article h1"),
    UniversityProfile("UDEC", "Universidad de Concepción", ("noticias.udec.cl",), "main"),
    UniversityProfile("ULAGOS", "Universidad de Los Lagos", ("www.ulagos.cl",), ".div-conten-post-text", ".title-post", ".conten-post-date"),
    UniversityProfile("UMAG", "Universidad de Magallanes", ("www.umag.cl",)),
    UniversityProfile("UPLA", "Universidad de Playa Ancha", ("upla.cl", "www.upla.cl"), "article .entry"),
    UniversityProfile("UTALCA", "Universidad de Talca", ("www.utalca.cl",), ".blog-details", ".blog-details h5", ".blog-details .entry-meta span:first-child"),
    UniversityProfile("UTA", "Universidad de Tarapacá", ("www.uta.cl",), "main"),
    UniversityProfile("UV", "Universidad de Valparaíso", ("www.uv.cl",)),
    UniversityProfile("UFRO", "Universidad de la Frontera", ("www.ufro.cl",)),
    UniversityProfile("USERENA", "Universidad de la Serena", ("www.userena.cl", "userena.cl")),
    UniversityProfile("UBIOBIO", "Universidad del Bío-Bío", ("noticias.ubiobio.cl",), ".article"),
)


def build_source_input(profile: UniversityProfile, university_id: int) -> SourceInput:
    """The directory only discovers links; article bytes come from an allowed university host."""
    return SourceInput(
        university_id=university_id,
        start_url=f"https://{DATOSLAB_HOST}/universidad/{profile.slug}",
        allowed_hosts=[DATOSLAB_HOST, *profile.official_hosts],
        allowed_image_hosts=list(profile.official_hosts),
        article_url_pattern=DETAIL_PATTERN,
        link_selector='div.album.py-5 p.card-text a[href*="/detalle/"]',
        content_selector=profile.content_selector,
        title_selector=profile.title_selector,
        date_selector=profile.date_selector,
        max_pages=1,
        max_articles=3,
        enabled=False,
        auto_publish=False,
    )
