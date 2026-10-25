import pytest
from backend.services.gcs_media import GcsMediaStore


def test_invalid_sha_rejected():
    store = GcsMediaStore("test-bucket")
    with pytest.raises(ValueError):
        store.put("short-sha", b"fake-bytes", "image/png")
