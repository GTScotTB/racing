#!/usr/bin/env python
import sqlite3
import os

# Path to the database file - try both possible locations
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'racing.db')
db_path_alt = os.path.join(BASE_DIR, 'DataBase', 'racing.db')

# SQL to create the TyreChecklist table
create_table_sql = '''
CREATE TABLE IF NOT EXISTS tyre_checklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    competitor_id INTEGER NOT NULL,
    tyres_marked_practice BOOLEAN DEFAULT 0,
    tyres_marked_qualifying BOOLEAN DEFAULT 0,
    practice1_checked BOOLEAN DEFAULT 0,
    practice2_checked BOOLEAN DEFAULT 0,
    practice3_checked BOOLEAN DEFAULT 0,
    practice4_checked BOOLEAN DEFAULT 0,
    qualifying_checked BOOLEAN DEFAULT 0,
    race1_checked BOOLEAN DEFAULT 0,
    race2_checked BOOLEAN DEFAULT 0,
    race3_checked BOOLEAN DEFAULT 0,
    inspector_name VARCHAR(100),
    last_updated DATETIME,
    notes TEXT,
    FOREIGN KEY (event_id) REFERENCES formula_ford_event (id),
    FOREIGN KEY (competitor_id) REFERENCES formula_ford_competitor (id)
);
'''

def create_table(db_file):
    """Create the tyre_checklist table in the specified database"""
    if not os.path.exists(db_file):
        print(f"Database file not found: {db_file}")
        return False
        
    print(f"Attempting to create tyre_checklist table in: {db_file}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tyre_checklist';")
        if cursor.fetchone():
            print(f"TyreChecklist table already exists in {db_file}.")
        else:
            # Create the table
            cursor.execute(create_table_sql)
            conn.commit()
            print(f"TyreChecklist table created successfully in {db_file}!")
            
        # Verify table structure
        cursor.execute("PRAGMA table_info(tyre_checklist);")
        columns = cursor.fetchall()
        print(f"Table structure in {db_file}:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Try to create the table in both possible database locations
    success = create_table(db_path)
    if not success:
        success = create_table(db_path_alt)
        
    if not success:
        print("Failed to create the tyre_checklist table in any database file.")
    else:
        print("Database update completed successfully.") 