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

@app.route('/preview_data', methods=['POST'])
def preview_data():
    # Get mapped columns
    mappings = {key: request.form[key] for key in request.form if key != 'rows'}
    print("Mappings:", mappings)  # Debugging

    # Get rows from the hidden field
    rows = request.form.get('rows', '[]')
    print("Raw Rows:", rows)  # Debugging

    try:
        rows = json.loads(rows)
        print("Parsed Rows:", rows[:5])  # Debugging (print first 5 rows)
    except json.JSONDecodeError as e:
        print("Error decoding rows JSON:", e)
        rows = []

    # Normalize class_type values and mark "drift" rows as excluded
    valid_classes = ['tuner', 'clubsprint', 'open', 'pro open', 'pro am', 'pro', 'flying 500', 'demo', 'default']
    class_type_suffix = {
        'clubsprint': 'C',
        'open': 'O',
        'pro': 'P',
        'tuner': 'T',
        'pro am': 'PA',
        'pro open': 'PO',
        'demo': 'D',
        'flying 500': 'F',
        'default': ''  # No suffix for default
    }

    for index, row in enumerate(rows):
        # Debugging: Print the row and check if 'vehicle_number' exists
        print(f"Processing row {index}: {row}")
        if mappings.get('vehicle_number', '') not in row:
            print(f"Row {index} is missing 'vehicle_number': {row}")
            row['vehicle_number'] = ''  # Set a default value to avoid KeyError

        # Get the original class_type value
        class_type = row.get(mappings.get('class_type', ''), '').lower()
        vehicle_number = row.get(mappings.get('vehicle_number', ''), '').lower()

        # Mark rows with "drift" as excluded by default
        if class_type == 'drift':
            row['exclude'] = 1  # Mark as excluded
        elif vehicle_number == 'null':
            row['exclude'] = 1
        elif vehicle_number == '0':
            row['exclude'] = 1
        else:
            row['exclude'] = 0  # Not excluded by default

        # Normalize class_type values
        if class_type == 'proam':
            row['class_type'] = 'Pro Am'
        elif class_type == 'flying500':
            row['class_type'] = 'Flying 500'
        elif class_type == 'proopen':
            row['class_type'] = 'Pro Open'
        elif class_type == 'demonstration':
            row['class_type'] = 'Demo'
        elif class_type not in valid_classes:
            row['class_type'] = 'Default'

        # Append class_type suffix to vehicle_number
        normalized_class_type = row.get('class_type', 'default').lower()
        suffix = class_type_suffix.get(normalized_class_type, '')
        if suffix:
            row['vehicle_number'] = f"{row['vehicle_number']}{suffix}"

    # Render the preview page
    return render_template('preview_data.html', mappings=mappings, rows=rows, valid_classes=valid_classes)


@app.route('/import_data', methods=['POST'])
def import_data():
    # Get data from the form
    data = request.form.to_dict(flat=False)

    # Debugging: Print submitted data
    print("Submitted data:", data)

    # Filter out rows marked as excluded
    rows_to_import = []
    vehicle_numbers = data.get('vehicle_number', [])
    for i in range(len(vehicle_numbers)):
        exclude_key = f"exclude_{i}"
        if exclude_key in data and data[exclude_key][0] == '1':
            continue  # Skip this row if the exclude checkbox is checked

        # Add the row to the list of rows to import, replacing 'default' with ''
        rows_to_import.append({
            'vehicle_number': vehicle_numbers[i] if vehicle_numbers[i] != 'default' else '',
            'vehicle_make': data.get('vehicle_make', [])[i] if data.get('vehicle_make', [])[i] != 'default' else '',
            'vehicle_model': data.get('vehicle_model', [])[i] if data.get('vehicle_model', [])[i] != 'default' else '',
            'driver_name': data.get('driver_name', [])[i] if data.get('driver_name', [])[i] != 'default' else '',
            'team_name': data.get('team_name', [])[i] if data.get('team_name', [])[i] != 'default' else '',
            'class_type': data.get('class_type', [])[i] if data.get('class_type', [])[i] != 'default' else '',
            'log_book_number': data.get('log_book_number', [])[i] if data.get('log_book_number', [])[i] != 'default' else '',
            'licence_number': data.get('licence_number', [])[i] if data.get('licence_number', [])[i] != 'default' else '',
            'garage_number': data.get('garage_number', [])[i] if data.get('garage_number', [])[i] != 'default' else '',
        })

    # Insert data into the database
    for row in rows_to_import:
        entry = Entry(
            vehicle_number=row['vehicle_number'],
            vehicle_make=row['vehicle_make'],
            vehicle_model=row['vehicle_model'],  # Include vehicle_model
            driver_name=row['driver_name'],
            team_name=row['team_name'],  # Include team_name
            class_type=row['class_type'],
            log_book_number=row['log_book_number'],
            licence_number=row['licence_number'],
            garage_number=row['garage_number']
        )
        db.session.add(entry)

    db.session.commit()
    flash("Data imported successfully!", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)