"""Initial migration - create all tables

Revision ID: 89d071d826ca
Revises:
Create Date: 2025-07-05 01:03:22.212181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "89d071d826ca"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "user",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=True),
        sa.Column("telegram_username", sa.String(100), nullable=True),
        sa.Column("telegram_first_name", sa.String(100), nullable=True),
        sa.Column("telegram_last_name", sa.String(100), nullable=True),
        sa.Column("telegram_photo_url", sa.String(500), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("bio", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_admin", sa.Boolean, default=False),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("last_login", sa.DateTime, nullable=True),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("timezone", sa.String(50), default="UTC"),
    )

    # Create surveys table
    op.create_table(
        "survey",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_public", sa.Boolean, default=True),
        sa.Column("access_token", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("starts_at", sa.DateTime, nullable=True),
        sa.Column("ends_at", sa.DateTime, nullable=True),
        sa.Column("settings", sa.JSON, nullable=True),
    )

    # Create questions table
    op.create_table(
        "question",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("survey_id", sa.Integer, sa.ForeignKey("survey.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("is_required", sa.Boolean, default=True),
        sa.Column("order", sa.Integer, default=0),
        sa.Column("options", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Create user_data table
    op.create_table(
        "userdata",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String(100), unique=True, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("browser_fingerprint", sa.JSON, nullable=True),
        sa.Column("device_info", sa.JSON, nullable=True),
        sa.Column("location_data", sa.JSON, nullable=True),
        sa.Column("telegram_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Create responses table
    op.create_table(
        "response",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "question_id", sa.Integer, sa.ForeignKey("question.id"), nullable=False
        ),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=True),
        sa.Column("user_session_id", sa.String(100), nullable=False),
        sa.Column("answer", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Create indexes
    op.create_index("idx_user_telegram_id", "user", ["telegram_id"])
    op.create_index("idx_user_username", "user", ["username"])
    op.create_index("idx_user_email", "user", ["email"])
    op.create_index("idx_survey_access_token", "survey", ["access_token"])
    op.create_index("idx_question_survey_id", "question", ["survey_id"])
    op.create_index("idx_response_question_id", "response", ["question_id"])
    op.create_index("idx_response_user_id", "response", ["user_id"])
    op.create_index("idx_response_session_id", "response", ["user_session_id"])
    op.create_index("idx_userdata_session_id", "userdata", ["session_id"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("response")
    op.drop_table("userdata")
    op.drop_table("question")
    op.drop_table("survey")
    op.drop_table("user")
