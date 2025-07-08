"""add_respondent_architecture_tables

Revision ID: 9d9bb9d0e800
Revises: cf061d6fb570
Create Date: 2025-07-07 00:11:13.721651

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '9d9bb9d0e800'
down_revision = 'cf061d6fb570'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create profiles table ###
    op.create_table('profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_picture_url', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_profiles_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_profiles')),
        sa.UniqueConstraint('user_id', name=op.f('uq_profiles_user_id'))
    )
    op.create_index(op.f('ix_profiles_user_id'), 'profiles', ['user_id'], unique=False)

    # ### Create respondents table ###
    op.create_table('respondents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('browser_fingerprint', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('geolocation', sa.JSON(), nullable=True),
        sa.Column('precise_location', sa.JSON(), nullable=True),
        sa.Column('device_info', sa.JSON(), nullable=True),
        sa.Column('telegram_data', sa.JSON(), nullable=True),
        sa.Column('custom_data', sa.JSON(), nullable=True),
        sa.Column('is_merged', sa.Boolean(), nullable=False),
        sa.Column('merged_at', sa.DateTime(), nullable=True),
        sa.Column('merged_from_id', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merged_from_id'], ['respondents.id'], name=op.f('fk_respondents_merged_from_id_respondents')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_respondents_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_respondents'))
    )
    op.create_index(op.f('ix_respondents_browser_fingerprint'), 'respondents', ['browser_fingerprint'], unique=False)
    op.create_index(op.f('ix_respondents_ip_address'), 'respondents', ['ip_address'], unique=False)
    op.create_index(op.f('ix_respondents_is_anonymous'), 'respondents', ['is_anonymous'], unique=False)
    op.create_index(op.f('ix_respondents_session_id'), 'respondents', ['session_id'], unique=False)
    op.create_index(op.f('ix_respondents_user_id'), 'respondents', ['user_id'], unique=False)

    # ### Create survey_data_requirements table ###
    op.create_table('survey_data_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('requires_location', sa.Boolean(), nullable=False),
        sa.Column('requires_precise_location', sa.Boolean(), nullable=False),
        sa.Column('requires_personal_data', sa.Boolean(), nullable=False),
        sa.Column('requires_technical_data', sa.Boolean(), nullable=False),
        sa.Column('gdpr_compliant', sa.Boolean(), nullable=False),
        sa.Column('consent_required', sa.JSON(), nullable=True),
        sa.Column('data_retention_days', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], name=op.f('fk_survey_data_requirements_survey_id_surveys')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_survey_data_requirements')),
        sa.UniqueConstraint('survey_id', name=op.f('uq_survey_data_requirements_survey_id'))
    )
    op.create_index(op.f('ix_survey_data_requirements_survey_id'), 'survey_data_requirements', ['survey_id'], unique=False)

    # ### Create consent_logs table ###
    op.create_table('consent_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('respondent_id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=True),
        sa.Column('consent_type', sa.String(length=50), nullable=False),
        sa.Column('is_granted', sa.Boolean(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('consent_version', sa.String(length=20), nullable=False),
        sa.Column('consent_source', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['respondent_id'], ['respondents.id'], name=op.f('fk_consent_logs_respondent_id_respondents')),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], name=op.f('fk_consent_logs_survey_id_surveys')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_consent_logs'))
    )
    op.create_index(op.f('ix_consent_logs_consent_type'), 'consent_logs', ['consent_type'], unique=False)
    op.create_index(op.f('ix_consent_logs_granted_at'), 'consent_logs', ['granted_at'], unique=False)
    op.create_index(op.f('ix_consent_logs_is_granted'), 'consent_logs', ['is_granted'], unique=False)
    op.create_index(op.f('ix_consent_logs_respondent_id'), 'consent_logs', ['respondent_id'], unique=False)
    op.create_index(op.f('ix_consent_logs_survey_id'), 'consent_logs', ['survey_id'], unique=False)

    # ### Create respondent_surveys table ###
    op.create_table('respondent_surveys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('respondent_id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('questions_answered', sa.Integer(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
        sa.Column('completion_source', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['respondent_id'], ['respondents.id'], name=op.f('fk_respondent_surveys_respondent_id_respondents')),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], name=op.f('fk_respondent_surveys_survey_id_surveys')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_respondent_surveys')),
        sa.UniqueConstraint('respondent_id', 'survey_id', name=op.f('uq_respondent_surveys_respondent_id_survey_id'))
    )
    op.create_index(op.f('ix_respondent_surveys_respondent_id'), 'respondent_surveys', ['respondent_id'], unique=False)
    op.create_index(op.f('ix_respondent_surveys_status'), 'respondent_surveys', ['status'], unique=False)
    op.create_index(op.f('ix_respondent_surveys_survey_id'), 'respondent_surveys', ['survey_id'], unique=False)

    # ### Create respondent_events table ###
    op.create_table('respondent_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('respondent_id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=True),
        sa.Column('response_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['respondent_id'], ['respondents.id'], name=op.f('fk_respondent_events_respondent_id_respondents')),
        sa.ForeignKeyConstraint(['response_id'], ['responses.id'], name=op.f('fk_respondent_events_response_id_responses')),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], name=op.f('fk_respondent_events_survey_id_surveys')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_respondent_events'))
    )
    op.create_index(op.f('ix_respondent_events_created_at'), 'respondent_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_respondent_events_event_type'), 'respondent_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_respondent_events_respondent_id'), 'respondent_events', ['respondent_id'], unique=False)

    # ### Add respondent_id column to responses table ###
    op.add_column('response', sa.Column('respondent_id', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('fk_response_respondent_id_respondents'), 'response', 'respondents', ['respondent_id'], ['id'])
    op.create_index(op.f('ix_response_respondent_id'), 'response', ['respondent_id'], unique=False)

    # ### Add Profile and Respondent relationships to User table ###
    # Note: Relationships are defined in the model, no schema changes needed


def downgrade() -> None:
    # ### Drop foreign keys and indexes ###
    op.drop_index(op.f('ix_response_respondent_id'), table_name='response')
    op.drop_constraint(op.f('fk_response_respondent_id_respondents'), 'response', type_='foreignkey')
    op.drop_column('response', 'respondent_id')

    # ### Drop respondent_events table ###
    op.drop_index(op.f('ix_respondent_events_respondent_id'), table_name='respondent_events')
    op.drop_index(op.f('ix_respondent_events_event_type'), table_name='respondent_events')
    op.drop_index(op.f('ix_respondent_events_created_at'), table_name='respondent_events')
    op.drop_table('respondent_events')

    # ### Drop respondent_surveys table ###
    op.drop_index(op.f('ix_respondent_surveys_survey_id'), table_name='respondent_surveys')
    op.drop_index(op.f('ix_respondent_surveys_status'), table_name='respondent_surveys')
    op.drop_index(op.f('ix_respondent_surveys_respondent_id'), table_name='respondent_surveys')
    op.drop_table('respondent_surveys')

    # ### Drop consent_logs table ###
    op.drop_index(op.f('ix_consent_logs_survey_id'), table_name='consent_logs')
    op.drop_index(op.f('ix_consent_logs_respondent_id'), table_name='consent_logs')
    op.drop_index(op.f('ix_consent_logs_is_granted'), table_name='consent_logs')
    op.drop_index(op.f('ix_consent_logs_granted_at'), table_name='consent_logs')
    op.drop_index(op.f('ix_consent_logs_consent_type'), table_name='consent_logs')
    op.drop_table('consent_logs')

    # ### Drop survey_data_requirements table ###
    op.drop_index(op.f('ix_survey_data_requirements_survey_id'), table_name='survey_data_requirements')
    op.drop_table('survey_data_requirements')

    # ### Drop respondents table ###
    op.drop_index(op.f('ix_respondents_user_id'), table_name='respondents')
    op.drop_index(op.f('ix_respondents_session_id'), table_name='respondents')
    op.drop_index(op.f('ix_respondents_is_anonymous'), table_name='respondents')
    op.drop_index(op.f('ix_respondents_ip_address'), table_name='respondents')
    op.drop_index(op.f('ix_respondents_browser_fingerprint'), table_name='respondents')
    op.drop_table('respondents')

    # ### Drop profiles table ###
    op.drop_index(op.f('ix_profiles_user_id'), table_name='profiles')
    op.drop_table('profiles')
