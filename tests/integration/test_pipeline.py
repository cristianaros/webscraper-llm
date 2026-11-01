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
    status = h.api_client.get("/api/admin/collector/status", headers={"Authorization": "Bearer admin-test"})
    assert status.json()["stale"] is False


def test_run_once_uses_pinned_backend_for_default_transport(tmp_path, monkeypatch):
    import collector.pipeline as pipeline
    from collector.http import PublicOnlyNetworkBackend

    h = PipelineHarness(tmp_path)
    captured = []
    original = pipeline.HttpFetcher
    def inspect(client=None, **kwargs):
        result = original(client, **kwargs)
        captured.append(result.client)
        return result
    monkeypatch.setattr(pipeline, "HttpFetcher", inspect)
    pipeline.run_once(
        h.collector_settings.model_copy(update={"allow_test_hosts": False}),
        clock=lambda: h.current_time,
        monotonic=lambda: h.monotonic_time,
        http_transport=None,
    )
    assert captured
    assert isinstance(captured[0]._transport._pool._network_backend, PublicOnlyNetworkBackend)


def test_run_once_closes_owned_fetcher_client(tmp_path, monkeypatch):
    import collector.pipeline as pipeline

    h = PipelineHarness(tmp_path)
    captured = []
    original = pipeline.HttpFetcher
    def inspect(client=None, **kwargs):
        result = original(client, **kwargs)
        captured.append(result.client)
        return result
    monkeypatch.setattr(pipeline, "HttpFetcher", inspect)
    pipeline.run_once(
        h.collector_settings.model_copy(update={"allow_test_hosts": False}),
        clock=lambda: h.current_time,
        monotonic=lambda: h.monotonic_time,
        http_transport=None,
    )
    assert captured and captured[0].is_closed
