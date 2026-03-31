"""add recurrence fields

Revision ID: 20260331_0002
Revises: 20260330_0001
Create Date: 2026-03-31 00:00:02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reminders", sa.Column("recurrence_type", sa.String(length=16), nullable=False, server_default="none"))
    op.add_column("reminders", sa.Column("recurrence_interval", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("reminders", sa.Column("last_message_id", sa.BigInteger(), nullable=True))
    op.alter_column("reminders", "recurrence_type", server_default=None)
    op.alter_column("reminders", "recurrence_interval", server_default=None)


def downgrade() -> None:
    op.drop_column("reminders", "last_message_id")
    op.drop_column("reminders", "recurrence_interval")
    op.drop_column("reminders", "recurrence_type")
