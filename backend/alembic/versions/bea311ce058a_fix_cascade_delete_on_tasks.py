"""fix_cascade_delete_on_tasks

Revision ID: bea311ce058a
Revises: fefa1f054cc5
Create Date: 2026-01-23 19:26:47.029612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bea311ce058a'
down_revision: Union[str, Sequence[str], None] = 'fefa1f054cc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - fix foreign key to use CASCADE delete."""
    # Drop existing foreign key constraint
    op.drop_constraint('tasks_user_id_fkey', 'tasks', type_='foreignkey')

    # Recreate foreign key with CASCADE delete
    op.create_foreign_key(
        'tasks_user_id_fkey',
        'tasks', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema - revert to NO ACTION."""
    # Drop CASCADE foreign key
    op.drop_constraint('tasks_user_id_fkey', 'tasks', type_='foreignkey')

    # Recreate foreign key without CASCADE
    op.create_foreign_key(
        'tasks_user_id_fkey',
        'tasks', 'users',
        ['user_id'], ['id']
    )
