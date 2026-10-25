from datetime import date, datetime, timezone
import hashlib
from uuid import uuid4

from fastapi.testclient import TestClient
from backend.config import BackendSettings
from backend.main import create_app
from backend.scripts.bootstrap_db import bootstrap_database
from models import AnalyticsOutbox, News, NewsMediaHistory, Source
from shared.contracts import ArticleFields, Delivery, Document, ImageAsset, ImageDelivery, Selection, TextBlock

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
       b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb6\x00\x00\x00\x00IEND\xaeB`\x82")

def _prepared_client(tmp_path):
    url = "sqlite:///" + (tmp_path / "api.db").as_posix(); bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, media_root=tmp_path / "media")); client = TestClient(app)
    admin = {"Authorization":"Bearer admin-test"}; worker = {"Authorization":"Bearer worker-test"}
    assert client.post("/api/admin/universities",json={"name":"U"},headers=admin).status_code == 201
    assert client.post("/api/admin/sources",json={"university_id":1,"start_url":"https://u.test/a","allowed_hosts":["u.test"]},headers=admin).status_code == 200
    db = app.state.session_factory(); source = db.get(Source, 1); source.enabled = source.auto_publish = True; source.validated_revision = 1; db.commit(); db.close()
    now = datetime.now(timezone.utc)
    article = Delivery(delivery_id=uuid4(),run_id=uuid4(),document=Document(source_id=1,source_revision=1,canonical_url="https://u.test/a",fetched_at=now,document_hash="a"*64,html_sha256="b"*64,blocks=[TextBlock(id=0,kind="title",text="T"),TextBlock(id=1,kind="date",text="D"),TextBlock(id=2,kind="body",text="Body")],expected_body_ids=[2]),selection=Selection(title_id=0,date_id=1,body_ids=[2],category="General"),fields=ArticleFields(title="T",content="Body",category="General",published_at=now,published_on=date.today(),date_precision="day"),issues=[],model="minimax/minimax-m3:free")
    receipt = client.post("/api/collector/articles",json=article.model_dump(mode="json"),headers=worker).json()
    image = ImageAsset(status="ready",original_url="https://u.test/image.png",sha256=hashlib.sha256(PNG).hexdigest(),content_type="image/png",width=1,height=1,byte_size=len(PNG))
    return client, app, worker, ImageDelivery(delivery_id=article.delivery_id,revision_id=receipt["revision_id"],expected_document_hash=article.document.document_hash,image=image)

def test_collector_media_upload_is_authenticated_and_idempotent(tmp_path):
    client, app, worker, delivery = _prepared_client(tmp_path)
    data = {"delivery":delivery.model_dump_json()}; files = {"file":("original.png",PNG,"image/png")}
    assert client.post("/api/collector/media",data=data,files=files).status_code == 401
    first = client.post("/api/collector/media",data=data,files=files,headers=worker)
    assert first.status_code == 200 and first.json()["applied_to_current"] is True
    repeated = client.post("/api/collector/media",data=data,files=files,headers=worker)
    assert repeated.status_code == 200 and repeated.json() == first.json()
    db = app.state.session_factory(); assert db.query(NewsMediaHistory).count() == 1; assert db.query(News).one().image_sha256 == delivery.image.sha256
    events = db.query(AnalyticsOutbox).all(); assert len(events) == 2 and events[-1].operation == "image_updated" and events[-1].payload_json["image_sha256"] == delivery.image.sha256; db.close()
    served = client.get(f"/api/media/{delivery.image.sha256}")
    assert served.status_code == 200 and served.headers["x-content-type-options"] == "nosniff"
