"""add phone_verified field

Revision ID: g0h1i2j3k4l5
Revises: f9c6d7e8a9b0
Create Date: 2024-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g0h1i2j3k4l5'
down_revision = 'f9c6d7e8a9b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 phone_verified 字段（手机号是否已验证）
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'phone_verified')
