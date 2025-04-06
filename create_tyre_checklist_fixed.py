#!/usr/bin/env python
import sqlite3
import os

# Path to the correct database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'DataBase', 'racing.db')

print(f"Targeting database at: {db_path}")

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

def main():
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tyre_checklist';")
        if cursor.fetchone():
            print("TyreChecklist table already exists.")
        else:
            # Create the table
            cursor.execute(create_table_sql)
            conn.commit()
            print("TyreChecklist table created successfully!")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main() 