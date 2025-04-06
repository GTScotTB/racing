from app import app, db
from sqlalchemy import text

# This script will add the notes columns to the FormulaFordTechnicalCheck table
def add_notes_columns():
    with app.app_context():
        conn = db.engine.connect()
        
        # Add each notes column
        notes_columns = [
            'weight_notes', 'height_notes', 'fuel_notes', 'track_width_notes', 
            'tyre_check_notes', 'throttle_size_notes', 'ecu_notes', 'engine_notes',
            'map_sensor_notes', 'air_temp_sensor_notes', 'lsd_notes', 'transponder_notes',
            'dash_data_notes', 'first_gear_notes', 'flywheel_notes'
        ]
        
        for column in notes_columns:
            try:
                # Check if column exists
                conn.execute(text(f"SELECT {column} FROM formula_ford_technical_check LIMIT 1"))
                print(f"Column {column} already exists")
            except Exception as e:
                try:
                    # Add column if it doesn't exist
                    conn.execute(text(f"ALTER TABLE formula_ford_technical_check ADD COLUMN {column} TEXT"))
                    conn.commit()
                    print(f"Added column {column}")
                except Exception as e:
                    print(f"Error adding column {column}: {str(e)}")
                
        conn.close()
        print("Migration completed!")

if __name__ == "__main__":
    add_notes_columns() 