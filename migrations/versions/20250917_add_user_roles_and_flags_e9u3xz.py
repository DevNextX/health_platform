"""
Add role, must_change_password, last_login_at to users table

Revision ID: add_user_roles_and_flags_e9u3xz
Revises: 
Create Date: 2025-09-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_roles_and_flags_e9u3xz'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users') as batch_op:
        try:
            batch_op.add_column(sa.Column('role', sa.String(length=20), nullable=False, server_default='USER'))
        except Exception:
            # Ignore if the column already exists or cannot be added; migration may be re-run.
            pass
        try:
            # SQLite uses 0/1; MySQL uses tinyint(1)
            batch_op.add_column(sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        except Exception:
            # Ignore if the column already exists or cannot be added; migration may be re-run.
            pass
        try:
            batch_op.add_column(sa.Column('last_login_at', sa.DateTime(), nullable=True))
        except Exception:
            # Ignore if the column already exists or cannot be added; migration may be re-run.
        # Ignore if the column could not be altered; migration may be re-run.
            pass
    # Remove server defaults if set
    try:
        with op.batch_alter_table('users') as batch_op:
            batch_op.alter_column('role', server_default=None)
            batch_op.alter_column('must_change_password', server_default=None)
    except Exception:
        # Ignore if the column does not exist or cannot be altered; migration may be re-run.
        pass

            # Ignore if the column does not exist or cannot be dropped; migration may be re-run.
            # Ignore if the column does not exist or cannot be dropped; migration may be re-run.
def downgrade():
    with op.batch_alter_table('users') as batch_op:
        try:
            batch_op.drop_column('last_login_at')
            # Ignore if the column does not exist or cannot be dropped; migration may be re-run.
        except Exception:
            pass
        try:
            batch_op.drop_column('must_change_password')
        except Exception:
            pass
        try:
            batch_op.drop_column('role')
        except Exception:
            pass
