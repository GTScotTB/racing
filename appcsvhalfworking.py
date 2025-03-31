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

@app.route('/map_columns', methods=['POST'])
def map_columns():
    headers = request.form.getlist('headers')
    rows = request.form.getlist('rows')

    # Render the mapping page
    return render_template('map_columns.html', headers=headers, rows=rows)

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

    # Normalize class_type values
    valid_classes = ['tuner', 'clubsprint', 'open', 'pro open', 'pro am', 'pro', 'flying 500', 'demo', 'default']
    for row in rows:
        class_type = row.get(mappings.get('class_type', ''), '').lower()
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

    # Render the preview page
    return render_template('preview_data.html', mappings=mappings, rows=rows, valid_classes=valid_classes)
    # Render the preview page
    return render_template('preview_data.html', mappings=mappings, rows=rows)

@app.route('/import_data', methods=['POST'])
def import_data():
    # Get data from the form
    data = request.form.to_dict(flat=False)

    # Insert data into the database
    for i in range(len(data['vehicle_number'])):
        entry = Entry(
            vehicle_number=data['vehicle_number'][i],
            vehicle_make=data['vehicle_make'][i],
            driver_name=data['driver_name'][i],
            class_type=data['class_type'][i]
        )
        db.session.add(entry)

    db.session.commit()
    flash("Data imported successfully!", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)