import json
from datetime import date, datetime
from app import app, db
from models import (
    User, FormulaFordEvent, FormulaFordCompetitor, FormulaFordEventEntry, Officials, Roles,
    TechnicalCheck, TyreChecklist, CompetitorWeightHeight
)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def backup_data():
    """Exports data from specified tables into JSON files."""
    with app.app_context():
        models_to_backup = {
            'users': User,
            'formula_ford_events': FormulaFordEvent,
            'formula_ford_competitors': FormulaFordCompetitor,
            'formula_ford_event_entries': FormulaFordEventEntry,
            'officials': Officials,
            'roles': Roles,
            'technical_checks': TechnicalCheck,
            'tyre_checklists': TyreChecklist,
            'competitor_weight_heights': CompetitorWeightHeight
        }

        for filename, model in models_to_backup.items():
            try:
                print(f"Backing up {model.__tablename__}...")
                # Query all data from the table
                records = model.query.all()
                
                # Convert records to a list of dictionaries
                data = []
                for record in records:
                    record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}
                    data.append(record_dict)
                
                # Write to a JSON file
                with open(f'{filename}_backup.json', 'w') as f:
                    json.dump(data, f, indent=4, default=json_serial)
                
                print(f" -> Successfully backed up {len(data)} records to {filename}_backup.json")

            except Exception as e:
                print(f" -> Error backing up {model.__tablename__}: {e}")

if __name__ == '__main__':
    print("Starting database backup...")
    backup_data()
    print("\nBackup complete. JSON files have been created in your project directory.")