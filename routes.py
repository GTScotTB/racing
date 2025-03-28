# config.py
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:21112@localhost/racing'
SQLALCHEMY_TRACK_MODIFICATIONS = False
# routes.py
from flask import Flask, jsonify, request
from models import db, Entry

app = Flask(__name__)

# Get total number of entries with vehicle_type = 'W'
@app.route('/total_entries', methods=['GET'])
def total_entries():
    total = Entry.query.filter_by(vehicle_type='W').count()
    return jsonify({'total_entries': total})

# Get total entries per class
@app.route('/class_entries', methods=['GET'])
def class_entries():
    entries = db.session.query(Entry.class_type, db.func.count(Entry.class_type))\
                        .filter_by(vehicle_type='W')\
                        .group_by(Entry.class_type)\
                        .all()
    return jsonify({'class_entries': [{row[0]: row[1]} for row in entries]})

# Add a new entry
@app.route('/add_entry', methods=['POST'])
def add_entry():
    data = request.json  # Expect JSON payload
    new_entry = Entry(
        Team_Name=data['Team_Name'],
        Driver_Name=data['Driver_Name'],
        Vehicle_make=data['Vehicle_make'],
        Vehicle_model=data['Vehicle_model'],
        garage_number=data['garage_number'],
        vehicle_number=data['vehicle_number'],
        class_type=data['class'],
        vehicle_type='W'  # All entries have vehicle_type = 'W'
    )
    db.session.add(new_entry)
    db.session.commit()
    return jsonify({'message': 'Entry added successfully!'})

# Get entries without inspection reports
@app.route('/missing_inspections', methods=['GET'])
def missing_inspections():
    entries = Entry.query.filter(Entry.inspection_report.is_(None)).all()
    return jsonify({'missing_inspections': [entry.id for entry in entries]})

# Get entries not approved to start
@app.route('/not_approved_to_start', methods=['GET'])
def not_approved_to_start():
    entries = Entry.query.filter_by(approved_to_start='N').all()
    return jsonify({'not_approved_to_start': [entry.id for entry in entries]})

# List entries by weight (if weight is part of the schema)
@app.route('/vehicles_by_weight', methods=['GET'])
def vehicles_by_weight():
    entries = Entry.query.filter(Entry.vehicle_weight.isnot(None)).all()
    return jsonify({'vehicles_by_weight': [{'driver': entry.Driver_Name, 'weight': entry.vehicle_weight} for entry in entries]})