"""schema: AssetType에 'fiat' 추가 및 instruments 데이터 정정

Revision ID: 22ab984e2dbf
Revises: 9a63b0cc60f7
Create Date: 2025-09-26 19:10:39.733133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22ab984e2dbf'
down_revision: Union[str, Sequence[str], None] = '9a63b0cc60f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ENUM 값 집합 (순서 포함)
OLD_ENUM = ("crypto", "fx", "stock", "future")
NEW_ENUM = ("crypto", "fiat", "fx", "stock", "future")

# 이 열거형을 사용하는 테이블과 컬럼 목록
# 필요 시 여기에 다른 테이블도 추가하세요.
TARGETS = [
    ("instruments", "asset_type"),
]

# 'fiat' 로 바꾸고 싶은 심볼들 (서비스 상황에 맞게 조정)
FIAT_SYMBOLS = ("KRW", "USD", "EUR", "JPY", "CNY")

def _alter_enum(table: str, column: str, values: tuple[str, ...]):
    # MySQL/MariaDB: ENUM 값 변경은 MODIFY로 처리
    enum_ddl = ",".join([f"'{v}'" for v in values])
    op.execute(
        f"ALTER TABLE `{table}` MODIFY `{column}` ENUM({enum_ddl}) NOT NULL"
    )

def upgrade():
    # 1) ENUM에 'fiat' 추가 (사용하는 모든 테이블/컬럼에 대해)
    for table, column in TARGETS:
        _alter_enum(table, column, NEW_ENUM)

    # 2) 데이터 정정: KRW 등은 fiat로 업데이트
    op.execute(
        f"""
        UPDATE instruments
           SET asset_type = 'fiat'
         WHERE symbol IN ({",".join([f"'{s}'" for s in FIAT_SYMBOLS])})
        """
    )

def downgrade():
    # 다운그레이드: 축소 전에 'fiat' 값을 허용 집합 내 값(여기선 'crypto')으로 되돌림
    op.execute("UPDATE instruments SET asset_type = 'crypto' WHERE asset_type = 'fiat'")

    # ENUM 집합을 원래대로 축소
    for table, column in TARGETS:
        _alter_enum(table, column, OLD_ENUM)
