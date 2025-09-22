"""add is_valid to core/user-owned tables

Revision ID: 5259e957988c
Revises: d390f9becff0
Create Date: 2025-09-22 14:01:34.394962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5259e957988c'
down_revision: Union[str, Sequence[str], None] = 'd390f9becff0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
