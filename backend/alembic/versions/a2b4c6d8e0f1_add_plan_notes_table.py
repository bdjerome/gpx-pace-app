"""add plan notes table

Revision ID: a2b4c6d8e0f1
Revises: 9f01bc049c94
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b4c6d8e0f1'
down_revision: Union[str, None] = '9f01bc049c94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plan_notes',
        sa.Column('plan_id', sa.UUID(), nullable=False),
        sa.Column('km', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['race_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('plan_id', 'km'),
    )


def downgrade() -> None:
    op.drop_table('plan_notes')
