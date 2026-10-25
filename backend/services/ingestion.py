from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from shared.contracts import ArticleFields, Delivery, Receipt, payload_digest
from models import IngestReceipt, News, NewsRevision, Source, SourceVersion, University
from services.analytics_events import emit_event

def _complete(f): return bool(f.title and f.content and f.category and f.published_on and f.date_precision)
def published_news(db): return db.query(News).filter(News.publication_status == "published")
def persist_article_revision(db, delivery: Delivery, now: datetime):
    source=db.get(Source,delivery.document.source_id)
    version=db.get(SourceVersion,(delivery.document.source_id,delivery.document.source_revision))
    if not source or not version: raise HTTPException(422,"unknown_source_revision")
    existing=db.execute(select(NewsRevision).where(NewsRevision.source_id==delivery.document.source_id,NewsRevision.source_revision==delivery.document.source_revision,NewsRevision.document_hash==delivery.document.document_hash,NewsRevision.prompt_version==delivery.prompt_version)).scalar_one_or_none()
    if existing: return Receipt(delivery_id=delivery.delivery_id,revision_id=existing.id,news_id=existing.news_id,outcome="unchanged")
    fields=delivery.fields; status="pending"; news=None; outcome="pending"
    current=db.query(News).filter(News.university_id==source.university_id,News.canonical_url==delivery.document.canonical_url).first()
    stale=bool(current and current.last_fetched_at and delivery.document.fetched_at < current.last_fetched_at)
    valid=_complete(fields) and delivery.selection is not None and not delivery.issues and source.enabled and source.validated_revision == source.revision and source.auto_publish
    if valid and not stale and not (current and current.editorial_lock):
        uni=db.get(University,source.university_id)
        news=current or News(university_id=source.university_id,source_id=source.id,canonical_url=delivery.document.canonical_url,university=uni.name,created_at=now)
        for key in ("title","content","category","summary","published_at","published_on","date_precision"): setattr(news,key,getattr(fields,key))
        news.source_url=delivery.document.canonical_url; news.content_hash=delivery.document.document_hash; news.last_fetched_at=delivery.document.fetched_at; news.publication_status="published"; news.editorial_lock=False; db.add(news); db.flush(); status="approved"; outcome="published"
    elif stale: outcome="stale"
    revision=NewsRevision(news_id=news.id if news else (current.id if current else None),source_id=source.id,source_revision=delivery.document.source_revision,canonical_url=delivery.document.canonical_url,document_hash=delivery.document.document_hash,prompt_version=delivery.prompt_version,fetched_at=delivery.document.fetched_at,payload_json=delivery.model_dump(mode="json"),issues_json=delivery.issues,review_status=status)
    db.add(revision); db.flush()
    if news: emit_event(db,news,"published",now)
    return Receipt(delivery_id=delivery.delivery_id,revision_id=revision.id,news_id=news.id if news else None,outcome=outcome)
def ingest(db, delivery: Delivery, now: datetime):
    digest=payload_digest(delivery.model_dump(mode="json")); key=str(delivery.delivery_id)
    prior=db.get(IngestReceipt,key)
    if prior:
        if prior.payload_hash != digest: raise HTTPException(409,"delivery_id_content_collision")
        return Receipt.model_validate(prior.receipt_json)
    try:
        receipt=persist_article_revision(db,delivery,now); db.add(IngestReceipt(delivery_id=key,payload_hash=digest,receipt_json=receipt.model_dump(mode="json"),created_at=now)); db.commit(); return receipt
    except Exception:
        db.rollback(); raise
def approve_revision(db, revision_id, fields: ArticleFields, *, editorial_lock, now):
    if not _complete(fields): raise HTTPException(422,"incomplete_article_fields")
    rev=db.get(NewsRevision,revision_id)
    if not rev: raise HTTPException(404,"revision_not_found")
    source=db.get(Source,rev.source_id); uni=db.get(University,source.university_id)
    news=db.get(News,rev.news_id) if rev.news_id else db.query(News).filter(News.university_id==source.university_id,News.canonical_url==rev.canonical_url).first()
    news=news or News(university_id=source.university_id,source_id=source.id,canonical_url=rev.canonical_url,university=uni.name,created_at=now)
    for key in ("title","content","category","summary","published_at","published_on","date_precision"): setattr(news,key,getattr(fields,key))
    news.source_url=rev.canonical_url; news.content_hash=rev.document_hash; news.publication_status="published"; news.editorial_lock=editorial_lock; db.add(news); db.flush(); rev.news_id=news.id; rev.review_status="approved"; rev.reviewed_at=now; emit_event(db,news,"approved",now); db.commit(); db.refresh(news); return news
