#!/usr/bin/env python
import sqlite3
import os

# Path to the database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'DataBase', 'racing.db')

print(f"Using database at: {db_path}")

def add_garage_number_column():
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(formula_ford_event_entry)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'FFgarage_number' in column_names:
            print("FFgarage_number column already exists in formula_ford_event_entry table.")
        else:
            # Add the FFgarage_number column
            cursor.execute("ALTER TABLE formula_ford_event_entry ADD COLUMN FFgarage_number VARCHAR(10);")
            conn.commit()
            print("FFgarage_number column added successfully to formula_ford_event_entry table.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    add_garage_number_column() 