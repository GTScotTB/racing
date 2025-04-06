"""Event-wide tech and tyre requirements

Revision ID: event_wide_requirements
Revises: initial_formula_ford_tables
Create Date: 2023-05-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'event_wide_requirements'
down_revision = 'initial_formula_ford_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create EventTechnicalRequirements table
    op.create_table('event_technical_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('min_weight_requirement', sa.Float(), nullable=True),
        sa.Column('height_requirement', sa.String(length=255), nullable=True),
        sa.Column('fuel_requirement', sa.String(length=255), nullable=True),
        sa.Column('safety_equipment_requirement', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('date_created', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create CompetitorTechnicalRecord table
    op.create_table('competitor_technical_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('height_check', sa.Boolean(), nullable=True),
        sa.Column('fuel_check', sa.Boolean(), nullable=True),
        sa.Column('safety_equipment_check', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('inspector_name', sa.String(length=100), nullable=True),
        sa.Column('check_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entry_id'], ['formula_ford_event_entry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_id')
    )
    
    # Create EventTyreRequirements table
    op.create_table('event_tyre_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('allowed_practice_brands', sa.String(length=255), nullable=True),
        sa.Column('allowed_practice_compounds', sa.String(length=255), nullable=True),
        sa.Column('allowed_race_brands', sa.String(length=255), nullable=True),
        sa.Column('allowed_race_compounds', sa.String(length=255), nullable=True),
        sa.Column('max_sets_allowed', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('date_created', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create CompetitorTyreRecord table
    op.create_table('competitor_tyre_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('practice_tyre_brand', sa.String(length=100), nullable=True),
        sa.Column('practice_tyre_compound', sa.String(length=100), nullable=True),
        sa.Column('practice_tyre_serial_numbers', sa.String(length=255), nullable=True),
        sa.Column('race_tyre_brand', sa.String(length=100), nullable=True),
        sa.Column('race_tyre_compound', sa.String(length=100), nullable=True),
        sa.Column('race_tyre_serial_numbers', sa.String(length=255), nullable=True),
        sa.Column('sets_used', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('inspector_name', sa.String(length=100), nullable=True),
        sa.Column('check_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entry_id'], ['formula_ford_event_entry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_id')
    )


def downgrade():
    op.drop_table('competitor_tyre_record')
    op.drop_table('event_tyre_requirements')
    op.drop_table('competitor_technical_record')
    op.drop_table('event_technical_requirements') 