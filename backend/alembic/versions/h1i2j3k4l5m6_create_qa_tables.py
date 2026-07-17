"""create qa tables for conversation logging

Revision ID: h1i2j3k4l5m6
Revises: g0h1i2j3k4l5
Create Date: 2026-07-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY


# revision identifiers, used by Alembic.
revision = 'h1i2j3k4l5m6'
down_revision = 'g0h1i2j3k4l5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 创建 qa_conversations 表
    op.create_table(
        'qa_conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('conversation_title', sa.String(length=255), nullable=True),
        sa.Column('extra_data', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='AI对话会话表'
    )
    op.create_index('ix_qa_conversations_user_id', 'qa_conversations', ['user_id'])
    op.create_index('ix_qa_conversations_session_id', 'qa_conversations', ['session_id'])
    op.create_index('ix_qa_conversations_created_at', 'qa_conversations', ['created_at'])
    op.create_index('ix_qa_conversations_user_created', 'qa_conversations', ['user_id', 'created_at'], postgresql_using='btree')

    # 2. 创建 qa_corrections 表（先创建，因为 qa_messages 会引用它）
    op.create_table(
        'qa_corrections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('original_answer', sa.Text(), nullable=False),
        sa.Column('corrected_answer', sa.Text(), nullable=False),
        sa.Column('correction_reason', sa.String(length=500), nullable=True),
        sa.Column('corrected_by', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reward_points', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='AI答案纠正记录表'
    )
    # 先创建索引，外键约束稍后添加
    op.create_index('ix_qa_corrections_message_id', 'qa_corrections', ['message_id'])
    op.create_index('ix_qa_corrections_corrected_by', 'qa_corrections', ['corrected_by'])
    op.create_index('ix_qa_corrections_status', 'qa_corrections', ['status'])

    # 3. 创建 qa_messages 表
    op.create_table(
        'qa_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('message_role', sa.String(length=10), nullable=False),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('sources', JSONB, nullable=True),
        sa.Column('tokens_input', sa.Integer(), nullable=True),
        sa.Column('tokens_output', sa.Integer(), nullable=True),
        sa.Column('tokens_total', sa.Integer(), nullable=True),
        sa.Column('cost_yuan', sa.String(length=20), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('retrieval_mode', sa.String(length=20), nullable=True),
        sa.Column('knowledge_tags', ARRAY(sa.String()), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('is_corrected', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('correction_id', sa.Integer(), nullable=True),
        sa.Column('is_followup', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("user_rating IS NULL OR (user_rating BETWEEN 1 AND 5)", name='check_user_rating'),
        sa.CheckConstraint("message_role IN ('user', 'assistant')", name='check_message_role'),
        sa.ForeignKeyConstraint(['conversation_id'], ['qa_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['correction_id'], ['qa_corrections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_message_id'], ['qa_messages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='AI对话消息表'
    )
    op.create_index('ix_qa_messages_conversation_id', 'qa_messages', ['conversation_id'])
    op.create_index('ix_qa_messages_is_corrected', 'qa_messages', ['is_corrected'])
    op.create_index('ix_qa_messages_created_at', 'qa_messages', ['created_at'])
    op.create_index('ix_qa_messages_conversation_created', 'qa_messages', ['conversation_id', 'created_at'], postgresql_using='btree')
    # GIN索引用于数组搜索
    op.create_index('ix_qa_messages_knowledge_tags', 'qa_messages', ['knowledge_tags'], postgresql_using='gin')

    # 4. 现在添加 qa_corrections 的外键约束
    op.create_foreign_key('fk_qa_corrections_message_id', 'qa_corrections', 'qa_messages', ['message_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_qa_corrections_corrected_by', 'qa_corrections', 'users', ['corrected_by'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_qa_corrections_reviewed_by', 'qa_corrections', 'users', ['reviewed_by'], ['id'], ondelete='SET NULL')

    # 5. 创建 qa_ratings 表
    op.create_table(
        'qa_ratings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('overall_rating', sa.Integer(), nullable=False),
        sa.Column('accuracy_rating', sa.Integer(), nullable=True),
        sa.Column('completeness_rating', sa.Integer(), nullable=True),
        sa.Column('clarity_rating', sa.Integer(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('overall_rating BETWEEN 1 AND 5', name='check_overall_rating'),
        sa.CheckConstraint('accuracy_rating IS NULL OR (accuracy_rating BETWEEN 1 AND 5)', name='check_accuracy_rating'),
        sa.CheckConstraint('completeness_rating IS NULL OR (completeness_rating BETWEEN 1 AND 5)', name='check_completeness_rating'),
        sa.CheckConstraint('clarity_rating IS NULL OR (clarity_rating BETWEEN 1 AND 5)', name='check_clarity_rating'),
        sa.ForeignKeyConstraint(['message_id'], ['qa_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', name='uq_qa_ratings_message_id'),
        comment='用户对AI答案的评分表'
    )
    op.create_index('ix_qa_ratings_message_id', 'qa_ratings', ['message_id'], unique=True)


def downgrade() -> None:
    # 按照创建的相反顺序删除
    op.drop_table('qa_ratings')

    # 删除 qa_corrections 的外键
    op.drop_constraint('fk_qa_corrections_reviewed_by', 'qa_corrections', type_='foreignkey')
    op.drop_constraint('fk_qa_corrections_corrected_by', 'qa_corrections', type_='foreignkey')
    op.drop_constraint('fk_qa_corrections_message_id', 'qa_corrections', type_='foreignkey')

    op.drop_table('qa_messages')
    op.drop_table('qa_corrections')
    op.drop_table('qa_conversations')
