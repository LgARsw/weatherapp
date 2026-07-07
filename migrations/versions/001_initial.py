"""initial

Revision ID: 001
Revises: 
Create Date: 2026-05-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'weather_queries',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('unit', sa.String(length=1), nullable=False),
        sa.Column('served_from_cache', sa.Boolean(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_weather_queries_city'), 'weather_queries', ['city'], unique=False)
    op.create_index(op.f('ix_weather_queries_id'), 'weather_queries', ['id'], unique=False)
    op.create_index(op.f('ix_weather_queries_timestamp'), 'weather_queries', ['timestamp'], unique=False)

def downgrade() -> None:
    op.drop_table('weather_queries')