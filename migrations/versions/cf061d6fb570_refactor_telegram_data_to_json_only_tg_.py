"""refactor_telegram_data_to_json_only_tg_id_separate

Revision ID: cf061d6fb570
Revises: 40358149e8ad
Create Date: 2025-07-06 21:55:30.414704

"""
from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = 'cf061d6fb570'
down_revision = '40358149e8ad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Step 1: Add new tg_id column
    op.add_column('userdata', sa.Column('tg_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_userdata_tg_id'), 'userdata', ['tg_id'], unique=False)

    # Step 2: Migrate data from old fields to new structure
    # Create connection to execute raw SQL
    connection = op.get_bind()

    # Get all records with telegram data
    result = connection.execute(
        sa.text("""
            SELECT id, telegram_user_id, telegram_username, telegram_first_name,
                   telegram_last_name, telegram_language_code, telegram_photo_url,
                   telegram_data
            FROM userdata
            WHERE telegram_user_id IS NOT NULL
        """)
    )

    # Process each record
    for row in result:
        # Copy telegram_user_id to tg_id
        tg_id = row.telegram_user_id

        # Prepare existing telegram_data or create new dict
        existing_data = {}
        if row.telegram_data:
            try:
                existing_data = json.loads(row.telegram_data) if isinstance(row.telegram_data, str) else row.telegram_data
            except (json.JSONDecodeError, TypeError):
                existing_data = {}

        # Add individual fields to telegram_data JSON
        telegram_data = existing_data.copy()
        if row.telegram_username:
            telegram_data['username'] = row.telegram_username
        if row.telegram_first_name:
            telegram_data['first_name'] = row.telegram_first_name
        if row.telegram_last_name:
            telegram_data['last_name'] = row.telegram_last_name
        if row.telegram_language_code:
            telegram_data['language_code'] = row.telegram_language_code
        if row.telegram_photo_url:
            telegram_data['photo_url'] = row.telegram_photo_url

        # Update the record
        connection.execute(
            sa.text("""
                UPDATE userdata
                SET tg_id = :tg_id, telegram_data = :telegram_data
                WHERE id = :id
            """),
            {
                'tg_id': tg_id,
                'telegram_data': json.dumps(telegram_data) if telegram_data else None,
                'id': row.id
            }
        )

    # Step 3: Drop old columns
    op.drop_column('userdata', 'telegram_language_code')
    op.drop_column('userdata', 'telegram_photo_url')
    op.drop_column('userdata', 'telegram_username')
    op.drop_column('userdata', 'telegram_first_name')
    op.drop_column('userdata', 'telegram_last_name')
    op.drop_column('userdata', 'telegram_user_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Step 1: Add old columns back
    op.add_column('userdata', sa.Column('telegram_user_id', sa.INTEGER(), nullable=True))
    op.add_column('userdata', sa.Column('telegram_last_name', sa.VARCHAR(length=100), nullable=True))
    op.add_column('userdata', sa.Column('telegram_first_name', sa.VARCHAR(length=100), nullable=True))
    op.add_column('userdata', sa.Column('telegram_username', sa.VARCHAR(length=100), nullable=True))
    op.add_column('userdata', sa.Column('telegram_photo_url', sa.VARCHAR(length=500), nullable=True))
    op.add_column('userdata', sa.Column('telegram_language_code', sa.VARCHAR(length=10), nullable=True))

    # Step 2: Migrate data back from new structure to old fields
    connection = op.get_bind()

    # Get all records with telegram data
    result = connection.execute(
        sa.text("SELECT id, tg_id, telegram_data FROM userdata WHERE tg_id IS NOT NULL")
    )

    # Process each record
    for row in result:
        # Prepare data from telegram_data JSON
        telegram_data = {}
        if row.telegram_data:
            try:
                telegram_data = json.loads(row.telegram_data) if isinstance(row.telegram_data, str) else row.telegram_data
            except (json.JSONDecodeError, TypeError):
                telegram_data = {}

        # Update the record with individual fields
        connection.execute(
            sa.text("""
                UPDATE userdata
                SET telegram_user_id = :telegram_user_id,
                    telegram_username = :telegram_username,
                    telegram_first_name = :telegram_first_name,
                    telegram_last_name = :telegram_last_name,
                    telegram_language_code = :telegram_language_code,
                    telegram_photo_url = :telegram_photo_url
                WHERE id = :id
            """),
            {
                'telegram_user_id': row.tg_id,
                'telegram_username': telegram_data.get('username'),
                'telegram_first_name': telegram_data.get('first_name'),
                'telegram_last_name': telegram_data.get('last_name'),
                'telegram_language_code': telegram_data.get('language_code'),
                'telegram_photo_url': telegram_data.get('photo_url'),
                'id': row.id
            }
        )

    # Step 3: Drop new columns
    op.drop_index(op.f('ix_userdata_tg_id'), table_name='userdata')
    op.drop_column('userdata', 'tg_id')
    # ### end Alembic commands ###
