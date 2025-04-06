from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

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
class FormulaFordCompetitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    team_association = db.Column(db.String(100))
    vehicle_make = db.Column(db.String(50), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    car_number = db.Column(db.Integer(), nullable=False, unique=True)
    # Relationships
    technical_checks = db.relationship('FormulaFordTechnicalCheck', backref='tech_check_competitor', lazy=True)
    event_entries = db.relationship('FormulaFordEventEntry', backref='event_entry_competitor', lazy=True)
    tyre_checks = db.relationship('FormulaFordTyreCheck', backref='tyre_check_competitor', lazy=True)
    
    def entry_for_event(self, event_id):
        """Find this competitor's entry for a specific event."""
        for entry in self.event_entries:
            if entry.event_id == event_id:
                return entry
        return None

class FormulaFordEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    # Relationships
    entries = db.relationship('FormulaFordEventEntry', foreign_keys='FormulaFordEventEntry.event_id', backref='event_rel', lazy=True)
    technical_checks = db.relationship('FormulaFordTechnicalCheck', foreign_keys='FormulaFordTechnicalCheck.event_id', backref='tech_check_event', lazy=True)
    tyre_checks = db.relationship('FormulaFordTyreCheck', foreign_keys='FormulaFordTyreCheck.event_id', backref='tyre_check_event', lazy=True)

class FormulaFordEventEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    entry_status = db.Column(db.String(20), nullable=False)  # confirmed, provisional, withdrawn, etc.
    weekend_car_number = db.Column(db.String(10), nullable=True)  # Weekend-specific car number that might differ from their regular number
    FFgarage_number = db.Column(db.String(10), nullable=True)  # Garage number for this event
    notes = db.Column(db.Text)

    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('ff_entries', lazy=True))
    competitor = db.relationship('FormulaFordCompetitor', backref=db.backref('competitor_entries', lazy=True))

    def __repr__(self):
        return f"<FormulaFordEventEntry for Event {self.event_id} and Competitor {self.competitor_id}>"

class FormulaFordTechnicalCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    
    # Technical check data
    weight = db.Column(db.Float)
    height_status = db.Column(db.String(10))
    fuel_status = db.Column(db.String(10))
    track_width_status = db.Column(db.String(10))
    tyre_check_status = db.Column(db.String(10))
    throttle_size_status = db.Column(db.String(10))
    ecu_number = db.Column(db.String(50))
    ecu_tune = db.Column(db.String(100))
    engine_number = db.Column(db.String(50))
    map_sensor_status = db.Column(db.String(10))
    air_temp_sensor_status = db.Column(db.String(10))
    lsd_status = db.Column(db.String(10))
    transponder_status = db.Column(db.String(10))
    dash_data_status = db.Column(db.String(10))
    first_gear_status = db.Column(db.String(10))
    flywheel_status = db.Column(db.String(10))
    # New custom "other" check
    other_check_name = db.Column(db.String(100))
    other_status = db.Column(db.String(10))
    check_date = db.Column(db.DateTime)
    checked_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Check-specific notes
    weight_notes = db.Column(db.Text)
    height_notes = db.Column(db.Text)
    fuel_notes = db.Column(db.Text)
    track_width_notes = db.Column(db.Text)
    tyre_check_notes = db.Column(db.Text)
    throttle_size_notes = db.Column(db.Text)
    ecu_notes = db.Column(db.Text)
    engine_notes = db.Column(db.Text)
    map_sensor_notes = db.Column(db.Text)
    air_temp_sensor_notes = db.Column(db.Text)
    lsd_notes = db.Column(db.Text)
    transponder_notes = db.Column(db.Text)
    dash_data_notes = db.Column(db.Text)
    first_gear_notes = db.Column(db.Text)
    flywheel_notes = db.Column(db.Text)
    other_notes = db.Column(db.Text)

    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('ff_technical_checks', lazy=True))

class FormulaFordTyreCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    
    # Tyre check data
    practice_tyre_brand = db.Column(db.String(100))
    practice_tyre_compound = db.Column(db.String(100))
    practice_tyre_serial_numbers = db.Column(db.Text)
    race_tyre_brand = db.Column(db.String(100))
    race_tyre_compound = db.Column(db.String(100))
    race_tyre_serial_numbers = db.Column(db.Text)
    notes = db.Column(db.Text)
    inspector_name = db.Column(db.String(100))
    check_date = db.Column(db.Date)
    
    # Add a field to indicate this is an event-wide check rather than competitor-specific
    is_event_wide = db.Column(db.Boolean, default=False)
    
    # For event-wide checks, these define the requirements that apply to all competitors
    allowed_practice_brands = db.Column(db.String(255))
    allowed_practice_compounds = db.Column(db.String(255))
    allowed_race_brands = db.Column(db.String(255))
    allowed_race_compounds = db.Column(db.String(255))
    max_sets_allowed = db.Column(db.Integer)

    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('ff_tyre_checks', lazy=True))

class TimetableSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    session_name = db.Column(db.String(100), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)  # practice, qualifying, race
    start_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    # Relationship
    formula_ford_event = db.relationship('FormulaFordEvent', backref='ff_timetable_sessions', lazy=True)

# New model for event technical requirements
class EventTechnicalRequirements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    min_weight_kg = db.Column(db.Float)
    height_requirement = db.Column(db.String(255))
    fuel_requirement = db.Column(db.String(255))
    safety_equipment_requirement = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Relationship
    formula_ford_event = db.relationship('FormulaFordEvent', backref='ff_technical_requirements', uselist=False)
    
    def __repr__(self):
        return f"<EventTechnicalRequirements for Event {self.event_id}>"

