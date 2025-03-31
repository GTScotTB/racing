from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, default=1)
    vehicle_number = db.Column(db.String(5), nullable=False, unique=True)
    vehicle_make = db.Column(db.String(255), nullable=False)
    vehicle_model = db.Column(db.String(255), nullable=False, default='UNK')
    vehicle_type = db.Column(db.String(2), nullable=False, default='W')
    garage_number = db.Column(db.String(255), nullable=True)
    log_book_number = db.Column(db.String(255), nullable=True)
    licence_number = db.Column(db.String(255), nullable=False, default='000000')
    driver_name = db.Column(db.String(255), nullable=False)
    team_name = db.Column(db.String(255), nullable=True)
    class_type = db.Column(db.String(255), nullable=True)
    inspection_report = db.Column(db.Integer, nullable=False, default=0)
    approved_to_start = db.Column(db.Integer, nullable=False, default=0)
    failed_items = db.Column(db.Integer, nullable=False, default=0)