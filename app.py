from flask import Flask, render_template, jsonify, request, flash, redirect, url_for, session
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from models import db,User, Entry, InspectionChecklist, InspectionItem, ChecklistItem, Officials, Roles, FormulaFordEvent, FormulaFordEventEntry, FormulaFordTechnicalCheck, FormulaFordTyreCheck, TimetableSession, FormulaFordCompetitor, EventTechnicalRequirements, CompetitorTechnicalRecord, EventTyreRequirements, CompetitorTyreRecord, CompetitorWeightHeight, CompetitorECU, CompetitorEngine, TechnicalCheck, TyreChecklist
from sqlalchemy import or_, func, Integer, text, case, desc
from flask_migrate import Migrate
import os
from datetime import datetime, timezone, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from auth import check_password, hash_password
import csv
import io
import json
# Reimport Flask-WTF CSRF protection
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf, CSRFError
import traceback
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
import re
import uuid
import argparse

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'yoursecretkey'  # Replace with a real secret key
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# Additional security configurations for session handling
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Session timeout
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # Increase CSRF token timeout to 1 hour
app.config['WTF_CSRF_SSL_STRICT'] = False  # Less strict CSRF checks for development

# Make sessions last longer
@app.before_request
def make_session_permanent():
    session.permanent = True  # Use the PERMANENT_SESSION_LIFETIME value

# Enable CSRF protection
# This ensures all POST, PUT, PATCH, and DELETE requests require a valid CSRF token
csrf = CSRFProtect(app)

# CSRF Error Handler - Register this immediately after creating csrf
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    print(f"CSRF ERROR: {str(e)}")
    print(f"Current session: {session}")
    print(f"Request cookies: {request.cookies}")
    flash("CSRF token validation failed. Please try again.", "danger")
    return redirect(url_for('login'))

# Make CSRF token available in all templates
# This function adds csrf_token to the context of all templates
@app.context_processor
def inject_csrf_token():
    token = generate_csrf()
    # Add debugging for token generation
    print(f"Generated CSRF token: {token}")
    return dict(csrf_token=token)

# Make Python's getattr function available to templates
@app.context_processor
def utility_processor():
    return dict(getattr=getattr)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Fetch user by ID

# Initialize SQLAlchemy with Flask
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Enable Foreign Key Constraints in SQLite
@app.before_request
def enable_foreign_keys():
    if 'sqlite' in SQLALCHEMY_DATABASE_URI:
        with db.engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys=ON"))

# admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.lower() != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('wtac_dashboard'))
        return f(*args, **kwargs)
    return decorated_function
 

# Route: Login (GET AND POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("\n=== LOGIN DEBUG START ===")
        print("LOGIN: POST request received")
        print(f"LOGIN: Form data: {request.form}")
        
        try:
            # CSRF protection is handled by CSRFProtect(app) automatically
            # We don't need to manually validate the token
            username = request.form['username']
            print(f"LOGIN: Username: {username}")
            
            plain_password = request.form['password']
            print("LOGIN: Password received (not logging actual value)")
            
            user = User.query.filter_by(username=username).first()
            print(f"LOGIN: User found: {user is not None}")

            if not user:
                print("LOGIN: User not found")
                flash("Invalid username or password.", "danger")
                return redirect(url_for('login'))
                
            password_match = check_password(plain_password, user.password)
            print(f"LOGIN: Password check result: {password_match}")
            
            if password_match:
                print(f"LOGIN: Login successful for user: {username}")
                login_user(user)
                next_page = request.args.get('next')
                if next_page:
                    print(f"LOGIN: Redirecting to next page: {next_page}")
                    print("=== LOGIN DEBUG END ===\n")
                    return redirect(next_page)
                
                # Check user role and redirect accordingly
                if user.role.lower() == 'admin':
                    print(f"LOGIN: Admin user detected, redirecting to index page")
                    print("=== LOGIN DEBUG END ===\n")
                    return redirect(url_for('index'))
                else:
                    print(f"LOGIN: Regular user detected, redirecting to WTAC dashboard")
                    print("=== LOGIN DEBUG END ===\n")
                    return redirect(url_for('wtac_dashboard'))
            else:
                print("LOGIN: Password mismatch")
                flash("Invalid username or password.", "danger")
                print("=== LOGIN DEBUG END ===\n")
                return redirect(url_for('login'))
                
        except Exception as e:
            print(f"LOGIN ERROR: {str(e)}")
            print("Exception traceback:")
            traceback.print_exc()
            flash(f"Error during login: {str(e)}", "danger")
            print("=== LOGIN DEBUG END ===\n")
            return redirect(url_for('login'))
    
    # For GET requests
    print("\n=== LOGIN GET DEBUG ===")
    print("LOGIN: GET request - rendering login template")
    print(f"LOGIN: Current session: {session}")
    print("=== LOGIN GET DEBUG END ===\n")
    
    return render_template('login.html')

# Route: Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))  # Keep this redirecting to index (home page)

# Route: Home 
@app.route('/')
@login_required
def index():
    # Redirect the root URL to the Formula Ford dashboard
    return redirect(url_for('formula_ford_dashboard'))

# Route: Formula Ford Dashboard
@app.route('/formula_ford/dashboard')
@login_required
def formula_ford_dashboard():
    events = FormulaFordEvent.query.order_by(FormulaFordEvent.round_number).all()
    return render_template('formula_ford_dashboard.html', events=events)

# Dynamic Formula Ford Round Route
@app.route('/formula_ford/round/<int:round_number>')
@login_required
def formula_ford_round(round_number):
    """
    Dynamically handles requests for any Formula Ford round.
    """
    event = FormulaFordEvent.query.filter_by(round_number=round_number).first_or_404()
    return render_template('formula_ford/round.html',
                           user=current_user, 
                           role=current_user.role,
                           event=event)

@app.route('/formula_ford/events')
@login_required
def manage_formula_ford_events():
    events = FormulaFordEvent.query.order_by(FormulaFordEvent.round_number).all()
    return render_template('formula_ford/manage_events.html', events=events)

