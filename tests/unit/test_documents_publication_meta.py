from datetime import UTC, datetime

from collector.documents import build_document
from collector.http import FetchResult
from shared.contracts import Selection
from shared.validation import materialize


def test_publication_meta_is_preserved_as_date_evidence(source):
    html = (
        '<html><head><meta property="article:published_time" '
        'content="2026-10-14T13:13:39-03:00"></head><body>'
        '<article><h1>Una noticia universitaria comprobable</h1>'
        '<p>La universidad publicó un informe detallado sobre sus actividades. '
        'El documento describe hechos y resultados verificables en su comunidad.</p>'
        '</article></body></html>'
    )
    configured = source.model_copy(update={
        "content_selector": "article",
        "date_selector": 'meta[property="article:published_time"]',
    })
    result = FetchResult(
        url="https://uni.example/noticias/informe", html=html, status=200,
        etag=None, last_modified=None, fetched_at=datetime(2026, 10, 25, tzinfo=UTC),
        content=html.encode(), content_type="text/html",
    )

    document = build_document(result, configured)
    date = next(block for block in document.blocks if block.kind == "date")
    title = next(block for block in document.blocks if block.kind == "title")
    fields = materialize(
        document,
        Selection(
            title_id=title.id, date_id=date.id,
            body_ids=document.expected_body_ids, category="Institucional",
        ),
        configured.timezone,
    )

    assert date.text == "2026-10-14T13:13:39-03:00"
    assert fields.published_on.isoformat() == "2026-10-14"
    assert fields.original_date_text == date.text
    assert "La universidad publicó" in fields.content
