#!/usr/bin/env python
from app import db
import sqlalchemy as sa
from models import TyreChecklist
from datetime import datetime

# Script to apply the TyreChecklist table migration directly
# This is an alternative to running the Alembic migration if that has issues

def create_tyre_checklist_table():
    # Check if table already exists
    inspector = sa.inspect(db.engine)
    if 'tyre_checklist' in inspector.get_table_names():
        print("TyreChecklist table already exists.")
        return

    print("Creating TyreChecklist table...")
    
    # Create the table directly using SQLAlchemy's create_all with just our model
    metadata = sa.MetaData()
    tyre_checklist = sa.Table(
        'tyre_checklist',
        metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
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
        sa.Column('last_updated', sa.DateTime(), default=datetime.utcnow),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['event_id'], ['formula_ford_event.id']),
        sa.ForeignKeyConstraint(['competitor_id'], ['formula_ford_competitor.id']),
    )
    
    metadata.create_all(db.engine, tables=[tyre_checklist])
    print("TyreChecklist table created successfully!")

if __name__ == '__main__':
    create_tyre_checklist_table() 