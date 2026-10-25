"""Add the recoverable collection and delivery records."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"


def _create(name, *columns, **kwargs):
    if not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *columns, **kwargs)


def upgrade():
    _create("universities", sa.Column("id", sa.Integer, primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("normalized_name", sa.String(200), nullable=False, unique=True))
    _create("sources", sa.Column("id", sa.Integer, primary_key=True), sa.Column("university_id", sa.Integer, sa.ForeignKey("universities.id"), nullable=False), sa.Column("start_url", sa.Text, nullable=False), sa.Column("revision", sa.Integer, nullable=False, server_default="1"), sa.Column("config_json", sa.JSON, nullable=False), sa.Column("validated_revision", sa.Integer), sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()), sa.Column("auto_publish", sa.Boolean, nullable=False, server_default=sa.false()), sa.Column("updated_at", sa.DateTime), sa.UniqueConstraint("university_id", "start_url", name="uq_source_origin"))
    _create("source_versions", sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id"), primary_key=True), sa.Column("revision", sa.Integer, primary_key=True), sa.Column("snapshot_json", sa.JSON, nullable=False), sa.Column("created_at", sa.DateTime))
    _create("news_revisions", sa.Column("id", sa.Integer, primary_key=True), sa.Column("news_id", sa.Integer, sa.ForeignKey("news.id")), sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id"), nullable=False), sa.Column("source_revision", sa.Integer, nullable=False), sa.Column("canonical_url", sa.Text, nullable=False), sa.Column("document_hash", sa.String(64), nullable=False), sa.Column("prompt_version", sa.String(40), nullable=False), sa.Column("fetched_at", sa.DateTime, nullable=False), sa.Column("payload_json", sa.JSON, nullable=False), sa.Column("issues_json", sa.JSON, nullable=False), sa.Column("review_status", sa.String(12), nullable=False, server_default="pending"), sa.Column("created_at", sa.DateTime), sa.Column("reviewed_at", sa.DateTime), sa.UniqueConstraint("source_id", "source_revision", "document_hash", "prompt_version", name="uq_revision_identity"))
    _create("ingest_receipts", sa.Column("delivery_id", sa.String(36), primary_key=True), sa.Column("payload_hash", sa.String(64), nullable=False), sa.Column("receipt_json", sa.JSON, nullable=False), sa.Column("kind", sa.String(10), nullable=False, server_default="article"), sa.Column("created_at", sa.DateTime, nullable=False))
    _create("scrape_runs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id"), nullable=False), sa.Column("source_revision", sa.Integer, nullable=False), sa.Column("trigger", sa.String(12), nullable=False), sa.Column("status", sa.String(12), nullable=False), sa.Column("requested_at", sa.DateTime, nullable=False), sa.Column("started_at", sa.DateTime), sa.Column("finished_at", sa.DateTime), sa.Column("lease_until", sa.DateTime), sa.Column("lease_token", sa.String(36)), sa.Column("report_json", sa.JSON), sa.Column("preview_json", sa.JSON), sa.Column("error_code", sa.String(80)))
    _create("collector_status", sa.Column("collector_id", sa.String(80), primary_key=True), sa.Column("last_seen_at", sa.DateTime, nullable=False), sa.Column("status_json", sa.JSON, nullable=False))


def downgrade():
    """Collection data is retained; a downgrade must never discard deliveries."""
    return