# New model for event tyre requirements
class EventTyreRequirements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    allowed_practice_brands = db.Column(db.String(255))
    allowed_practice_compounds = db.Column(db.String(255))
    allowed_race_brands = db.Column(db.String(255))
    allowed_race_compounds = db.Column(db.String(255))
    max_sets_allowed = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Relationship
    formula_ford_event = db.relationship('FormulaFordEvent', backref='ff_tyre_requirements', uselist=False)
    
    def __repr__(self):
        return f"<EventTyreRequirements for Event {self.event_id}>"

# New model for competitor check records that reference the event requirements
class CompetitorTechnicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('entries.id'), nullable=False)
    weight_kg = db.Column(db.Float)
    height_check_result = db.Column(db.String(10))  # Pass/Fail
    fuel_check_result = db.Column(db.String(10))    # Pass/Fail
    safety_equipment_result = db.Column(db.String(10))  # Pass/Fail
    inspector_name = db.Column(db.String(100))
    check_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    
    # Relationships
    formula_ford_event = db.relationship('FormulaFordEvent', backref='ff_competitor_technical_records')
    competitor = db.relationship('FormulaFordCompetitor', backref='technical_records')
    
    def __repr__(self):
        return f"<CompetitorTechnicalRecord {self.id} for {self.competitor_id} at Event {self.event_id}>"

# New model for competitor tyre records
class CompetitorTyreRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    practice_tyre_brand = db.Column(db.String(100))
    practice_tyre_compound = db.Column(db.String(100))
    practice_tyre_serial_numbers = db.Column(db.Text)
    race_tyre_brand = db.Column(db.String(100))
    race_tyre_compound = db.Column(db.String(100))
    race_tyre_serial_numbers = db.Column(db.Text)
    inspector_name = db.Column(db.String(100))
    check_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    
    # Relationships
    formula_ford_event = db.relationship('FormulaFordEvent', backref='ff_competitor_tyre_records')
    competitor = db.relationship('FormulaFordCompetitor', backref='tyre_records')
    
    def __repr__(self):
        return f"<CompetitorTyreRecord {self.id} for {self.competitor_id} at Event {self.event_id}>"

# New models for the Formula Ford competition

class CompetitorWeightHeight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    qual_weight = db.Column(db.Float, nullable=True)
    qual_height = db.Column(db.String(10), nullable=True)
    r1_weight = db.Column(db.Float, nullable=True)
    r1_height = db.Column(db.String(10), nullable=True)
    r2_weight = db.Column(db.Float, nullable=True)
    r2_height = db.Column(db.String(10), nullable=True)
    r3_weight = db.Column(db.Float, nullable=True)
    r3_height = db.Column(db.String(10), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('ff_weight_height_records', lazy=True))
    competitor = db.relationship('FormulaFordCompetitor', backref=db.backref('weight_height_records', lazy=True))

class CompetitorECU(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    ecu_number = db.Column(db.String(50), nullable=True)
    inspector_name = db.Column(db.String(100), nullable=True)
    check_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('ff_ecu_records', lazy=True))
    competitor = db.relationship('FormulaFordCompetitor', backref=db.backref('ecu_records', lazy=True))

class CompetitorEngine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    engine_number = db.Column(db.String(50), nullable=True)
    inspector_name = db.Column(db.String(100), nullable=True)
    check_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('ff_engine_records', lazy=True))
    competitor = db.relationship('FormulaFordCompetitor', backref=db.backref('engine_records', lazy=True))

class TechnicalCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    check_type = db.Column(db.String(50), nullable=True)
    result = db.Column(db.String(255), nullable=True)
    inspector_name = db.Column(db.String(100), nullable=True)
    check_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('ff_technical_check_records', lazy=True))
    competitor = db.relationship('FormulaFordCompetitor', backref=db.backref('technical_check_records', lazy=True))

class TyreChecklist(db.Model):
    __tablename__ = 'tyre_checklist'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('formula_ford_event.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('formula_ford_competitor.id'), nullable=False)
    
    # Columns for marking tyres
    tyres_marked_practice = db.Column(db.Boolean, default=False)  # TMP
    tyres_marked_qualifying = db.Column(db.Boolean, default=False)  # TMR
    
    # Columns for practice sessions
    practice1_checked = db.Column(db.Boolean, default=False)  # P1
    practice2_checked = db.Column(db.Boolean, default=False)  # P2
    practice3_checked = db.Column(db.Boolean, default=False)  # P3
    practice4_checked = db.Column(db.Boolean, default=False)  # P4
    
    # Qualifying and races
    qualifying_checked = db.Column(db.Boolean, default=False)  # Q
    race1_checked = db.Column(db.Boolean, default=False)  # R1
    race2_checked = db.Column(db.Boolean, default=False)  # R2
    race3_checked = db.Column(db.Boolean, default=False)  # R3
    
    # Additional information
    inspector_name = db.Column(db.String(100), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    formula_ford_event = db.relationship('FormulaFordEvent', backref=db.backref('tyre_checklists', lazy=True))
    competitor = db.relationship('FormulaFordCompetitor', backref=db.backref('tyre_checklists', lazy=True))
    
    def __repr__(self):
        return f"<TyreChecklist for Competitor {self.competitor_id} at Event {self.event_id}>"
