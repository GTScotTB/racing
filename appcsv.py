from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from modelcsv import db, Entry
from configcsv import Config
import os
import csv
import io
import json

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

import csv
import io

@app.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        csv_file = request.files.get('csv_file')
        if not csv_file or csv_file.filename == '':
            flash("No file uploaded or selected.", "danger")
            return redirect(url_for('upload_csv'))

        # Read the CSV file
        try:
            stream = io.StringIO(csv_file.stream.read().decode("utf-8-sig"))
            csv_reader = csv.DictReader(stream)

            # Validate headers
            headers = csv_reader.fieldnames
            if not headers:
                flash("Invalid CSV file. No headers found.", "danger")
                return redirect(url_for('upload_csv'))

            # Pass headers and rows to the mapping page
            rows = list(csv_reader)
            return render_template('map_columns.html', headers=headers, rows=rows)

        except Exception as e:
            flash(f"Error processing CSV file: {e}", "danger")
            return redirect(url_for('upload_csv'))

    return render_template('upload.html')

def split_vehicle(vehicle_string):
    """Split vehicle string into make and model."""
    parts = vehicle_string.split(' ', 1)
    if len(parts) > 1:
        return parts[0], parts[1]
    return parts[0], ''

@app.route('/preview_data', methods=['POST'])
def preview_data():
    # Get mapped columns
    mappings = {key: request.form[key] for key in request.form if key != 'rows'}
    print("Mappings:", mappings)  # Debug print

    # Get rows from the hidden field
    rows = request.form.get('rows', '[]')
    try:
        rows = json.loads(rows)
    except json.JSONDecodeError as e:
        print("Error decoding rows JSON:", e)
        rows = []

    # Define valid classes and their mappings
    class_type_mapping = {
        'proam': 'Pro Am',
        'pro am': 'Pro Am',
        'flying500': 'Flying 500',
        'flying 500': 'Flying 500',
        'proopen': 'Pro Open',
        'pro open': 'Pro Open',
        'demonstration': 'Demo',
        'demo': 'Demo',
        'clubsprint': 'Clubsprint',
        'tuner': 'Tuner',
        'open': 'Open',
        'pro': 'Pro',
        'drift': 'Drift'
    }

    # Define valid classes list
    valid_classes = sorted(set(class_type_mapping.values()))

    class_type_suffix = {
        'clubsprint': 'C',
        'open': 'O',
        'pro': 'P',
        'tuner': 'T',
        'pro am': 'PA',
        'pro open': 'PO',
        'demo': 'D',
        'flying 500': 'F'
    }

    # Initialize default values for new fields
    for row in rows:
        # Store original vehicle value if it exists
        if mappings.get('vehicle') in row:
            print(f"Original vehicle value: {row[mappings['vehicle']]}")  # Debug print
            row['original_vehicle'] = row[mappings['vehicle']]
            
        # Get values from mapped columns with defaults
        vehicle_column = mappings.get('vehicle', '')
        if vehicle_column in row:
            make, model = split_vehicle(row[vehicle_column])
            row['vehicle_make'] = make
            row['vehicle_model'] = model
            print(f"Split vehicle: {make} | {model}")  # Debug print
        else:
            # If no vehicle column mapped, try individual make/model columns
            row['vehicle_make'] = row.get(mappings.get('vehicle_make', ''), '')
            row['vehicle_model'] = row.get(mappings.get('vehicle_model', ''), '')

        # Initialize class_type from mapping or set default
        class_type_column = mappings.get('class_type', '')
        row['class_type'] = row.get(class_type_column, '').lower() if class_type_column else ''
        row['vehicle_number'] = row.get(mappings.get('vehicle_number', ''), '')

    for row in rows:
        # Normalize class type
        original_class = row['class_type'].lower().strip()
        row['class_type'] = class_type_mapping.get(original_class, 'Default')
        
        # Mark excluded rows
        if original_class == 'drift' or row['vehicle_number'].lower() in ['null', '0', '']:
            row['exclude'] = 1
        else:
            row['exclude'] = 0

        # Add suffix to vehicle number based on normalized class
        if row['vehicle_number'] and row['class_type'].lower() in class_type_suffix:
            suffix = class_type_suffix[row['class_type'].lower()]
            if not row['vehicle_number'].endswith(suffix):
                row['vehicle_number'] = f"{row['vehicle_number']}{suffix}"

    return render_template('preview_data.html', 
                         mappings=mappings, 
                         rows=rows, 
                         valid_classes=valid_classes)


@app.route('/import_data', methods=['POST'])
def import_data():
    try:
        data = request.form.to_dict(flat=False)
        print("Submitted data:", data)  # Debug print
        
        # Get the number of rows from vehicle_number field
        num_rows = len(data.get('vehicle_number[]', []))
        print(f"Number of rows to process: {num_rows}")  # Debug print
        
        rows_to_import = []
        for i in range(num_rows):
            # Skip if row is marked as excluded
            exclude_key = f"exclude_{i}"
            if exclude_key in data and data[exclude_key][0] == '1':
                print(f"Skipping row {i} - marked as excluded")  # Debug print
                continue
            
            # Create row dictionary
            row = {}
            for field in ['vehicle_number', 'vehicle_make', 'vehicle_model', 
                         'driver_name', 'team_name', 'class_type', 
                         'log_book_number', 'licence_number', 'garage_number']:
                field_key = f"{field}[]"
                if field_key in data and i < len(data[field_key]):
                    value = data[field_key][i]
                    row[field] = '' if value.lower() == 'default' else value
                else:
                    row[field] = ''
            
            print(f"Processing row {i}:", row)  # Debug print
            rows_to_import.append(row)

        # Insert data into the database
        print(f"Attempting to import {len(rows_to_import)} rows")  # Debug print
        for row in rows_to_import:
            try:
                entry = Entry(
                    vehicle_number=row['vehicle_number'],
                    vehicle_make=row['vehicle_make'],
                    vehicle_model=row['vehicle_model'],
                    driver_name=row['driver_name'],
                    team_name=row['team_name'],
                    class_type=row['class_type'],
                    log_book_number=row['log_book_number'],
                    licence_number=row['licence_number'],
                    garage_number=row['garage_number']
                )
                db.session.add(entry)
                print(f"Added entry: {row['vehicle_number']}")  # Debug print
            except Exception as e:
                print(f"Error adding row {row['vehicle_number']}: {str(e)}")  # Debug print
                raise

        db.session.commit()
        print("Database commit successful")  # Debug print
        flash("Data imported successfully!", "success")
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error during import: {str(e)}")  # Debug print
        flash(f"Error importing data: {str(e)}", "danger")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)