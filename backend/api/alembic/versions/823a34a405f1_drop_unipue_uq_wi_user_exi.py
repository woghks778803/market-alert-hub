"""drop unipue uq_wi_user_exi

Revision ID: 823a34a405f1
Revises: 22ab984e2dbf
Create Date: 2025-09-28 20:15:11.009487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '823a34a405f1'
down_revision: Union[str, Sequence[str], None] = '22ab984e2dbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL에서는 UNIQUE 제약이 유니크 인덱스로 구현되므로
    # drop_constraint(type_="unique")가 내부적으로 DROP INDEX를 실행합니다.
    op.drop_constraint(
        "uq_wi_user_exi",
        "watchlist_items",
        type_="unique",
    )


def downgrade() -> None:
    # 롤백 시 동일한 이름과 컬럼으로 유니크 제약을 복구
    op.create_unique_constraint(
        "uq_wi_user_exi",
        "watchlist_items",
        ["user_id", "exchange_instrument_id"],
    )
