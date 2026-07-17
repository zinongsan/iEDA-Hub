"""add notification settings

Revision ID: e8b9c5d6f7g8
Revises: d7a8b9c4e5f6
Create Date: 2024-07-10 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8b9c5d6f7g8'
down_revision = 'd7a8b9c4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加通知偏好字段
    op.add_column('users', sa.Column('notification_email', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('notification_system', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('notification_course', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('notification_announcement', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    # 删除通知偏好字段
    op.drop_column('users', 'notification_announcement')
    op.drop_column('users', 'notification_course')
    op.drop_column('users', 'notification_system')
    op.drop_column('users', 'notification_email')
