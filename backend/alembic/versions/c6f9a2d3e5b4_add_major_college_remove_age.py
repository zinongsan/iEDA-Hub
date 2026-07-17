"""add major and college fields, remove age

Revision ID: c6f9a2d3e5b4
Revises: b5e8f9c3d4a2
Create Date: 2026-07-10 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6f9a2d3e5b4'
down_revision = 'b5e8f9c3d4a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加专业和学院字段
    op.add_column('users', sa.Column('major', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('college', sa.String(length=100), nullable=True))

    # 删除年龄字段
    op.drop_column('users', 'age')


def downgrade() -> None:
    # 恢复年龄字段
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))

    # 删除专业和学院字段
    op.drop_column('users', 'college')
    op.drop_column('users', 'major')
