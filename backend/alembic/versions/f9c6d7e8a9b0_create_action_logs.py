"""create action_logs table

Revision ID: f9c6d7e8a9b0
Revises: e8b9c5d6f7g8
Create Date: 2024-07-12 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'f9c6d7e8a9b0'
down_revision = 'e8b9c5d6f7g8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建action_logs表
    op.create_table(
        'action_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('details', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户操作日志表'
    )

    # 创建索引
    op.create_index('ix_action_logs_user_id', 'action_logs', ['user_id'])
    op.create_index('ix_action_logs_action', 'action_logs', ['action'])
    op.create_index('ix_action_logs_created_at', 'action_logs', ['created_at'])
    # 复合索引：user_id + created_at（常用查询）
    op.create_index('ix_action_logs_user_created', 'action_logs', ['user_id', 'created_at'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_action_logs_user_created', 'action_logs')
    op.drop_index('ix_action_logs_created_at', 'action_logs')
    op.drop_index('ix_action_logs_action', 'action_logs')
    op.drop_index('ix_action_logs_user_id', 'action_logs')

    # 删除表
    op.drop_table('action_logs')
