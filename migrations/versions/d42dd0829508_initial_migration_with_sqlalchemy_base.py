"""Initial migration with SQLAlchemy Base

Revision ID: d42dd0829508
Revises: 
Create Date: 2025-07-06 19:08:11.633675

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd42dd0829508'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('survey',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.Column('access_token', sa.String(length=100), nullable=True),
    sa.Column('telegram_notifications', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_survey'))
    )
    op.create_index(op.f('ix_survey_access_token'), 'survey', ['access_token'], unique=False)
    op.create_index(op.f('ix_survey_id'), 'survey', ['id'], unique=False)
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('telegram_id', sa.BigInteger(), nullable=True),
    sa.Column('telegram_username', sa.String(length=100), nullable=True),
    sa.Column('telegram_first_name', sa.String(length=100), nullable=True),
    sa.Column('telegram_last_name', sa.String(length=100), nullable=True),
    sa.Column('telegram_photo_url', sa.String(length=500), nullable=True),
    sa.Column('first_name', sa.String(length=100), nullable=True),
    sa.Column('last_name', sa.String(length=100), nullable=True),
    sa.Column('display_name', sa.String(length=100), nullable=True),
    sa.Column('bio', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('language', sa.String(length=10), nullable=False),
    sa.Column('timezone', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user'))
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_telegram_id'), 'user', ['telegram_id'], unique=True)
    op.create_index(op.f('ix_user_telegram_username'), 'user', ['telegram_username'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('userdata',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=100), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=False),
    sa.Column('user_agent', sa.String(length=1000), nullable=False),
    sa.Column('referrer', sa.String(length=500), nullable=True),
    sa.Column('entry_page', sa.String(length=500), nullable=True),
    sa.Column('fingerprint', sa.String(length=200), nullable=False),
    sa.Column('geolocation', sa.JSON(), nullable=True),
    sa.Column('device_info', sa.JSON(), nullable=False),
    sa.Column('browser_info', sa.JSON(), nullable=False),
    sa.Column('telegram_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_userdata'))
    )
    op.create_index(op.f('ix_userdata_id'), 'userdata', ['id'], unique=False)
    op.create_index(op.f('ix_userdata_session_id'), 'userdata', ['session_id'], unique=True)
    op.create_table('question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('survey_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('question_type', sa.String(length=20), nullable=False),
    sa.Column('is_required', sa.Boolean(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('options', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['survey_id'], ['survey.id'], name=op.f('fk_question_survey_id_survey')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_question'))
    )
    op.create_index(op.f('ix_question_id'), 'question', ['id'], unique=False)
    op.create_table('response',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('user_session_id', sa.String(length=100), nullable=False),
    sa.Column('answer', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], name=op.f('fk_response_question_id_question')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_response_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_response'))
    )
    op.create_index(op.f('ix_response_id'), 'response', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_response_id'), table_name='response')
    op.drop_table('response')
    op.drop_index(op.f('ix_question_id'), table_name='question')
    op.drop_table('question')
    op.drop_index(op.f('ix_userdata_session_id'), table_name='userdata')
    op.drop_index(op.f('ix_userdata_id'), table_name='userdata')
    op.drop_table('userdata')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_telegram_username'), table_name='user')
    op.drop_index(op.f('ix_user_telegram_id'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_survey_id'), table_name='survey')
    op.drop_index(op.f('ix_survey_access_token'), table_name='survey')
    op.drop_table('survey')
    # ### end Alembic commands ###
