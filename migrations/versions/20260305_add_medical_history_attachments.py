"""
Add medical_history_attachments table

Revision ID: add_medical_history_attachments_20260305
Revises: add_medical_histories_a1b2c3
Create Date: 2026-03-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_medical_history_attachments_20260305'
down_revision = 'add_medical_histories_a1b2c3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'medical_history_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('medical_history_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_ext', sa.String(length=16), nullable=False),
        sa.Column('mime_type', sa.String(length=128), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('storage_provider', sa.String(length=32), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['household_id'], ['households.id']),
        sa.ForeignKeyConstraint(['medical_history_id'], ['medical_histories.id']),
        sa.ForeignKeyConstraint(['member_id'], ['members.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_key'),
    )
    op.create_index('ix_mha_household_id', 'medical_history_attachments', ['household_id'], unique=False)
    op.create_index('ix_mha_member_id', 'medical_history_attachments', ['member_id'], unique=False)
    op.create_index('ix_mha_history_id', 'medical_history_attachments', ['medical_history_id'], unique=False)


def downgrade():
    op.drop_index('ix_mha_history_id', table_name='medical_history_attachments')
    op.drop_index('ix_mha_member_id', table_name='medical_history_attachments')
    op.drop_index('ix_mha_household_id', table_name='medical_history_attachments')
    op.drop_table('medical_history_attachments')
