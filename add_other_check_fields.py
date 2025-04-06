from app import app, db
from sqlalchemy import text

# This script will add the new 'other' check fields to FormulaFordTechnicalCheck
# and add weekend_car_number to FormulaFordEventEntry
def add_new_fields():
    with app.app_context():
        conn = db.engine.connect()
        
        # Add fields to FormulaFordTechnicalCheck
        check_fields = [
            'other_check_name', 
            'other_status',
            'other_notes'
        ]
        
        for column in check_fields:
            try:
                # Check if column exists
                conn.execute(text(f"SELECT {column} FROM formula_ford_technical_check LIMIT 1"))
                print(f"Column {column} already exists in formula_ford_technical_check")
            except Exception:
                # Add column if it doesn't exist
                conn.execute(text(f"ALTER TABLE formula_ford_technical_check ADD COLUMN {column} TEXT"))
                print(f"Added column {column} to formula_ford_technical_check")
        
        # Add weekend_car_number to FormulaFordEventEntry
        try:
            # Check if column exists
            conn.execute(text("SELECT weekend_car_number FROM formula_ford_event_entry LIMIT 1"))
            print("Column weekend_car_number already exists in formula_ford_event_entry")
        except Exception:
            # Add column if it doesn't exist
            conn.execute(text("ALTER TABLE formula_ford_event_entry ADD COLUMN weekend_car_number TEXT"))
            print("Added column weekend_car_number to formula_ford_event_entry")
                
        conn.close()
        print("Migration completed!")

if __name__ == "__main__":
    add_new_fields() 