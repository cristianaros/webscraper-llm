from datetime import UTC, datetime
from tests.integration.pipeline_harness import PipelineHarness


def test_acceptance_end_to_end_collection(tmp_path):
    h = PipelineHarness(tmp_path)
    h.portal_article("/noticias/agua", html=(
        "<article>"
        "<h1>Agua y Sustentabilidad</h1>"
        '<time datetime="2026-09-06">2026-09-06</time>'
        "<p>Contenido completo y verificable sobre el uso del agua en la región universitaria.</p>"
        "</article>"
    ))
    h.llm_returns_selection(title_id=0, date_id=1, body_ids=[2], category="Investigación")
    h.run()
    assert h.count_local_documents() == 1
    assert h.count_public_news() == 1
    assert h.count_outbox_pending() == 0
