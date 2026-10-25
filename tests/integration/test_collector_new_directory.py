from collector.pipeline import run_once
from tests.integration.pipeline_harness import PipelineHarness


def test_first_run_creates_its_isolated_data_directory(tmp_path):
    harness = PipelineHarness(tmp_path)
    harness.data_dir.rmdir()

    result = run_once(
        harness.collector_settings,
        clock=lambda: harness.current_time,
        monotonic=lambda: harness.monotonic_time,
        http_transport=harness.transport,
    )

    assert result.exit_code == 0
    assert (harness.data_dir / "collector.db").is_file()
