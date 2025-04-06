"""Add TyreChecklist table

Revision ID: tyre_checklist_001
Revises: 
Create Date: 2025-04-06

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'tyre_checklist_001'
down_revision = None  # Set this to the ID of the previous migration if any
branch_labels = None
depends_on = None


def upgrade():
    # Create TyreChecklist table
    op.create_table(
        'tyre_checklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        
        # Columns for marking tyres
        sa.Column('tyres_marked_practice', sa.Boolean(), default=False),
        sa.Column('tyres_marked_qualifying', sa.Boolean(), default=False),
        
        # Columns for practice sessions
        sa.Column('practice1_checked', sa.Boolean(), default=False),
        sa.Column('practice2_checked', sa.Boolean(), default=False),
        sa.Column('practice3_checked', sa.Boolean(), default=False),
        sa.Column('practice4_checked', sa.Boolean(), default=False),
        
        # Qualifying and races
        sa.Column('qualifying_checked', sa.Boolean(), default=False),
        sa.Column('race1_checked', sa.Boolean(), default=False),
        sa.Column('race2_checked', sa.Boolean(), default=False),
        sa.Column('race3_checked', sa.Boolean(), default=False),
        
        # Additional information
        sa.Column('inspector_name', sa.String(100), nullable=True),
        sa.Column('last_updated', sa.DateTime, default=datetime.utcnow),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Primary key and foreign keys
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id'], ),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id'], ),
    )


def downgrade():
    # Drop the TyreChecklist table if needed
    op.drop_table('tyre_checklist') 