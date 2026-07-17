"""add user profile fields

Revision ID: b5e8f9c3d4a2
Revises: a3f7c8d2e1b9
Create Date: 2026-07-10 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5e8f9c3d4a2'
down_revision = 'a3f7c8d2e1b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加个人信息字段
    op.add_column('users', sa.Column('real_name', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('student_id', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('school', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('profile_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('profile_completed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # 移除个人信息字段
    op.drop_column('users', 'profile_completed_at')
    op.drop_column('users', 'profile_completed')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'age')
    op.drop_column('users', 'school')
    op.drop_column('users', 'student_id')
    op.drop_column('users', 'role')
    op.drop_column('users', 'real_name')
