"""add avatar_url field

Revision ID: d7a8b9c4e5f6
Revises: c6f9a2d3e5b4
Create Date: 2024-07-10 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7a8b9c4e5f6'
down_revision = 'c6f9a2d3e5b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加头像URL字段
    op.add_column('users', sa.Column('avatar_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # 删除头像URL字段
    op.drop_column('users', 'avatar_url')
