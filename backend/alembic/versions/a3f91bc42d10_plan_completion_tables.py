"""plan completion: transfers, notifications, audit, extensions

Revision ID: a3f91bc42d10
Revises: 1b4e1c2c7fea
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a3f91bc42d10"
down_revision: Union[str, None] = "1b4e1c2c7fea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("faculty", sa.String(length=200), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("projects", sa.Column("join_code", sa.String(length=32), nullable=True))
    op.create_index("ix_projects_join_code", "projects", ["join_code"], unique=True)

    op.add_column("auctions", sa.Column("resource_type", sa.String(length=32), server_default="consultation"))
    op.add_column("auctions", sa.Column("location", sa.String(length=200), nullable=True))
    op.add_column("auctions", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("auctions", sa.Column("min_bid", sa.Numeric(78, 0), server_default="1"))
    op.add_column("auctions", sa.Column("bid_step", sa.Numeric(78, 0), server_default="1"))
    op.add_column("auctions", sa.Column("image_url", sa.String(length=500), nullable=True))

    op.create_table(
        "bid_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("auction_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(78, 0), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["auction_id"], ["auctions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transfers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(78, 0), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="completed"),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("is_read", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=200), nullable=False),
        sa.Column("object_ref", sa.String(length=300), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("transfers")
    op.drop_table("bid_events")
    op.drop_column("auctions", "image_url")
    op.drop_column("auctions", "bid_step")
    op.drop_column("auctions", "min_bid")
    op.drop_column("auctions", "description")
    op.drop_column("auctions", "location")
    op.drop_column("auctions", "resource_type")
    op.drop_index("ix_projects_join_code", table_name="projects")
    op.drop_column("projects", "join_code")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "faculty")
