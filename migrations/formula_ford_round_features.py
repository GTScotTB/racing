"""formula_ford_round_features

Revision ID: formula_ford_round_features
Create Date: 2023-04-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'formula_ford_round_features'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add car_number_round to FormulaFordEventEntry
    op.add_column('formula_ford_event_entry', sa.Column('car_number_round', sa.Integer(), nullable=True))
    
    # Create CompetitorWeightHeight table
    op.create_table('competitor_weight_height',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('qual_weight', sa.Float(), nullable=True),
        sa.Column('qual_height', sa.String(length=10), nullable=True),
        sa.Column('r1_weight', sa.Float(), nullable=True),
        sa.Column('r1_height', sa.String(length=10), nullable=True),
        sa.Column('r2_weight', sa.Float(), nullable=True),
        sa.Column('r2_height', sa.String(length=10), nullable=True),
        sa.Column('r3_weight', sa.Float(), nullable=True),
        sa.Column('r3_height', sa.String(length=10), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create CompetitorECU table
    op.create_table('competitor_ecu',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('ecu_number', sa.String(length=50), nullable=True),
        sa.Column('inspector_name', sa.String(length=100), nullable=True),
        sa.Column('check_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create CompetitorEngine table
    op.create_table('competitor_engine',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('engine_number', sa.String(length=50), nullable=True),
        sa.Column('inspector_name', sa.String(length=100), nullable=True),
        sa.Column('check_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create TechnicalCheck table
    op.create_table('technical_check',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=True),
        sa.Column('result', sa.String(length=255), nullable=True),
        sa.Column('inspector_name', sa.String(length=100), nullable=True),
        sa.Column('check_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop the new tables
    op.drop_table('technical_check')
    op.drop_table('competitor_engine')
    op.drop_table('competitor_ecu')
    op.drop_table('competitor_weight_height')
    
    # Remove the added column
    op.drop_column('formula_ford_event_entry', 'car_number_round') 