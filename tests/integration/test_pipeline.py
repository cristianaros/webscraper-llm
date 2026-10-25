from tests.integration.pipeline_harness import PipelineHarness


def test_downloads_survive_quota_and_publish_after_recovery(tmp_path):
    h = PipelineHarness(tmp_path)
    h.portal_article("/noticias/agua", fixture="article.html")
    h.llm_returns(status=429, retry_after=120)
    h.run()
    assert h.count_local_documents() == 1
    assert h.count_public_news() == 0
    h.advance(seconds=121)
    h.llm_returns_selection(title_id=0, date_id=1, body_ids=[2], category="Investigación")
    h.api_available(False)
    h.run()
    assert h.count_outbox_pending() == 1
    h.restart_collector()
    h.api_available(True)
    h.run()
    assert h.count_public_news() == 1
    assert h.count_outbox_pending() == 0
