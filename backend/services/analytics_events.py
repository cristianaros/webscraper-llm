from datetime import datetime
from uuid import uuid4
from models import AnalyticsOutbox
def emit_event(db, news, operation: str, now: datetime):
    version = (news.updated_at or now).isoformat()
    db.add(AnalyticsOutbox(event_id=str(uuid4()), news_id=news.id, record_version=hash(version) & 0x7fffffff, event_at=now, operation=operation, payload_json={"news_id":news.id,"publication_status":news.publication_status,"title":news.title,"content":news.content,"category":news.category,"university":news.university,"published_on":news.published_on.isoformat() if news.published_on else None,"image_sha256":news.image_sha256}))
