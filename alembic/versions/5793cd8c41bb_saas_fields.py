"""saas_fields

Revision ID: 5793cd8c41bb
Revises: c2ca5541e420
Create Date: 2026-04-24 14:35:32.974702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '5793cd8c41bb'
down_revision: Union[str, None] = 'c2ca5541e420'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

role_enum = sa.Enum('user', 'admin', name='role')


def upgrade() -> None:
    role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('users', sa.Column('role', role_enum, nullable=False, server_default='user'))
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('chars_used_this_period', sa.Integer(), nullable=False, server_default='0'))

    op.create_unique_constraint('uq_users_stripe_customer_id', 'users', ['stripe_customer_id'])
    op.create_unique_constraint('uq_users_stripe_subscription_id', 'users', ['stripe_subscription_id'])


def downgrade() -> None:
    op.drop_constraint('uq_users_stripe_subscription_id', 'users', type_='unique')
    op.drop_constraint('uq_users_stripe_customer_id', 'users', type_='unique')
    op.drop_column('users', 'chars_used_this_period')
    op.drop_column('users', 'billing_period_start')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'role')
    role_enum.drop(op.get_bind(), checkfirst=True)
