"""
Add medical_histories table

Revision ID: add_medical_histories_a1b2c3
Revises: f041ccf3b820
Create Date: 2025-12-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_medical_histories_a1b2c3'
down_revision = 'f041ccf3b820'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'medical_histories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('disease_name', sa.String(length=120), nullable=False),
        sa.Column('onset_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_ongoing', sa.Boolean(), nullable=False),
        sa.Column('is_on_medication', sa.Boolean(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['household_id'], ['households.id']),
        sa.ForeignKeyConstraint(['member_id'], ['members.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_medical_histories_member_id',
        'medical_histories',
        ['member_id'],
    )
    op.create_index(
        'ix_medical_histories_member_onset',
        'medical_histories',
        ['member_id', 'onset_date'],
    )


def downgrade():
    op.drop_index('ix_medical_histories_member_onset', table_name='medical_histories')
    op.drop_index('ix_medical_histories_member_id', table_name='medical_histories')
    op.drop_table('medical_histories')
