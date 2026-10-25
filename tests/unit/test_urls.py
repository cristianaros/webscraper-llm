import pytest

from shared.contracts import SourceConfig
from shared.urls import normalize_url, validate_destination


@pytest.fixture
def source():
    return SourceConfig(id=1, university_id=1, university_name="Universidad de Prueba", start_url="https://uni.example/noticias/", allowed_hosts=["uni.example"], revision=1)


def test_tracking_removed_but_article_identity_preserved():
    assert normalize_url("https://UNI.example/noticias/?p=42&utm_source=x#top") == "https://uni.example/noticias/?p=42"


@pytest.mark.parametrize("target,ips", [("http://127.0.0.1/", ["127.0.0.1"]), ("https://uni.example/noticias/a", ["169.254.169.254"]), ("https://other.example/a", ["8.8.8.8"])])
def test_rejects_unassigned_or_private_destination(source, target, ips):
    with pytest.raises(ValueError):
        validate_destination(target, source, ips)


def test_accepts_public_configured_destination(source):
    validate_destination("https://uni.example/noticias/a", source, ["8.8.8.8"])
