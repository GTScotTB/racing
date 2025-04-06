"""initial formula ford tables

Revision ID: initial_formula_ford_tables
Revises: 
Create Date: 2024-03-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'initial_formula_ford_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create FormulaFordEvent table
    op.create_table('formula_ford_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create FormulaFordCompetitor table
    op.create_table('formula_ford_competitor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('team_association', sa.String(length=100)),
        sa.Column('vehicle_make', sa.String(length=50), nullable=False),
        sa.Column('vehicle_type', sa.String(length=50), nullable=False),
        sa.Column('car_number', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('car_number')
    )

    # Create FormulaFordEventEntry table
    op.create_table('formula_ford_event_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('entry_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text()),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create FormulaFordTechnicalCheck table
    op.create_table('formula_ford_technical_check',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Float()),
        sa.Column('height_status', sa.String(length=10)),
        sa.Column('fuel_status', sa.String(length=10)),
        sa.Column('track_width_status', sa.String(length=10)),
        sa.Column('tyre_check_status', sa.String(length=10)),
        sa.Column('throttle_size_status', sa.String(length=10)),
        sa.Column('ecu_number', sa.String(length=50)),
        sa.Column('ecu_tune', sa.String(length=100)),
        sa.Column('engine_number', sa.String(length=50)),
        sa.Column('map_sensor_status', sa.String(length=10)),
        sa.Column('air_temp_sensor_status', sa.String(length=10)),
        sa.Column('lsd_status', sa.String(length=10)),
        sa.Column('transponder_status', sa.String(length=10)),
        sa.Column('dash_data_status', sa.String(length=10)),
        sa.Column('first_gear_status', sa.String(length=10)),
        sa.Column('flywheel_status', sa.String(length=10)),
        sa.Column('check_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('checked_by', sa.String(length=100)),
        sa.Column('notes', sa.Text()),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create FormulaFordTyreCheck table
    op.create_table('formula_ford_tyre_check',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('practice_tyres_event', sa.String(length=100)),
        sa.Column('p1_used', sa.Boolean(), default=False),
        sa.Column('p2_used', sa.Boolean(), default=False),
        sa.Column('p3_used', sa.Boolean(), default=False),
        sa.Column('p4_used', sa.Boolean(), default=False),
        sa.Column('race_tyres_marked', sa.Boolean(), default=False),
        sa.Column('r1_used', sa.Boolean(), default=False),
        sa.Column('r2_used', sa.Boolean(), default=False),
        sa.Column('r3_used', sa.Boolean(), default=False),
        sa.Column('comments', sa.Text()),
        sa.Column('check_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('checked_by', sa.String(length=100)),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create TimetableSession table
    op.create_table('timetable_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('session_name', sa.String(length=100), nullable=False),
        sa.Column('session_type', sa.String(length=20), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('timetable_session')
    op.drop_table('formula_ford_tyre_check')
    op.drop_table('formula_ford_technical_check')
    op.drop_table('formula_ford_event_entry')
    op.drop_table('formula_ford_competitor')
    op.drop_table('formula_ford_event') 