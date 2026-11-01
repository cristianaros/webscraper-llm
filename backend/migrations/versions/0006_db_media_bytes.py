"""Persist media bytes in the operational database."""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("media_assets")}
    if "content_bytes" not in columns:
        with op.batch_alter_table("media_assets") as batch_op:
            batch_op.add_column(sa.Column("content_bytes", sa.LargeBinary(), nullable=True))


def downgrade():
    # Existing image bytes are retained as operational data.
    return
