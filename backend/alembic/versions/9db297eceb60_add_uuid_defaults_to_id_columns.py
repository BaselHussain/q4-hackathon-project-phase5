"""add_uuid_defaults_to_id_columns

Revision ID: 9db297eceb60
Revises: bea311ce058a
Create Date: 2026-01-23 19:34:54.437637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9db297eceb60'
down_revision: Union[str, Sequence[str], None] = 'bea311ce058a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add UUID defaults to id columns."""
    # Add default UUID generation to users.id
    op.alter_column('users', 'id',
                    server_default=sa.text('gen_random_uuid()'),
                    existing_type=sa.dialects.postgresql.UUID(),
                    existing_nullable=False)

    # Add default UUID generation to tasks.id
    op.alter_column('tasks', 'id',
                    server_default=sa.text('gen_random_uuid()'),
                    existing_type=sa.dialects.postgresql.UUID(),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema - remove UUID defaults from id columns."""
    # Remove default from tasks.id
    op.alter_column('tasks', 'id',
                    server_default=None,
                    existing_type=sa.dialects.postgresql.UUID(),
                    existing_nullable=False)

    # Remove default from users.id
    op.alter_column('users', 'id',
                    server_default=None,
                    existing_type=sa.dialects.postgresql.UUID(),
                    existing_nullable=False)
