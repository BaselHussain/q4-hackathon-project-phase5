"""create_users_table

Revision ID: 1e46b5fe1664
Revises: 9db297eceb60
Create Date: 2026-01-24 19:20:08.658918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e46b5fe1664'
down_revision: Union[str, Sequence[str], None] = '9db297eceb60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table and add user_id to tasks table."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(254), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create index on email for faster lookups
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Add user_id column to tasks table if it doesn't exist
    # First check if column exists by trying to add it
    try:
        op.add_column('tasks', sa.Column('user_id', sa.UUID(), nullable=True))

        # Create index on user_id
        op.create_index('ix_tasks_user_id', 'tasks', ['user_id'])

        # Add foreign key constraint
        op.create_foreign_key(
            'fk_tasks_user_id',
            'tasks', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
    except Exception:
        # Column might already exist, skip
        pass


def downgrade() -> None:
    """Drop users table and remove user_id from tasks table."""
    # Remove foreign key constraint from tasks
    try:
        op.drop_constraint('fk_tasks_user_id', 'tasks', type_='foreignkey')
        op.drop_index('ix_tasks_user_id', 'tasks')
        op.drop_column('tasks', 'user_id')
    except Exception:
        pass

    # Drop users table
    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')
