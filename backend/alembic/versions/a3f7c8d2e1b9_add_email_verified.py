"""add email_verified to users

Revision ID: a3f7c8d2e1b9
Revises: 9c4f1a2b7e3d
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f7c8d2e1b9'
down_revision: Union[str, None] = '9c4f1a2b7e3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default=true：存量用户（含默认 admin）迁移后视为已验证，避免被锁死。
    # 新注册由代码显式设为 False。
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
