import json
from datetime import date, datetime
from app import app, db
from models import (
    User, FormulaFordEvent, FormulaFordCompetitor, FormulaFordEventEntry,
    TechnicalCheck, TyreChecklist, CompetitorWeightHeight,
    Entry, InspectionChecklist, InspectionItem, Officials, Roles
)
from werkzeug.security import generate_password_hash

def parse_date(iso_date):
    """Converts ISO date string to a date object, returns None if invalid."""
    if not iso_date:
        return None
    try:
        return date.fromisoformat(iso_date)
    except (TypeError, ValueError):
        return None

def parse_datetime(iso_datetime):
    """Converts ISO datetime string to a datetime object, returns None if invalid."""
    if not iso_datetime:
        return None
    try:
        return datetime.fromisoformat(iso_datetime)
    except (TypeError, ValueError):
        return None

def restore_data():
    """Imports data from JSON files into the database."""
    with app.app_context():
        # The order is important to respect foreign key constraints
        # (e.g., import users and events before entries)
        models_to_restore = [
            ('roles', Roles),
            ('users', User),
            ('formula_ford_events', FormulaFordEvent),
            ('formula_ford_competitors', FormulaFordCompetitor),
            ('formula_ford_event_entries', FormulaFordEventEntry),
            ('technical_checks', TechnicalCheck),
            ('tyre_checklists', TyreChecklist),
            ('competitor_weight_heights', CompetitorWeightHeight),
            ('wtac_entries', Entry),
            ('wtac_checklists', InspectionChecklist),
            ('wtac_items', InspectionItem),
            ('officials', Officials),
        ]

        for filename, model in models_to_restore:
            try:
                print(f"Restoring data for {model.__tablename__}...")
                with open(f'{filename}_backup.json', 'r') as f:
                    data = json.load(f)

                for record_data in data:
                    # Handle date/datetime fields
                    for key, value in record_data.items():
                        if 'date' in key and isinstance(value, str):
                            record_data[key] = parse_date(value)
                        if 'updated' in key and isinstance(value, str):
                            record_data[key] = parse_datetime(value)
                    
                    # Special handling for user passwords (re-hash them)
                    if model == User and 'password' in record_data:
                        # This assumes you don't store plain text passwords in backups.
                        # If you do, you should hash them on restore.
                        # For this example, we'll skip re-inserting if the user exists.
                        if not User.query.filter_by(username=record_data['username']).first():
                             db.session.add(User(**record_data))
                        continue

                    db.session.add(model(**record_data))
                db.session.commit()
                print(f" -> Successfully restored {len(data)} records.")
            except FileNotFoundError:
                print(f" -> Backup file {filename}_backup.json not found. Skipping.")
            except Exception as e:
                print(f" -> Error restoring {model.__tablename__}: {e}")
                db.session.rollback()

if __name__ == '__main__':
    print("Starting database restore...")
    restore_data()
    print("\nRestore complete.")