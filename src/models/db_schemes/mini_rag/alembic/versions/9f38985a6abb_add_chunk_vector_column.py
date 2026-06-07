"""add_chunk_vector_column

Revision ID: 9f38985a6abb
Revises: 934ceb499995
Create Date: 2026-06-07 18:09:39.016811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector  # ✅ أضف هذا


# revision identifiers, used by Alembic.
revision: str = '9f38985a6abb'
down_revision: Union[str, None] = '934ceb499995'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ تفعيل pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ✅ إضافة العمود
    op.add_column(
        "data_chunks",
        sa.Column("chunk_vector", Vector(1536), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("data_chunks", "chunk_vector")