from tests.integration.analytics_harness import AnalyticsHarness
from tests.integration.pipeline_harness import PipelineHarness


def test_local_collection_and_prepare_need_no_gcp(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    h = PipelineHarness(tmp_path)
    h.run()
    ah = AnalyticsHarness(h.app.state.session_factory(), tmp_path)
    ah.publish_news(title="Prueba local")
    manifest = ah.prepare()
    assert manifest.record_count >= 1
