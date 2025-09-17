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

# Formula Ford Models

class FormulaFordEvent(db.Model):
    __tablename__ = 'formula_ford_event'
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False, unique=True)
    location = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    
    # Relationships
    entries = db.relationship('FormulaFordEventEntry', back_populates='event', cascade="all, delete-orphan")
    technical_checks = db.relationship('TechnicalCheck', back_populates='event', cascade="all, delete-orphan")
    tyre_checklists = db.relationship('TyreChecklist', back_populates='event', cascade="all, delete-orphan")
    weight_height_records = db.relationship('CompetitorWeightHeight', back_populates='event', cascade="all, delete-orphan")

class FormulaFordCompetitor(db.Model):
    __tablename__ = 'formula_ford_competitor'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    team_association = db.Column(db.String(255))
    vehicle_make = db.Column(db.String(100), nullable=False)
    vehicle_type = db.Column(db.String(100), nullable=False)
    car_number = db.Column(db.Integer, nullable=False, unique=True)
    
    # Relationships
    event_entries = db.relationship('FormulaFordEventEntry', back_populates='competitor', cascade="all, delete-orphan")
    technical_checks = db.relationship('TechnicalCheck', back_populates='competitor', cascade="all, delete-orphan")
    tyre_checklists = db.relationship('TyreChecklist', back_populates='competitor', cascade="all, delete-orphan")
    weight_height_records = db.relationship('CompetitorWeightHeight', back_populates='competitor', cascade="all, delete-orphan")

class FormulaFordEventEntry(db.Model):
    __tablename__ = 'formula_ford_event_entry'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    entry_status = db.Column(db.String(50), nullable=False, default='Confirmed')
    weekend_car_number = db.Column(db.String(10))
    FFgarage_number = db.Column(db.String(10))
    notes = db.Column(db.Text)
    
    # Relationships
    event = db.relationship('FormulaFordEvent', back_populates='entries')
    competitor = db.relationship('FormulaFordCompetitor', back_populates='event_entries')

class TechnicalCheck(db.Model):
    __tablename__ = 'formula_ford_technical_check'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    check_type = db.Column(db.String(50), nullable=False)
    result = db.Column(db.String(255))
    notes = db.Column(db.Text)
    inspector_name = db.Column(db.String(100))
    check_date = db.Column(db.Date)
    
    # Relationships
    event = db.relationship('FormulaFordEvent', back_populates='technical_checks')
    competitor = db.relationship('FormulaFordCompetitor', back_populates='technical_checks')

class TyreChecklist(db.Model):
    __tablename__ = 'tyre_checklist'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    tyres_marked_practice = db.Column(db.Boolean, default=False)
    tyres_marked_qualifying = db.Column(db.Boolean, default=False)
    practice1_checked = db.Column(db.Boolean, default=False)
    practice2_checked = db.Column(db.Boolean, default=False)
    practice3_checked = db.Column(db.Boolean, default=False)
    practice4_checked = db.Column(db.Boolean, default=False)
    qualifying_checked = db.Column(db.Boolean, default=False)
    race1_checked = db.Column(db.Boolean, default=False)
    race2_checked = db.Column(db.Boolean, default=False)
    race3_checked = db.Column(db.Boolean, default=False)
    inspector_name = db.Column(db.String(100))
    last_updated = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    event = db.relationship('FormulaFordEvent', back_populates='tyre_checklists')
    competitor = db.relationship('FormulaFordCompetitor', back_populates='tyre_checklists')

class CompetitorWeightHeight(db.Model):
    __tablename__ = 'competitor_weight_height'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    qual_weight = db.Column(db.Float)
    qual_height = db.Column(db.String(50))
    r1_weight = db.Column(db.Float)
    r1_height = db.Column(db.String(50))
    r2_weight = db.Column(db.Float)
    r2_height = db.Column(db.String(50))
    r3_weight = db.Column(db.Float)
    r3_height = db.Column(db.String(50))
    
    # Relationships
    event = db.relationship('FormulaFordEvent', back_populates='weight_height_records')
    competitor = db.relationship('FormulaFordCompetitor', back_populates='weight_height_records')

# The following models are not used in app.py but are in the import list.
# I'm adding them to prevent future import errors.

class FormulaFordTechnicalCheck(db.Model): # Likely replaced by TechnicalCheck
    __tablename__ = 'formula_ford_technical_check_old'
    id = db.Column(db.Integer, primary_key=True)

class FormulaFordTyreCheck(db.Model): # Likely replaced by TyreChecklist
    __tablename__ = 'formula_ford_tyre_check_old'
    id = db.Column(db.Integer, primary_key=True)

class TimetableSession(db.Model):
    __tablename__ = 'timetable_session'
    id = db.Column(db.Integer, primary_key=True)

class EventTechnicalRequirements(db.Model):
    __tablename__ = 'event_technical_requirements'
    id = db.Column(db.Integer, primary_key=True)

class CompetitorTechnicalRecord(db.Model):
    __tablename__ = 'competitor_technical_record'
    id = db.Column(db.Integer, primary_key=True)

class EventTyreRequirements(db.Model):
    __tablename__ = 'event_tyre_requirements'
    id = db.Column(db.Integer, primary_key=True)

class CompetitorTyreRecord(db.Model):
    __tablename__ = 'competitor_tyre_record'
    id = db.Column(db.Integer, primary_key=True)

class CompetitorECU(db.Model):
    __tablename__ = 'competitor_ecu'
    id = db.Column(db.Integer, primary_key=True)

class CompetitorEngine(db.Model):
    __tablename__ = 'competitor_engine'
    id = db.Column(db.Integer, primary_key=True)
