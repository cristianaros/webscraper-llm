from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Index
from sqlalchemy.sql import func
from database import Base, UTCDateTime

class University(Base):
    __tablename__ = "universities"; id = Column(Integer, primary_key=True); name = Column(String(200), nullable=False); normalized_name = Column(String(200), nullable=False, unique=True)
class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True); university_id = Column(Integer, ForeignKey("universities.id"), nullable=False); start_url = Column(Text, nullable=False); revision = Column(Integer, nullable=False, default=1); config_json = Column(JSON, nullable=False, default=dict); validated_revision = Column(Integer); enabled = Column(Boolean, nullable=False, default=False); auto_publish = Column(Boolean, nullable=False, default=False); updated_at = Column(UTCDateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("university_id", "start_url", name="uq_source_origin"),)
class SourceVersion(Base):
    __tablename__ = "source_versions"; source_id = Column(Integer, ForeignKey("sources.id"), primary_key=True); revision = Column(Integer, primary_key=True); snapshot_json = Column(JSON, nullable=False); created_at = Column(UTCDateTime(timezone=True), server_default=func.now())
class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True); title = Column(String(255), nullable=False); summary = Column(String(500)); content = Column(Text, nullable=False); category = Column(String(100), nullable=False, default="General"); university = Column(String(200), nullable=False, default="Universidad Demo"); author = Column(String(150)); image_url = Column(String(500)); source_url = Column(String(500)); is_featured = Column(Boolean, default=False); published_at = Column(UTCDateTime(timezone=True), index=True); created_at = Column(UTCDateTime(timezone=True), server_default=func.now()); updated_at = Column(UTCDateTime(timezone=True), onupdate=func.now())
    university_id = Column(Integer, ForeignKey("universities.id")); source_id = Column(Integer, ForeignKey("sources.id")); canonical_url = Column(Text); content_hash = Column(String(64)); published_on = Column(Date); date_precision = Column(String(10)); publication_status = Column(String(12), nullable=False, default="published"); editorial_lock = Column(Boolean, nullable=False, default=True); last_fetched_at = Column(UTCDateTime(timezone=True)); image_status = Column(String(12), nullable=False, default="not_found"); image_sha256 = Column(String(64)); image_original_url = Column(Text); image_alt = Column(Text); image_credit = Column(Text)
    __table_args__ = (UniqueConstraint("university_id", "canonical_url", name="uq_news_origin"), Index("ix_news_publication", "publication_status", "published_at", "id"))
class NewsRevision(Base):
    __tablename__ = "news_revisions"
    id = Column(Integer, primary_key=True); news_id = Column(Integer, ForeignKey("news.id")); source_id = Column(Integer, ForeignKey("sources.id"), nullable=False); source_revision = Column(Integer, nullable=False); canonical_url = Column(Text, nullable=False); document_hash = Column(String(64), nullable=False); prompt_version = Column(String(40), nullable=False); fetched_at = Column(UTCDateTime(timezone=True), nullable=False); payload_json = Column(JSON, nullable=False); issues_json = Column(JSON, nullable=False, default=list); review_status = Column(String(12), nullable=False, default="pending"); created_at = Column(UTCDateTime(timezone=True), server_default=func.now()); reviewed_at = Column(UTCDateTime(timezone=True))
    __table_args__ = (UniqueConstraint("source_id", "source_revision", "document_hash", "prompt_version", name="uq_revision_identity"),)
class IngestReceipt(Base):
    __tablename__ = "ingest_receipts"; delivery_id = Column(String(36), primary_key=True); payload_hash = Column(String(64), nullable=False); receipt_json = Column(JSON, nullable=False); kind = Column(String(10), nullable=False, default="article"); created_at = Column(UTCDateTime(timezone=True), nullable=False)
class ScrapeRun(Base):
    __tablename__ = "scrape_runs"; id = Column(String(36), primary_key=True); source_id = Column(Integer, ForeignKey("sources.id"), nullable=False); source_revision = Column(Integer, nullable=False); trigger = Column(String(12), nullable=False); status = Column(String(12), nullable=False); requested_at = Column(UTCDateTime(timezone=True), nullable=False); started_at = Column(UTCDateTime(timezone=True)); finished_at = Column(UTCDateTime(timezone=True)); lease_until = Column(UTCDateTime(timezone=True)); lease_token = Column(String(36)); report_json = Column(JSON, default=dict); preview_json = Column(JSON); error_code = Column(String(80))
class CollectorStatus(Base):
    __tablename__ = "collector_status"; collector_id = Column(String(80), primary_key=True); last_seen_at = Column(UTCDateTime(timezone=True), nullable=False); status_json = Column(JSON, nullable=False)
class MediaAsset(Base):
    __tablename__ = "media_assets"; sha256 = Column(String(64), primary_key=True); storage_key = Column(Text, nullable=False); storage_backend = Column(String(20), nullable=False); content_type = Column(String(40), nullable=False); width = Column(Integer, nullable=False); height = Column(Integer, nullable=False); byte_size = Column(Integer, nullable=False); created_at = Column(UTCDateTime(timezone=True), server_default=func.now())
class NewsMediaHistory(Base):
    __tablename__ = "news_media_history"; id = Column(Integer, primary_key=True); revision_id = Column(Integer, ForeignKey("news_revisions.id"), nullable=False); news_id = Column(Integer, ForeignKey("news.id")); image_json = Column(JSON, nullable=False); created_at = Column(UTCDateTime(timezone=True), server_default=func.now())
class AnalyticsOutbox(Base):
    __tablename__ = "analytics_outbox"; event_id = Column(String(36), primary_key=True); news_id = Column(Integer, ForeignKey("news.id"), nullable=False); record_version = Column(Integer, nullable=False); event_at = Column(UTCDateTime(timezone=True), nullable=False); operation = Column(String(20), nullable=False); payload_json = Column(JSON, nullable=False); acknowledged_at = Column(UTCDateTime(timezone=True))
