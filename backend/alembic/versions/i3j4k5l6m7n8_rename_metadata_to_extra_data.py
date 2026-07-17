"""rename metadata to extra_data in qa_conversations

Revision ID: i3j4k5l6m7n8
Revises: h1i2j3k4l5m6
Create Date: 2026-07-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i3j4k5l6m7n8'
down_revision = 'h1i2j3k4l5m6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 重命名 metadata 字段为 extra_data（避免SQLAlchemy保留字冲突）
    op.alter_column('qa_conversations', 'metadata', new_column_name='extra_data')


def downgrade() -> None:
    # 回退：重命名 extra_data 为 metadata
    op.alter_column('qa_conversations', 'extra_data', new_column_name='metadata')
