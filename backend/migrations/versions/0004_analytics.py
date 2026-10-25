"""Add the transactional analytics outbox."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"


def upgrade():
    if not sa.inspect(op.get_bind()).has_table("analytics_outbox"):
        op.create_table("analytics_outbox", sa.Column("event_id", sa.String(36), primary_key=True), sa.Column("news_id", sa.Integer, sa.ForeignKey("news.id"), nullable=False), sa.Column("record_version", sa.Integer, nullable=False), sa.Column("event_at", sa.DateTime, nullable=False), sa.Column("operation", sa.String(20), nullable=False), sa.Column("payload_json", sa.JSON, nullable=False), sa.Column("acknowledged_at", sa.DateTime))


def downgrade():
    """Retain immutable events; exports may still need unacknowledged rows."""
    return