@app.route('/formula_ford/events/add', methods=['POST'])
@login_required
def add_formula_ford_event():
    try:
        round_number = request.form.get('round_number', type=int)
        location = request.form.get('location')
        event_date = request.form.get('event_date')

        if not all([round_number, location, event_date]):
            flash('All fields are required', 'error')
            return redirect(url_for('manage_formula_ford_events'))

        # Check if the maximum number of rounds has been reached
        total_events = FormulaFordEvent.query.count()
        if total_events >= 20:
            flash('Cannot add more than 20 rounds.', 'error')
            return redirect(url_for('manage_formula_ford_events'))

        # Check if round number already exists
        existing_event = FormulaFordEvent.query.filter_by(round_number=round_number).first()
        if existing_event:
            flash(f'Round {round_number} already exists', 'error')
            return redirect(url_for('manage_formula_ford_events'))

        new_event = FormulaFordEvent(
            round_number=round_number,
            location=location,
            event_date=datetime.strptime(event_date, '%Y-%m-%d').date()
        )
        db.session.add(new_event)
        db.session.commit()
        flash(f'Event Round {round_number} added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding event: {str(e)}', 'error')
    
    return redirect(url_for('manage_formula_ford_events'))

@app.route('/formula_ford/events/<int:event_id>/competitors')
@login_required
def event_competitors(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # Get all competitors currently in this event
    event_competitor_ids = [entry.competitor_id for entry in entries]
    
    # Get all competitors
    all_competitors = FormulaFordCompetitor.query.all()
    
    # Filter competitors not already in this event
    available_competitors = [c for c in all_competitors if c.id not in event_competitor_ids]
    
    # Load competitor data for each entry and build a list of competitors in this event
    competitors = []
    for entry in entries:
        competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        competitor.entry_id = entry.id  # Attach entry ID to competitor
        competitor.entry_status = entry.entry_status
        competitor.weekend_car_number = entry.weekend_car_number
        competitor.FFgarage_number = entry.FFgarage_number # Correctly attach the garage number
        competitors.append(competitor)
    
    # Sort by weekend_car_number numerically if present, otherwise by car_number
    def numeric_sort_key(comp):
        if comp.weekend_car_number:
            # Convert to string if it's an integer
            weekend_num = str(comp.weekend_car_number) if isinstance(comp.weekend_car_number, int) else comp.weekend_car_number
            if weekend_num.isdigit():
                return int(weekend_num)
        if comp.car_number:
            # Convert to string if it's an integer
            car_num = str(comp.car_number) if isinstance(comp.car_number, int) else comp.car_number
            if car_num.isdigit():
                return int(car_num)
        return 999999  # Place non-numeric at the end
            
    competitors.sort(key=numeric_sort_key)
    
    return render_template('formula_ford/event_competitors.html', 
                          event=event, 
                          competitors=competitors,
                          available_competitors=available_competitors)

@app.route('/formula_ford/events/<int:event_id>/competitors/add', methods=['POST'])
@login_required
def add_formula_ford_event_competitor(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    competitor_id = request.form.get('competitor_id')
    weekend_car_number = request.form.get('weekend_car_number')
    FFgarage_number = request.form.get('FFgarage_number')
    entry_status = request.form.get('entry_status')

    # Check if the competitor is already in the event
    existing_entry = FormulaFordEventEntry.query.filter_by(
        event_id=event_id,
        competitor_id=competitor_id
    ).first()
    
    if existing_entry:
        flash('This competitor is already entered in the event.', 'warning')
    else:
        # If no weekend car number provided, use the competitor's regular car number
        if not weekend_car_number or not weekend_car_number.strip():
            competitor = db.session.get(FormulaFordCompetitor, competitor_id)
            if competitor:
                weekend_car_number = str(competitor.car_number)
        
        # Add the competitor to the event - Convert to title case for consistent display
        entry = FormulaFordEventEntry(
            event_id=event_id,
            competitor_id=competitor_id,
            weekend_car_number=weekend_car_number if weekend_car_number else None,
            FFgarage_number=FFgarage_number if FFgarage_number else None,
            entry_status=entry_status.title()
        )
        db.session.add(entry)
        
        try:
            db.session.commit()
            flash('Competitor added to event successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding competitor: {str(e)}', 'error')

    return redirect(url_for('event_competitors', event_id=event_id))

@app.route('/formula_ford/events/<int:event_id>/competitors/bulk_add', methods=['GET', 'POST'])
@login_required
def bulk_add_competitors(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    
    if request.method == 'POST':
        competitor_ids_to_add = request.form.getlist('competitor_ids')
        
        if not competitor_ids_to_add:
            flash('No competitors were selected.', 'warning')
            return redirect(url_for('bulk_add_competitors', event_id=event_id))
            
        added_count = 0
        for competitor_id in competitor_ids_to_add:
            weekend_car_number = request.form.get(f'weekend_car_number_{competitor_id}')
            garage_number = request.form.get(f'garage_number_{competitor_id}')
            
            # Use competitor's default car number if weekend number is not provided
            if not weekend_car_number or not weekend_car_number.strip():
                competitor = db.session.get(FormulaFordCompetitor, competitor_id)
                if competitor:
                    weekend_car_number = str(competitor.car_number)
            
            entry = FormulaFordEventEntry(
                event_id=event_id,
                competitor_id=competitor_id,
                weekend_car_number=weekend_car_number if weekend_car_number else None,
                FFgarage_number=garage_number if garage_number else None,
                entry_status='Confirmed' # Default status for bulk add
            )
            db.session.add(entry)
            added_count += 1
            
        try:
            db.session.commit()
            flash(f'Successfully added {added_count} competitors to the event.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding competitors: {str(e)}', 'error')
            
        return redirect(url_for('event_competitors', event_id=event_id))

    # GET request: Show the bulk add page
    # Get all competitors already in this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    event_competitor_ids = [entry.competitor_id for entry in entries]
    
    # Get all competitors not already in this event
    available_competitors = FormulaFordCompetitor.query.filter(FormulaFordCompetitor.id.notin_(event_competitor_ids)).order_by(FormulaFordCompetitor.car_number).all()
    
    return render_template('formula_ford/bulk_add_competitors.html', 
                           event=event, available_competitors=available_competitors)

@app.route('/formula_ford/events/<int:event_id>/weight_height_tracking/save_row', methods=['POST'])
@login_required
def save_weight_height_row(event_id):
    competitor_id = request.form.get('competitor_id')
    
    # Check if a record already exists
    record = CompetitorWeightHeight.query.filter_by(
        event_id=event_id,
        competitor_id=competitor_id
    ).first()
    
    if not record:
        # Create new record
        record = CompetitorWeightHeight(
            event_id=event_id,
            competitor_id=competitor_id
        )
        db.session.add(record)
    
    # Update qualifying data
    qual_weight = request.form.get(f'weight_qual_{competitor_id}')
    qual_height = request.form.get(f'height_qual_{competitor_id}')
    record.qual_weight = float(qual_weight) if qual_weight and qual_weight.strip() else record.qual_weight
    record.qual_height = qual_height if qual_height else record.qual_height
    
    # Update race 1 data
    r1_weight = request.form.get(f'weight_r1_{competitor_id}')
    r1_height = request.form.get(f'height_r1_{competitor_id}')
    record.r1_weight = float(r1_weight) if r1_weight and r1_weight.strip() else record.r1_weight
    record.r1_height = r1_height if r1_height else record.r1_height
    
    # Update race 2 data
    r2_weight = request.form.get(f'weight_r2_{competitor_id}')
    r2_height = request.form.get(f'height_r2_{competitor_id}')
    record.r2_weight = float(r2_weight) if r2_weight and r2_weight.strip() else record.r2_weight
    record.r2_height = r2_height if r2_height else record.r2_height
    
    # Update race 3 data
    r3_weight = request.form.get(f'weight_r3_{competitor_id}')
    r3_height = request.form.get(f'height_r3_{competitor_id}')
    record.r3_weight = float(r3_weight) if r3_weight and r3_weight.strip() else record.r3_weight
    record.r3_height = r3_height if r3_height else record.r3_height
    
    db.session.commit()
    flash('Record updated successfully for competitor.', 'success')
    return redirect(url_for('weight_height_tracking', event_id=event_id))

@app.route('/formula_ford/events/<int:event_id>/weight_height_tracking/save_all', methods=['POST'])
@login_required
def save_all_weight_height(event_id):
    # Get all entries for this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # Update records for each competitor
    saved_count = 0
    for entry in entries:
        competitor_id = entry.competitor_id
        
        # Skip if no data for this competitor
        if not any(key.endswith(f'_{competitor_id}') for key in request.form.keys()):
            continue
            
        # Check if a record already exists
        record = CompetitorWeightHeight.query.filter_by(
            event_id=event_id,
            competitor_id=competitor_id
        ).first()
        
        if not record:
            # Create new record
            record = CompetitorWeightHeight(
                event_id=event_id,
                competitor_id=competitor_id
            )
            db.session.add(record)
        
        # Update qualifying data
        qual_weight = request.form.get(f'weight_qual_{competitor_id}')
        qual_height = request.form.get(f'height_qual_{competitor_id}')
        record.qual_weight = float(qual_weight) if qual_weight and qual_weight.strip() else record.qual_weight
        record.qual_height = qual_height if qual_height else record.qual_height
        
        # Update race 1 data
        r1_weight = request.form.get(f'weight_r1_{competitor_id}')
        r1_height = request.form.get(f'height_r1_{competitor_id}')
        record.r1_weight = float(r1_weight) if r1_weight and r1_weight.strip() else record.r1_weight
        record.r1_height = r1_height if r1_height else record.r1_height
        
        # Update race 2 data
        r2_weight = request.form.get(f'weight_r2_{competitor_id}')
        r2_height = request.form.get(f'height_r2_{competitor_id}')
        record.r2_weight = float(r2_weight) if r2_weight and r2_weight.strip() else record.r2_weight
        record.r2_height = r2_height if r2_height else record.r2_height
        
        # Update race 3 data
        r3_weight = request.form.get(f'weight_r3_{competitor_id}')
        r3_height = request.form.get(f'height_r3_{competitor_id}')
        record.r3_weight = float(r3_weight) if r3_weight and r3_weight.strip() else record.r3_weight
        record.r3_height = r3_height if r3_height else record.r3_height
        
        saved_count += 1
    
    db.session.commit()
    flash(f'Successfully updated {saved_count} competitor records.', 'success')
    return redirect(url_for('weight_height_tracking', event_id=event_id))

@app.route('/formula_ford/events/<int:event_id>/technical_check')
@login_required
def technical_check(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    check_type = request.args.get('check_type', 'ecu')
    other_check_name = request.args.get('other_check_name', '').strip()
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # For each entry, load the competitor data
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        
        check = None
        if check_type == 'other':
            if other_check_name:
                # Find a specific "other" check by name for this competitor
                # We search for results starting with the check name + ':'
                check = TechnicalCheck.query.filter(
                    TechnicalCheck.event_id == event_id,
                    TechnicalCheck.competitor_id == entry.competitor_id,
                    TechnicalCheck.check_type == 'other',
                    TechnicalCheck.result.like(f"{other_check_name}:%")
                ).first()
        else:
            # Load any existing check for this competitor for non-'other' types
            check = TechnicalCheck.query.filter_by(
                event_id=event_id,
                competitor_id=entry.competitor_id,
                check_type=check_type
            ).first()
        
        # If a check exists, parse the result for display in the template.
        if check and check.result:
            if check_type == 'ecu':
                num_match = re.search(r'Number:\s*([^,]+)', check.result)
                tune_match = re.search(r'Tune:\s*(.*)', check.result)
                check.ecu_number = num_match.group(1).strip() if num_match else ''
                check.ecu_tune = tune_match.group(1).strip() if tune_match else ''
            elif check_type == 'engine':
                check.engine_number = check.result
            elif check_type == 'other' and ':' in check.result:
                # For 'other', split the result into name and status
                parts = check.result.split(':', 1)
                check.status = parts[1].strip() if len(parts) > 1 else ''
        entry.check = check
    
    # Sort by weekend_car_number numerically if present, otherwise by car_number
    def numeric_sort_key(entry):
        if entry.weekend_car_number:
            # Convert to string if it's an integer
            weekend_num = str(entry.weekend_car_number) if isinstance(entry.weekend_car_number, int) else entry.weekend_car_number
            if weekend_num.isdigit():
                return int(weekend_num)
        if entry.competitor and entry.competitor.car_number:
            # Convert to string if it's an integer
            car_num = str(entry.competitor.car_number) if isinstance(entry.competitor.car_number, int) else entry.competitor.car_number
            if car_num.isdigit():
                return int(car_num)
        return 999999  # Place non-numeric at the end
            
    entries.sort(key=numeric_sort_key)
    
    return render_template('formula_ford/technical_check.html',
                         event=event,
                         entries=entries,
                         check_type=check_type,
                         other_check_name=other_check_name)

@app.route('/formula_ford/events/<int:event_id>/technical_check/save', methods=['POST'])
@login_required
def save_technical_check(event_id):
    competitor_id = request.form.get('competitor_id')
    check_type = request.form.get('check_type') # This will be 'ecu', 'engine', etc.
    
    # Get the result based on the check type
    result = ''
    if check_type == 'weight':
        result = request.form.get(f'weight_{competitor_id}', '')
    elif check_type == 'ecu':
        ecu_number = request.form.get(f'ecu_number_{competitor_id}', '')
        ecu_tune = request.form.get(f'ecu_tune_{competitor_id}', '')
        result = f"Number: {ecu_number}, Tune: {ecu_tune}"
    elif check_type == 'engine':
        result = request.form.get(f'engine_number_{competitor_id}', '')
    elif check_type == 'other':
        other_check_name = request.form.get('other_check_name', '').strip()
        other_status = request.form.get(f'other_status_{competitor_id}', '')
        if other_check_name and other_status:
            result = f"{other_check_name}: {other_status}"
    else:
        result = request.form.get(f'{check_type}_status_{competitor_id}', '') # Use the specific status name
    
    notes = request.form.get(f'notes_{competitor_id}', '').strip()
    
    record = None
    if check_type == 'other' and other_check_name:
        # For 'other' checks, we need to find the record based on the check name
        record = TechnicalCheck.query.filter(
            TechnicalCheck.event_id == event_id,
            TechnicalCheck.competitor_id == competitor_id,
            TechnicalCheck.check_type == 'other',
            TechnicalCheck.result.like(f"{other_check_name}:%")
        ).first()
    else:
        # For all other check types
        record = TechnicalCheck.query.filter_by(
            event_id=event_id,
            competitor_id=competitor_id,
            check_type=check_type
        ).first()
    
    if record:
        record.result = result
        record.notes = notes
        record.inspector_name = current_user.username
        record.check_date = datetime.now().date()
    else:
        record = TechnicalCheck(
            event_id=event_id,
            competitor_id=competitor_id,
            check_type=check_type,
            result=result,
            notes=notes,
            inspector_name=current_user.username,
            check_date=datetime.now().date()
        )
        db.session.add(record)
    
    try:
        db.session.commit()
        flash(f'{check_type.replace("_", " ").title()} check saved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving check: {str(e)}', 'error')
    
    return redirect(url_for('technical_check', event_id=event_id, check_type=check_type))

@app.route('/formula_ford/events/<int:event_id>/weight_height_tracking')
@login_required
def weight_height_tracking(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # Load competitor data and weight/height records
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        entry.weight_height = CompetitorWeightHeight.query.filter_by(
            event_id=event_id,
            competitor_id=entry.competitor_id
        ).first()
    
    # Sort by weekend_car_number numerically if present, otherwise by car_number
    def numeric_sort_key(entry):
        if entry.weekend_car_number:
            # Convert to string if it's an integer
            weekend_num = str(entry.weekend_car_number) if isinstance(entry.weekend_car_number, int) else entry.weekend_car_number
            if weekend_num.isdigit():
                return int(weekend_num)
        if entry.competitor and entry.competitor.car_number:
            # Convert to string if it's an integer
            car_num = str(entry.competitor.car_number) if isinstance(entry.competitor.car_number, int) else entry.competitor.car_number
            if car_num.isdigit():
                return int(car_num)
        return 999999  # Place non-numeric at the end
            
    entries.sort(key=numeric_sort_key)
    
    return render_template('formula_ford/weight_height_tracking.html',
                         event=event,
                         entries=entries)

@app.route('/formula_ford/events/<int:event_id>/technical_records')
@login_required
def event_technical_records(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    
    # Get all technical records for this event
    records = TechnicalCheck.query.filter_by(event_id=event_id).all()
    
    # Group records by competitor
    records_by_competitor = {}
    for record in records:
        if record.competitor_id not in records_by_competitor:
            records_by_competitor[record.competitor_id] = []
        records_by_competitor[record.competitor_id].append(record)
    
    # Get all competitors in this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        entry.records = records_by_competitor.get(entry.competitor_id, [])
    
    # Sort by weekend_car_number numerically if present, otherwise by car_number
    def numeric_sort_key(entry):
        if entry.weekend_car_number:
            # Convert to string if it's an integer
            weekend_num = str(entry.weekend_car_number) if isinstance(entry.weekend_car_number, int) else entry.weekend_car_number
            if weekend_num.isdigit():
                return int(weekend_num)
        if entry.competitor and entry.competitor.car_number:
            # Convert to string if it's an integer
            car_num = str(entry.competitor.car_number) if isinstance(entry.competitor.car_number, int) else entry.competitor.car_number
            if car_num.isdigit():
                return int(car_num)
        return 999999  # Place non-numeric at the end
            
    entries.sort(key=numeric_sort_key)
    
    return render_template('formula_ford/technical_records.html',
                         event=event,
                         entries=entries)

@app.route('/formula_ford/events/<int:event_id>/tyre_records')
@login_required
def event_tyre_records(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    
    # Get all tyre records for this event
    records = FormulaFordTyreCheck.query.filter_by(event_id=event_id).all()
    
    # Group records by competitor
    records_by_competitor = {}
    for record in records:
        if record.competitor_id not in records_by_competitor:
            records_by_competitor[record.competitor_id] = []
        records_by_competitor[record.competitor_id].append(record)
    
    # Get all competitors in this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        entry.records = records_by_competitor.get(entry.competitor_id, [])
    
    # Sort by weekend_car_number numerically if present, otherwise by car_number
    def numeric_sort_key(entry):
        if entry.weekend_car_number:
            # Convert to string if it's an integer
            weekend_num = str(entry.weekend_car_number) if isinstance(entry.weekend_car_number, int) else entry.weekend_car_number
            if weekend_num.isdigit():
                return int(weekend_num)
        if entry.competitor and entry.competitor.car_number:
            # Convert to string if it's an integer
            car_num = str(entry.competitor.car_number) if isinstance(entry.competitor.car_number, int) else entry.competitor.car_number
            if car_num.isdigit():
                return int(car_num)
        return 999999  # Place non-numeric at the end
            
    entries.sort(key=numeric_sort_key)
    
    return render_template('formula_ford/tyre_records.html',
                         event=event,
                         entries=entries)

@app.route('/formula_ford/events/<int:event_id>/technical_check/save_all', methods=['POST'])
@login_required
def save_all_technical_checks(event_id):
    print("\n--- DEBUG: save_all_technical_checks ---")
    print(f"Received form data: {request.form}")

    check_type = request.form.get('check_type')
    saved_count = 0

    # --- FIX: Dynamically find competitor IDs from submitted form data ---
    # Create a set of unique competitor IDs from the form keys.
    # e.g., 'ecu_number_5' -> '5', 'notes_5' -> '5'. The set will store '5' only once.
    competitor_ids = set()
    for key in request.form:
        # --- FIX: Explicitly skip metadata fields to avoid parsing errors ---
        if key in ['csrf_token', 'check_type', 'other_check_name']:
            continue
        if '_' in key: # Only process keys that are expected to contain an ID
            parts = key.split('_')
            if parts[-1].isdigit():
                competitor_ids.add(parts[-1])
    
    print(f"Found competitor IDs in form: {competitor_ids}")
    
    for competitor_id in competitor_ids:
        # Get the result based on the check type
        result = ''
        notes = request.form.get(f'notes_{competitor_id}', '').strip()
        has_data = False

        print(f"\nProcessing competitor_id: {competitor_id}")

        if check_type == 'weight':
            weight = request.form.get(f'weight_{competitor_id}', '')
            result = weight
            if weight: has_data = True
        elif check_type == 'ecu':
            ecu_number = request.form.get(f'ecu_number_{competitor_id}', '')
            ecu_tune = request.form.get(f'ecu_tune_{competitor_id}', '')
            if ecu_number or ecu_tune:
                result = f"Number: {ecu_number}, Tune: {ecu_tune}"
                has_data = True
        elif check_type == 'engine':
            result = request.form.get(f'engine_number_{competitor_id}', '')
            if result: has_data = True
        elif check_type == 'other':
            other_check_name = request.form.get('other_check_name', '').strip()
            other_status = request.form.get(f'other_status_{competitor_id}', '')
            # Only create a result if both name and status are present
            if other_check_name and other_status:
                result = f"{other_check_name}: {other_status}"
                has_data = True
            else:
                result = ''
        else:
            result = request.form.get(f'{check_type}_status_{competitor_id}', '') # Correctly formatted name
            if result: has_data = True

        print(f"  - Result string: '{result}'")
        print(f"  - Notes: '{notes}'")
        
        # Skip if no meaningful data for this competitor
        if not has_data and not notes:
            print("  - SKIPPING: No data or notes found.")
            continue
            
        record = None
        if check_type == 'other' and other_check_name:
            # For 'other' checks, find the record based on the check name
            record = TechnicalCheck.query.filter(
                TechnicalCheck.event_id == event_id,
                TechnicalCheck.competitor_id == competitor_id,
                TechnicalCheck.check_type == 'other',
                TechnicalCheck.result.like(f"{other_check_name}:%")
            ).first()
        else:
            record = TechnicalCheck.query.filter_by(
                event_id=event_id,
                competitor_id=competitor_id,
                check_type=check_type
            ).first()
        
        print(f"  - Existing record found: {record is not None}")
        if record:
            record.result = result
            record.notes = notes
            record.inspector_name = current_user.username
            record.check_date = datetime.now().date()
        else:
            record = TechnicalCheck(
                event_id=event_id,
                competitor_id=competitor_id,
                check_type=check_type,
                result=result,
                notes=notes,
                inspector_name=current_user.username,
                check_date=datetime.now().date()
            )
            db.session.add(record)
        
        saved_count += 1
    
    print(f"Total saved count: {saved_count}")
    try:
        db.session.commit()
        flash(f'{saved_count} {check_type.replace("_", " ").title()} checks saved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving checks: {str(e)}', 'error')
    print("--- DEBUG END ---\n")
    
    return redirect(url_for('technical_check', event_id=event_id, check_type=check_type))

@app.route('/formula_ford/events/<int:event_id>/technical_check/other_check_names', methods=['GET'])
@login_required
def get_other_check_names(event_id):
    """Get a list of unique 'other check' names used in this event"""
    check_names = []
    try:
        # Find all 'other' type technical checks for this event
        other_checks = TechnicalCheck.query.filter_by(
            event_id=event_id,
            check_type='other'
        ).all()
        
        # Extract unique check names from the results
        check_names = []
        for check in other_checks:
            # Extract check name from result string (format: "Name: Status")
            if check.result and ':' in check.result:
                name = check.result.split(':', 1)[0].strip()
                if name and name not in check_names:
                    check_names.append(name)
        
        return jsonify(check_names=check_names)
    except Exception as e:
        return jsonify(error=str(e), check_names=[])

@app.route('/formula_ford/events/update', methods=['POST'])
@login_required
def update_formula_ford_event():
    try:
        event_id = request.form.get('event_id')
        event = db.session.get(FormulaFordEvent, event_id) or abort(404)
        
        # Update fields
        event.location = request.form.get('location')
        event_date = request.form.get('event_date')
        if event_date:
            event.event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Event updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating event: {str(e)}', 'error')
    
    return redirect(url_for('manage_formula_ford_events'))

@app.route('/formula_ford/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_formula_ford_event(event_id):
    """Deletes a specific event and its related data."""
    try:
        event = db.session.get(FormulaFordEvent, event_id) or abort(404)
        # The database cascade should handle related deletions in other tables
        db.session.delete(event)
        db.session.commit()
        flash(f"Successfully deleted Event Round {event.round_number} and all related data.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting event: {str(e)}", "danger")
    
    return redirect(url_for('manage_formula_ford_events'))

@app.route('/formula_ford/events/<int:event_id>/cleanup_technical_checks', methods=['GET'])
@login_required
def cleanup_technical_checks(event_id):
    """
    Admin utility to clean up duplicate technical check records.
    For each competitor and check type, it keeps only the oldest record and deletes duplicates.
    """
    try:
        # Get all distinct competitor_id and check_type combinations for this event
        check_combinations = db.session.query(
            TechnicalCheck.competitor_id, 
            TechnicalCheck.check_type
        ).filter_by(event_id=event_id).distinct().all()
        
        deleted_count = 0
        
        # For each combination
        for competitor_id, check_type in check_combinations:
            # Get all records for this combination
            records = TechnicalCheck.query.filter_by(
                event_id=event_id,
                competitor_id=competitor_id,
                check_type=check_type
            ).order_by(TechnicalCheck.id).all()
            
            # If we have more than one record, keep the first (oldest) and delete the rest
            if len(records) > 1:
                # Keep the first one
                for record in records[1:]:
                    db.session.delete(record)
                    deleted_count += 1
        
        db.session.commit()
        if deleted_count > 0:
            flash(f"Successfully removed {deleted_count} duplicate technical check records.", "success")
        else:
            flash("No duplicate records found. Database is clean.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error cleaning up technical checks: {str(e)}", "danger")
    
    return redirect(url_for('event_technical_checks', event_id=event_id))

@app.route('/formula_ford/competitors')
@login_required
def manage_formula_ford_competitors():
    # Get sorting parameter from query string, default to car_number
    sort_by = request.args.get('sort_by', 'car_number')
    
    # Define the sorting criteria
    if sort_by == 'name':
        order_by = [FormulaFordCompetitor.last_name, FormulaFordCompetitor.first_name]
    elif sort_by == 'team':
        order_by = [FormulaFordCompetitor.team_association]
    elif sort_by == 'vehicle':
        order_by = [FormulaFordCompetitor.vehicle_make, FormulaFordCompetitor.vehicle_type]
    else:  # default to car_number
        order_by = [FormulaFordCompetitor.car_number]
    
    # Get all competitors with the specified sorting
    competitors = FormulaFordCompetitor.query.order_by(*order_by).all()
    
    return render_template('formula_ford/manage_competitors.html', 
                          competitors=competitors,
                          sort_by=sort_by)

@app.route('/formula_ford/competitors/add', methods=['POST'])
@login_required
def add_formula_ford_competitor():
    try:
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        team_association = request.form.get('team_association')
        vehicle_make = request.form.get('vehicle_make')
        vehicle_type = request.form.get('vehicle_type')
        car_number = request.form.get('car_number')

        # Validate required fields
        if not all([first_name, last_name, vehicle_make, vehicle_type, car_number]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('manage_formula_ford_competitors'))

        try:
            car_number = int(car_number)
        except ValueError:
            flash('Car number must be a valid number', 'error')
            return redirect(url_for('manage_formula_ford_competitors'))
            
        # Check if car number already exists
        existing = FormulaFordCompetitor.query.filter_by(car_number=car_number).first()
        if existing:
            flash(f'Car number {car_number} is already in use', 'error')
            return redirect(url_for('manage_formula_ford_competitors'))

        # Create new competitor
        competitor = FormulaFordCompetitor(
            first_name=first_name,
            last_name=last_name,
            team_association=team_association,
            vehicle_make=vehicle_make,
            vehicle_type=vehicle_type,
            car_number=car_number
        )
        
        db.session.add(competitor)
        db.session.commit()
        flash('Competitor added successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding competitor: {str(e)}', 'error')
    
    return redirect(url_for('manage_formula_ford_competitors'))

@app.route('/formula_ford/competitors/<int:competitor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_formula_ford_competitor(competitor_id):
    competitor = db.session.get(FormulaFordCompetitor, competitor_id) or abort(404)

    if request.method == 'POST':
        # Get updated data from the form
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        team_association = request.form.get('team_association')
        vehicle_make = request.form.get('vehicle_make')
        vehicle_type = request.form.get('vehicle_type')
        car_number_str = request.form.get('car_number') # Get as string first

        # Basic validation
        if not all([first_name, last_name, vehicle_make, vehicle_type, car_number_str]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('edit_formula_ford_competitor', competitor_id=competitor.id))

        try:
            car_number = int(car_number_str)
        except ValueError:
            flash('Car number must be a valid integer.', 'error')
            return redirect(url_for('edit_formula_ford_competitor', competitor_id=competitor.id))

        # Check for duplicate car number, excluding the current competitor
        existing_competitor_with_car_number = FormulaFordCompetitor.query.filter(
            FormulaFordCompetitor.car_number == car_number,
            FormulaFordCompetitor.id != competitor_id
        ).first()
        if existing_competitor_with_car_number:
            flash(f'Car number {car_number} is already in use by another competitor.', 'error')
            return redirect(url_for('edit_formula_ford_competitor', competitor_id=competitor.id))

        # Update competitor object
        competitor.first_name = first_name
        competitor.last_name = last_name
        competitor.team_association = team_association
        competitor.vehicle_make = vehicle_make
        competitor.vehicle_type = vehicle_type
        competitor.car_number = car_number

        try:
            db.session.commit()
            flash('Competitor updated successfully.', 'success')
            return redirect(url_for('manage_formula_ford_competitors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating competitor: {str(e)}', 'error')
            # Re-render the form with current data and error
            return render_template('formula_ford/edit_competitor.html', competitor=competitor)

    # GET request: Render the edit form
    return render_template('formula_ford/edit_competitor.html', competitor=competitor)

@app.route('/formula_ford/events/<int:event_id>/entries/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event_entry(event_id, entry_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    entry = db.session.get(FormulaFordEventEntry, entry_id) or abort(404)
    competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id) or abort(404)
    
    if request.method == 'POST':
        entry_status = request.form.get('entry_status')
        weekend_car_number = request.form.get('weekend_car_number')
        FFgarage_number = request.form.get('FFgarage_number')
        notes = request.form.get('notes')
        
        if not entry_status:
            flash('Entry status is required', 'error')
            return redirect(url_for('edit_event_entry', event_id=event_id, entry_id=entry_id))
        
        try:
            entry.entry_status = entry_status
            entry.weekend_car_number = weekend_car_number
            entry.FFgarage_number = FFgarage_number
            entry.notes = notes
            db.session.commit()
            flash('Entry updated successfully', 'success')
            return redirect(url_for('event_competitors', event_id=event_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating entry: {str(e)}', 'error')
    
    return render_template('formula_ford/edit_event_entry.html',
                         event=event,
                         entry=entry,
                         competitor=competitor)

@app.route('/formula_ford/events/<int:event_id>/entries/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_event_entry(event_id, entry_id):
    try:
        entry = db.session.get(FormulaFordEventEntry, entry_id) or abort(404)
        db.session.delete(entry)
        db.session.commit()
        flash('Entry deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting entry: {str(e)}', 'error')

    return redirect(url_for('event_competitors', event_id=event_id))

@app.route('/formula_ford/competitors/<int:competitor_id>/delete', methods=['POST'])
@login_required
def delete_formula_ford_competitor(competitor_id):
    try:
        # First check if the competitor exists without loading related models
        competitor_exists = db.session.execute(
            text("SELECT id, first_name, last_name, car_number FROM formula_ford_competitor WHERE id = :id"),
            {"id": competitor_id}
        ).fetchone()
        
        if not competitor_exists:
            flash(f'Competitor not found.', 'error')
            return redirect(url_for('manage_formula_ford_competitors'))
        
        # Extract competitor info for the success message
        competitor_id, first_name, last_name, car_number = competitor_exists
        
        # Begin transaction
        db.session.begin_nested()
        
        # Get a list of all tables in the database
        tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        table_names = [table[0] for table in tables]
        
        # Check each table for a competitor_id column and delete records if present
        for table_name in table_names:
            # Skip the formula_ford_competitor table itself
            if table_name == 'formula_ford_competitor':
                continue
                
            # Check if the table has a competitor_id column
            try:
                columns = db.session.execute(
                    text(f"PRAGMA table_info({table_name})")
                ).fetchall()
                
                column_names = [col[1] for col in columns]
                
                # If the table has a competitor_id column, delete matching records
                if 'competitor_id' in column_names:
                    db.session.execute(
                        text(f"DELETE FROM {table_name} WHERE competitor_id = :competitor_id"),
                        {"competitor_id": competitor_id}
                    )
            except Exception as e:
                # Log but continue - table might be a view or have issues
                print(f"Error checking/cleaning table {table_name}: {str(e)}")
        
        # Finally delete the competitor
        db.session.execute(
            text("DELETE FROM formula_ford_competitor WHERE id = :id"),
            {"id": competitor_id}
        )
        
        # Commit all changes
        db.session.commit()
        flash(f'Competitor {first_name} {last_name} (Car #{car_number}) deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting competitor: {str(e)}', 'error')
        
    return redirect(url_for('manage_formula_ford_competitors'))

@app.route('/formula-ford/event/<int:event_id>/tyre-checklist')
@login_required
def formula_ford_tyre_checklist(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    
    # Get all entries for this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # Load competitor data for each entry
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        
        # Check if there's already a tyre checklist record
        entry.tyre_checklist = TyreChecklist.query.filter_by(
            event_id=event_id, 
            competitor_id=entry.competitor_id
        ).first()
        
        # If no record exists, create one
        if not entry.tyre_checklist:
            new_checklist = TyreChecklist(
                event_id=event_id,
                competitor_id=entry.competitor_id,
                last_updated=datetime.now()
            )
            db.session.add(new_checklist)
            entry.tyre_checklist = new_checklist
    
    db.session.commit()
    
    # Use numeric sorting for weekend_car_number
    entries.sort(key=lambda entry: 
        int(entry.weekend_car_number) if entry.weekend_car_number and entry.weekend_car_number.isdigit() 
        else float('inf')
    )
    
    return render_template('formula_ford/tyre_checklist.html', 
                          event=event, 
                          entries=entries)

@app.route('/formula-ford/event/<int:event_id>/tyre-checklist/save-row', methods=['POST'])
@login_required
def save_tyre_check_row(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    competitor_id = request.form.get('competitor_id')
    
    if not competitor_id:
        flash('Invalid request - missing competitor ID', 'danger')
        return redirect(url_for('formula_ford_tyre_checklist', event_id=event_id))
    
    # Find or create the tyre checklist record
    checklist = TyreChecklist.query.filter_by(
        event_id=event_id,
        competitor_id=competitor_id
    ).first()
    
    if not checklist:
        checklist = TyreChecklist(
            event_id=event_id,
            competitor_id=competitor_id
        )
        db.session.add(checklist)
    
    # Update all checkbox fields
    checklist.tyres_marked_practice = request.form.get('tyres_marked_practice') == 'true'
    checklist.tyres_marked_qualifying = request.form.get('tyres_marked_qualifying') == 'true'
    checklist.practice1_checked = request.form.get('practice1_checked') == 'true'
    checklist.practice2_checked = request.form.get('practice2_checked') == 'true'
    checklist.practice3_checked = request.form.get('practice3_checked') == 'true'
    checklist.practice4_checked = request.form.get('practice4_checked') == 'true'
    checklist.qualifying_checked = request.form.get('qualifying_checked') == 'true'
    checklist.race1_checked = request.form.get('race1_checked') == 'true'
    checklist.race2_checked = request.form.get('race2_checked') == 'true'
    checklist.race3_checked = request.form.get('race3_checked') == 'true'
    
    # Record who updated it and when
    checklist.inspector_name = current_user.username
    checklist.last_updated = datetime.now()
    
    db.session.commit()
    
    flash('Tyre check data saved successfully!', 'success')
    return redirect(url_for('formula_ford_tyre_checklist', event_id=event_id))

@app.route('/formula-ford/event/<int:event_id>/tyre-checklist/save-all', methods=['POST'])
@login_required
def save_all_tyre_checks(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    
    # Get all entries for this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # Process each competitor's checkboxes
    for entry in entries:
        competitor_id = entry.competitor_id
        
        # Find or create the tyre checklist record
        checklist = TyreChecklist.query.filter_by(
            event_id=event_id,
            competitor_id=competitor_id
        ).first()
        
        if not checklist:
            checklist = TyreChecklist(
                event_id=event_id,
                competitor_id=competitor_id
            )
            db.session.add(checklist)
        
        # Update checkbox fields based on form data
        prefix_list = [
            'tyres_marked_practice',
            'tyres_marked_qualifying',
            'practice1_checked',
            'practice2_checked',
            'practice3_checked',
            'practice4_checked',
            'qualifying_checked',
            'race1_checked',
            'race2_checked',
            'race3_checked'
        ]
        
        for prefix in prefix_list:
            field_name = f"{prefix}_{competitor_id}"
            setattr(checklist, prefix, field_name in request.form)
        
        # Record who updated it and when
        checklist.inspector_name = current_user.username
        checklist.last_updated = datetime.now()
    
    db.session.commit()
    
    flash('All tyre check data saved successfully!', 'success')
    return redirect(url_for('formula_ford_tyre_checklist', event_id=event_id))

@app.route('/formula-ford/event/<int:event_id>/tyre-checklist/save-notes', methods=['POST'])
@login_required
def save_tyre_check_notes(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    competitor_id = request.form.get('competitor_id')
    notes = request.form.get('notes', '')
    
    if not competitor_id:
        flash('Invalid request - missing competitor ID', 'danger')
        return redirect(url_for('formula_ford_tyre_checklist', event_id=event_id))
    
    # Find or create the tyre checklist record
    checklist = TyreChecklist.query.filter_by(
        event_id=event_id,
        competitor_id=competitor_id
    ).first()
    
    if not checklist:
        checklist = TyreChecklist(
            event_id=event_id,
            competitor_id=competitor_id
        )
        db.session.add(checklist)
    
    # Update notes
    checklist.notes = notes
    
    # Record who updated it and when
    checklist.inspector_name = current_user.username
    checklist.last_updated = datetime.now()
    
    db.session.commit()
    
    flash('Notes saved successfully!', 'success')
    return redirect(url_for('formula_ford_tyre_checklist', event_id=event_id))

@app.route('/formula_ford/events/<int:event_id>/garage_numbers')
@login_required
def formula_ford_garage_numbers(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    
    # Get all entries for this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # Load competitor data for each entry
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
    
    # Sort by weekend_car_number numerically if present, otherwise by car_number
    def numeric_sort_key(entry):
        if entry.weekend_car_number:
            # Convert to string if it's an integer
            weekend_num = str(entry.weekend_car_number) if isinstance(entry.weekend_car_number, int) else entry.weekend_car_number
            if weekend_num.isdigit():
                return int(weekend_num)
        if entry.competitor and entry.competitor.car_number:
            # Convert to string if it's an integer
            car_num = str(entry.competitor.car_number) if isinstance(entry.competitor.car_number, int) else entry.competitor.car_number
            if car_num.isdigit():
                return int(car_num)
        return 999999  # Place non-numeric at the end
    
    entries.sort(key=numeric_sort_key)
    
    return render_template('formula_ford/garage_list.html', 
                         event=event, 
                         entries=entries)

@app.route('/formula_ford/events/<int:event_id>/garage_numbers/save-row', methods=['POST'])
@login_required
def save_garage_number_row(event_id):
    entry_id = request.form.get('entry_id')
    garage_number = request.form.get('garage_number')
    
    if not entry_id:
        flash('Invalid request - missing entry ID', 'danger')
        return redirect(url_for('formula_ford_garage_numbers', event_id=event_id))
    
    # Find the entry
    entry = db.session.get(FormulaFordEventEntry, entry_id) or abort(404)
    
    # Update garage number
    entry.FFgarage_number = garage_number
    
    db.session.commit()
    
    flash('Garage number saved successfully!', 'success')
    return redirect(url_for('formula_ford_garage_numbers', event_id=event_id))

@app.route('/formula_ford/events/<int:event_id>/garage_numbers/save-all', methods=['POST'])
@login_required
def save_all_garage_numbers(event_id):
    # Get all entries for this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # Update garage numbers
    for entry in entries:
        garage_number_key = f'garage_number_{entry.id}'
        if garage_number_key in request.form:
            entry.FFgarage_number = request.form.get(garage_number_key)
    
    db.session.commit()
    
    flash('All garage numbers saved successfully!', 'success')
    return redirect(url_for('formula_ford_garage_numbers', event_id=event_id))

@app.route('/formula_ford/database_management')
@login_required
def database_management():
    """Renders the database management page with options for purging data."""
    events = FormulaFordEvent.query.order_by(FormulaFordEvent.round_number).all()
    return render_template('formula_ford/database_management.html', events=events)

@app.route('/formula_ford/purge/all_events', methods=['POST'])
@login_required
def purge_all_events():
    """Deletes all events and their related data."""
    try:
        # The database cascade should handle related deletions
        num_deleted = FormulaFordEvent.query.delete()
        db.session.commit()
        flash(f"Successfully deleted {num_deleted} events and all related data.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting events: {str(e)}", "danger")
    return redirect(url_for('database_management'))

@app.route('/formula_ford/purge/all_competitors', methods=['POST'])
@login_required
def purge_all_competitors():
    """Deletes all competitors and their related data."""
    try:
        # The database cascade should handle related deletions
        num_deleted = FormulaFordCompetitor.query.delete()
        db.session.commit()
        flash(f"Successfully deleted {num_deleted} competitors and all their related data.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting competitors: {str(e)}", "danger")
    return redirect(url_for('database_management'))

@app.route('/formula_ford/purge/all_checks', methods=['POST'])
@login_required
def purge_all_checks():
    """Deletes all check-related data."""
    try:
        num_tech = TechnicalCheck.query.delete()
        num_tyre = TyreChecklist.query.delete()
        num_wh = CompetitorWeightHeight.query.delete()
        db.session.commit()
        flash(f"Successfully deleted {num_tech} technical checks, {num_tyre} tyre checklists, and {num_wh} weight/height records.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting checks: {str(e)}", "danger")
    return redirect(url_for('database_management'))

@app.route('/formula_ford/purge/everything', methods=['POST'])
@login_required
def purge_everything():
    """Deletes all data from all Formula Ford tables."""
    try:
        # Delete in an order that respects foreign key constraints
        # Checks first, then entries, then competitors and events
        TechnicalCheck.query.delete()
        TyreChecklist.query.delete()
        CompetitorWeightHeight.query.delete()
        FormulaFordEventEntry.query.delete()
        FormulaFordCompetitor.query.delete()
        FormulaFordEvent.query.delete()
        
        db.session.commit()
        flash("Successfully purged all Formula Ford data from the database.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred during the purge: {str(e)}", "danger")
    return redirect(url_for('database_management'))

# Run the application
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    args = parser.parse_args()
    
    app.run(host='0.0.0.0', debug=True, port=args.port)

@app.cli.command("delete-other-checks")
def delete_other_checks():
    """Deletes all technical checks with the type 'other' from the database."""
    try:
        # Count how many 'other' checks exist before deleting
        num_deleted = TechnicalCheck.query.filter_by(check_type='other').count()
        
        if num_deleted == 0:
            print("No 'other' technical checks found to delete.")
            return

        # Perform the deletion
        TechnicalCheck.query.filter_by(check_type='other').delete()
        db.session.commit()
        print(f"Successfully deleted {num_deleted} 'other' technical checks from the database.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {str(e)}")
