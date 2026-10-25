"""Restore missing technical creation timestamps without replacing news rows."""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"


def upgrade():
    bind = op.get_bind()
    if "created_at" not in {column["name"] for column in sa.inspect(bind).get_columns("news")}:
        return
    # Earlier Alembic schemas omitted the server default. An analytics event
    # records when a managed story was published; older legacy rows have no
    # equivalent evidence, so their first known time is this migration.
    bind.execute(sa.text("""
        UPDATE news SET created_at = COALESCE(
            (SELECT MIN(event_at) FROM analytics_outbox WHERE news_id = news.id),
            CURRENT_TIMESTAMP
        ) WHERE created_at IS NULL
    """))


def downgrade():
    # Backfilled timestamps are data, not schema, and must remain available.
    return
