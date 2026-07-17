"""add password_changed_at to users

Revision ID: 9c4f1a2b7e3d
Revises: 1be69940de33
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c4f1a2b7e3d'
down_revision: Union[str, None] = '1be69940de33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增可空列；存量用户保持 NULL（get_current_user 对 NULL 不做限制，向后兼容）。
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_changed_at')
