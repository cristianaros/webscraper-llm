"""Create the original news table without replacing an adopted installation."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    """Bootstrap an empty database, leaving an existing legacy table intact."""
    if sa.inspect(op.get_bind()).has_table("news"):
        return
    op.create_table(
        "news",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.String(500)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("university", sa.String(200), nullable=False),
        sa.Column("author", sa.String(150)),
        sa.Column("image_url", sa.String(500)),
        sa.Column("source_url", sa.String(500)),
        sa.Column("is_featured", sa.Boolean),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )


def downgrade():
    """Do not drop news: it can predate Alembic and contains editorial data."""
    return
