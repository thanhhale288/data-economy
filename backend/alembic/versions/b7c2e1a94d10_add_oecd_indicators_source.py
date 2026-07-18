"""add oecd_indicators.source

Revision ID: b7c2e1a94d10
Revises: 48406b8f82a5
Create Date: 2026-07-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c2e1a94d10"
down_revision: Union[str, None] = "48406b8f82a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("oecd_indicators", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "source",
                sa.String(length=50),
                nullable=False,
                server_default="OECD",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("oecd_indicators", schema=None) as batch_op:
        batch_op.drop_column("source")
