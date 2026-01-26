"""add_users_table_and_update_tasks

Revision ID: fefa1f054cc5
Revises:
Create Date: 2026-01-23 19:23:56.181190

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fefa1f054cc5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add missing columns to users table."""
    # Add password_hash column to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=False, server_default=''))

    # Add created_at column to users table
    op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

    # Add last_login_at column to users table
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))

    # Alter email column to be varchar(254) instead of varchar(255)
    op.alter_column('users', 'email',
                    existing_type=sa.String(255),
                    type_=sa.String(254),
                    existing_nullable=False)

    # Remove server_default from password_hash after adding column
    op.alter_column('users', 'password_hash', server_default=None)


def downgrade() -> None:
    """Downgrade schema - remove added columns from users table."""
    # Alter email column back to varchar(255)
    op.alter_column('users', 'email',
                    existing_type=sa.String(254),
                    type_=sa.String(255),
                    existing_nullable=False)

    # Remove last_login_at column
    op.drop_column('users', 'last_login_at')

    # Remove created_at column
    op.drop_column('users', 'created_at')

    # Remove password_hash column
    op.drop_column('users', 'password_hash')
