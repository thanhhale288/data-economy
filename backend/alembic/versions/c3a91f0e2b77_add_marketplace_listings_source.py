"""add marketplace_listings.source

Revision ID: c3a91f0e2b77
Revises: b7c2e1a94d10
Create Date: 2026-07-25 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a91f0e2b77"
down_revision: Union[str, None] = "b7c2e1a94d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("marketplace_listings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "source",
                sa.String(length=50),
                nullable=False,
                server_default="seed",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("marketplace_listings", schema=None) as batch_op:
        batch_op.drop_column("source")
