"""Add thread_tag association table

Revision ID: bafb8206ad9f
Revises: c95845522d4e
Create Date: 2025-05-29 06:52:38.227647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bafb8206ad9f'
down_revision: Union[str, None] = 'c95845522d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
