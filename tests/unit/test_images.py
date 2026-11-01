import io, pytest
import httpx
from PIL import Image
from collector.images import find_image_candidates, inspect_image, ImageFetcher
from collector.http import HttpFetcher, FetchError
from scripts.datoslab_catalog import DATOSLAB_PROFILES, build_source_input
from shared.contracts import SourceConfig

def test_detects_actual_format_and_dimensions():
    data=io.BytesIO(); Image.new('RGB',(640,360),'white').save(data,format='PNG')
    info=inspect_image(data.getvalue()); assert (info.width,info.height,info.content_type)==(640,360,'image/png')
def test_html_disguised_as_image_is_rejected():
    with pytest.raises(ValueError): inspect_image(b'<html><script>bad()</script></html>')


def test_empty_jsonld_image_list_does_not_abort_other_image_candidates():
    profile = next(item for item in DATOSLAB_PROFILES if item.slug == "PUCV")
    source = SourceConfig.model_validate({
        **build_source_input(profile, university_id=1).model_dump(),
        "id": 1, "university_name": profile.name, "revision": 1,
    })
    html = (
        '<meta property="og:image" content="https://www.pucv.cl/imagen.jpg">'
        '<script type="application/ld+json">{"@type":"NewsArticle","image":[]}</script>'
    )
    candidates = find_image_candidates(html, source, "https://www.pucv.cl/noticia")
    assert [item.url for item in candidates] == ["https://www.pucv.cl/imagen.jpg"]


def test_lazy_loaded_institutional_image_and_redirect_final_url(monkeypatch):
    profile = next(item for item in DATOSLAB_PROFILES if item.slug == "UACH")
    source = SourceConfig.model_validate({
        **build_source_input(profile, university_id=1).model_dump(),
        "id": 1, "university_name": profile.name, "revision": 1,
    }).model_copy(update={"allowed_hosts": ["uninews.datoslab.cl", "diario.uach.cl"], "allowed_image_hosts": ["diario.uach.cl"]})
    html = '<article><img src="data:image/gif;base64,x" data-src="https://www.uach.cl/img.jpg"></article>'
    candidates = find_image_candidates(html, source, "https://diario.uach.cl/noticia")
    assert [candidate.url for candidate in candidates] == ["https://www.uach.cl/img.jpg"]
    image = io.BytesIO(); Image.new("RGB", (640, 360), "white").save(image, format="JPEG")
    def handler(request):
        if request.url.path == "/robots.txt": return httpx.Response(404)
        if request.url.host == "www.uach.cl": return httpx.Response(302, headers={"Location": "https://i0.wp.com/final.uach.cl/foto.jpg"})
        if request.url.host == "i0.wp.com": return httpx.Response(200, content=image.getvalue(), headers={"Content-Type":"image/jpeg"})
        return httpx.Response(404)
    monkeypatch.setattr("collector.http.socket.getaddrinfo", lambda *a, **k: [(None,None,None,None,("8.8.8.8",0))])
    fetcher = HttpFetcher(httpx.Client(transport=httpx.MockTransport(handler)), allow_test_hosts=True)
    asset, _ = ImageFetcher(fetcher).fetch(candidates[0], source)
    assert asset.original_url == "https://i0.wp.com/final.uach.cl/foto.jpg"


def test_image_redirect_to_metadata_ip_is_blocked_before_request(monkeypatch):
    profile = next(item for item in DATOSLAB_PROFILES if item.slug == "UACH")
    source = SourceConfig.model_validate({**build_source_input(profile, university_id=1).model_dump(), "id":1,"university_name":profile.name,"revision":1}).model_copy(update={"allowed_image_hosts":["img.uach.cl"]})
    seen = []
    def handler(request):
        seen.append(str(request.url))
        if request.url.path == "/robots.txt": return httpx.Response(404)
        return httpx.Response(302, headers={"Location":"http://169.254.169.254/latest/meta-data"})
    client=httpx.Client(transport=httpx.MockTransport(handler))
    fetcher=HttpFetcher(client,allow_test_hosts=True)
    monkeypatch.setattr("collector.http.socket.getaddrinfo", lambda *a, **k: [(None,None,None,None,("8.8.8.8",0))])
    candidate=type("Candidate",(),{"url":"https://img.uach.cl/p.jpg","alt":None,"credit":None})()
    with pytest.raises(FetchError, match="private_destination|literal_ip_not_allowed|destination_host_not_allowed"):
        ImageFetcher(fetcher).fetch(candidate,source)
    assert not any("169.254.169.254" in url for url in seen)
