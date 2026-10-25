import io, pytest
from PIL import Image
from collector.images import find_image_candidates, inspect_image
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
