from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# User Models for Auth
class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Matches your SQLite table name

    id = db.Column(db.Integer, primary_key=True)  # Unique user ID
    username = db.Column(db.String(80), unique=True, nullable=False)  # Unique username
    password = db.Column(db.String(120), nullable=False)  # Hashed password
    role = db.Column(db.String(20), nullable=False)  # Role (e.g., admin, user)

    def __repr__(self):
        return f"<User {self.username}>"


# Entry Model (Existing)
class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each entry
    vehicle_number = db.Column(db.String(5), nullable=False)
    vehicle_make = db.Column(db.String(255), nullable=False)
    vehicle_model = db.Column(db.String(255), nullable=False)
    vehicle_type = db.Column(db.String(2), nullable=False, default='W')
    garage_number = db.Column(db.String(255), nullable=True)
    log_book_number = db.Column(db.String(255), nullable=True)
    licence_number = db.Column(db.String(255), nullable=False, default='000000')
    driver_name = db.Column(db.String(255), nullable=False)
    team_name = db.Column(db.String(255), nullable=True)
    class_type = db.Column(db.String(255), nullable=True)  # Renamed from 'class'
    Inspection_report = db.Column(db.Boolean, nullable=False, default=False)
    approved_to_start = db.Column(db.Boolean, nullable=False, default=False)
    failed_items = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    inspection_checklist = db.relationship('InspectionChecklist', backref='entry', lazy=True)

# Inspection Checklist Model
class InspectionChecklist(db.Model):
    __tablename__ = 'inspection_checklists'

    id = db.Column(db.Integer, primary_key=True)  # Unique ID for the checklist
    entry_id = db.Column(db.Integer, db.ForeignKey('entries.id'), nullable=False)  # Links to the 'entries' table
    approved_to_start = db.Column(db.Boolean, default=False)
    scrutineer_name = db.Column(db.String(255), nullable=True)  # Add this column
    scrutineer_licence_number = db.Column(db.String(255), nullable=True)  # Add this column
    date = db.Column(db.Date, nullable=True)  # Add this column if not already present
    time = db.Column(db.Time, nullable=True)  # Add this column if not already present

    # Relationships
    items = db.relationship('InspectionItem', backref='checklist', lazy=True)

# Inspection Item Model
class InspectionItem(db.Model):
    __tablename__ = 'inspection_items'

    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('inspection_checklists.id'), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')
    brand = db.Column(db.String(255), nullable=True)
    standard = db.Column(db.String(255), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    rops = db.Column(db.String(255), nullable=True)
    brand_required = db.Column(db.Boolean, default=False)
    standard_required = db.Column(db.Boolean, default=False)
    expiry_date_required = db.Column(db.Boolean, default=False)
    rops_required = db.Column(db.Boolean, default=False)
    value = db.Column(db.String(255), nullable=True)

# Checklist Item Model
class ChecklistItem(db.Model):
    __tablename__ = 'checklist_items'

    id = db.Column(db.Integer, primary_key=True)  # Unique ID for the checklist item
    item_name = db.Column(db.String(255), nullable=False)  # Name of the inspection item
    applicable_to_tuner = db.Column(db.Boolean, default=False)
    applicable_to_clubsprint = db.Column(db.Boolean, default=False)
    applicable_to_open = db.Column(db.Boolean, default=False)
    applicable_to_pro_open = db.Column(db.Boolean, default=False)
    applicable_to_pro_am = db.Column(db.Boolean, default=False)
    applicable_to_pro = db.Column(db.Boolean, default=False)
    applicable_to_flying_500 = db.Column(db.Boolean, default=False)
    applicable_to_demo = db.Column(db.Boolean, default=False)
    brand_required = db.Column(db.Boolean, default=False)
    standard_required = db.Column(db.Boolean, default=False)
    expiry_date_required = db.Column(db.Boolean, default=False)
    rops_required = db.Column(db.Boolean, default=False)
# Officials Model
class Officials(db.Model):
    __tablename__ = 'officials'  # Make sure this matches your database table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    contact_info = db.Column(db.String(200), nullable=True)
    licence_number = db.Column(db.String(25), nullable=True)
   
# Roles Model
class Roles(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(100), nullable=False, unique=True)
