"""Add original-image storage and additive image evidence to news."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("news")}
    additions = (
        ("published_at", sa.DateTime()), ("university_id", sa.Integer()),
        ("source_id", sa.Integer()), ("canonical_url", sa.Text()),
        ("content_hash", sa.String(64)), ("published_on", sa.Date()),
        ("date_precision", sa.String(10)), ("publication_status", sa.String(12)),
        ("editorial_lock", sa.Boolean()), ("last_fetched_at", sa.DateTime()),
        ("image_status", sa.String(12)), ("image_sha256", sa.String(64)),
        ("image_original_url", sa.Text()), ("image_alt", sa.Text()),
        ("image_credit", sa.Text()),
    )
    with op.batch_alter_table("news") as batch:
        for name, type_ in additions:
            if name not in columns:
                batch.add_column(sa.Column(name, type_))
    if not sa.inspect(bind).has_table("media_assets"):
        op.create_table("media_assets", sa.Column("sha256", sa.String(64), primary_key=True), sa.Column("storage_key", sa.Text, nullable=False), sa.Column("storage_backend", sa.String(20), nullable=False), sa.Column("content_type", sa.String(40), nullable=False), sa.Column("width", sa.Integer, nullable=False), sa.Column("height", sa.Integer, nullable=False), sa.Column("byte_size", sa.Integer, nullable=False), sa.Column("created_at", sa.DateTime))
    if not sa.inspect(bind).has_table("news_media_history"):
        op.create_table("news_media_history", sa.Column("id", sa.Integer, primary_key=True), sa.Column("revision_id", sa.Integer, sa.ForeignKey("news_revisions.id"), nullable=False), sa.Column("news_id", sa.Integer, sa.ForeignKey("news.id")), sa.Column("image_json", sa.JSON, nullable=False), sa.Column("created_at", sa.DateTime))


def downgrade():
    """Keep additive image columns and files referenced by existing records."""
    return
