"""fix cost_yuan field length

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-07-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j4k5l6m7n8o9'
down_revision = 'i3j4k5l6m7n8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """修改 cost_yuan 字段长度从 VARCHAR(20) 改为 NUMERIC(12,6)"""
    # 方案1: 改为 NUMERIC 类型（更合理）
    op.alter_column('qa_messages', 'cost_yuan',
                    type_=sa.NUMERIC(12, 6),
                    existing_type=sa.VARCHAR(20),
                    existing_nullable=True,
                    postgresql_using='cost_yuan::numeric')


def downgrade() -> None:
    """回退到 VARCHAR(20)"""
    op.alter_column('qa_messages', 'cost_yuan',
                    type_=sa.VARCHAR(20),
                    existing_type=sa.NUMERIC(12, 6),
                    existing_nullable=True,
                    postgresql_using='cost_yuan::varchar')
