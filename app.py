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
    return render_template('index.html')  # Render the new index page with two buttons

# Route: WTAC Dashboard
@app.route('/wtac_dashboard')
@login_required
def wtac_dashboard():
    user_role = current_user.role  # Get the role of the logged-in user
    return render_template('wtac_dashboard.html', user=current_user, role=user_role)  # Render the WTAC dashboard

# Route: Formula Ford Dashboard
@app.route('/formula_ford/dashboard')
@login_required
def formula_ford_dashboard():
    events = FormulaFordEvent.query.order_by(FormulaFordEvent.round_number).all()
    return render_template('formula_ford_dashboard.html', events=events)

# Route: Register
@app.route('/register')
def register():
    return render_template('register.html')

# Route: Add Entry (GET)
@app.route('/add_entry', methods=['GET'])
@login_required
def show_add_entry():
    # Define valid classes or fetch them from your system
    classes = [
        "Tuner", "Clubsprint", "Open", "Pro Open",
        "Pro Am", "Pro", "Flying 500", "Demo"
    ]
    return render_template('add_entry.html', classes=classes)  # Pass classes to the template

# Route: Add Entry (POST)
@app.route('/add_entry', methods=['POST'])
@login_required
def add_entry():
    # Extract data from the form
    vehicle_number = request.form.get('vehicle_number')
    vehicle_make = request.form.get('vehicle_make')
    vehicle_model = request.form.get('vehicle_model')
    garage_number = request.form.get('garage_number')
    log_book_number = request.form.get('log_book_number')
    licence_number = request.form.get('licence_number', '000000')
    driver_name = request.form.get('driver_name')
    class_type = request.form.get('class')
    normalized_class_type = class_type.replace(' ', '_').lower()
    action = request.form.get('action')  # Capture the action (add or add_and_inspect)

    # Check mandatory fields
    if not vehicle_number or not vehicle_make or not driver_name or not class_type:
        return render_template('add_entry.html', error="Please fill in all required fields.")

    # Create a new Entry object
    new_entry = Entry(
        vehicle_number=vehicle_number,
        vehicle_make=vehicle_make,
        vehicle_model=vehicle_model,
        garage_number=garage_number,
        log_book_number=log_book_number,
        licence_number=licence_number,
        driver_name=driver_name,
        class_type=normalized_class_type
    )

    try:
        # Add the entry to the database
        db.session.add(new_entry)
        db.session.commit()

        # Handle the "Add Entry and Inspect" action
        if action == "add_and_inspect":
            # Generate a checklist for the new entry
            checklist = InspectionChecklist(entry_id=new_entry.id)
            db.session.add(checklist)
            db.session.commit()

            # Dynamically generate inspection items from checklist_items
            applicable_items = ChecklistItem.query.filter(
                getattr(ChecklistItem, f"applicable_to_{new_entry.class_type.lower()}") == True
            ).all()

            for item in applicable_items:
                new_item = InspectionItem(
                    checklist_id=checklist.id,
                    item_name=item.item_name,
                    brand_required=item.brand_required,
                    standard_required=item.standard_required,
                    expiry_date_required=item.expiry_date_required,
                    rops_required=item.rops_required
                )
                db.session.add(new_item)

            db.session.commit()

            # Redirect to the checklist page
            return redirect(url_for('view_checklist', checklist_id=checklist.id))

        # Handle the "Add Entry" action
        return render_template('index.html', success="Entry added successfully!")

    except Exception as e:
        print(f"Error adding entry: {e}")
        return render_template('add_entry.html', error="Failed to add entry. Please try again.")
    
# Route: Lookup Entry (GET)
@app.route('/lookup_entry', methods=['GET'])
@login_required
def lookup_entry():
    search_query = request.args.get('search_query', '').strip()

    if search_query:
        # Fetch entries matching the search query
        results = db.session.query(
            Entry.id,
            Entry.driver_name,
            Entry.vehicle_number,
            Entry.vehicle_make,
            Entry.vehicle_model,
            Entry.class_type,
            Entry.garage_number
        ).filter(
            or_(
                Entry.driver_name.ilike(f"%{search_query}%"),
                Entry.vehicle_number.ilike(f"%{search_query}%"),
                Entry.vehicle_make.ilike(f"%{search_query}%"),
                Entry.vehicle_model.ilike(f"%{search_query}%")
            )
        ).order_by(
            func.cast(
                func.substr(
                    Entry.vehicle_number,
                    1,
                    func.instr(Entry.vehicle_number + 'A', 'A') - 1
                ),
                Integer
        )
    ).all()
    else:
        results = []

    # Render the template and pass the results
    return render_template('lookup_entry.html', results=results, search_query=search_query)

# Route: Lookup Entry2 (GET)
@app.route('/lookup_entry2', methods=['GET'])
@login_required
# This route is similar to lookup_entry but its for loaded the button stye view page
def lookup_entry2():
    search_query = request.args.get('search_query', '').strip()

    if search_query:
        # Fetch entries matching the search query
        results = db.session.query(
            Entry.id,
            Entry.driver_name,
            Entry.vehicle_number,
            Entry.vehicle_make,
            Entry.vehicle_model,
            Entry.class_type,
            Entry.garage_number
        ).filter(
            or_(
                Entry.driver_name.ilike(f"%{search_query}%"),
                Entry.vehicle_number.ilike(f"%{search_query}%"),
                Entry.vehicle_make.ilike(f"%{search_query}%"),
                Entry.vehicle_model.ilike(f"%{search_query}%")
            )
        ).order_by(
    func.cast(
        func.substr(
            Entry.vehicle_number,
            1,
            func.instr(Entry.vehicle_number + 'A', 'A') - 1
        ),
        Integer
    )
).all()
    else:
        results = []

    # Render the template and pass the results
    return render_template('lookup_entry2.html', results=results, search_query=search_query)


# Route: View Checklist (GET & POST)
@app.route('/view_checklist', methods=['GET', 'POST'])
@login_required
def view_checklist():
    scrutineers = Officials.query.filter_by(role="Scrutineer").all()

    if request.method == 'POST':
        entry_id = request.form.get('entry_id')  # Get entry_id from the form
        print(f"Received entry_id: {entry_id}")  # Debugging

        entry = db.session.get(Entry, entry_id)  # Retrieve the entry
        if not entry:
            return jsonify({'error': "Entry not found!"}), 404

        print(f"Found entry: {entry}")  # Debugging

        # Check if a checklist exists for this entry
        checklist = InspectionChecklist.query.filter_by(entry_id=entry.id).first()

        if not checklist:
            print("No checklist found. Creating a new checklist.")  # Debugging

            # Create a new checklist
            checklist = InspectionChecklist(entry_id=entry.id)
            db.session.add(checklist)
            db.session.commit()

            # Dynamically generate inspection items for this checklist
            applicable_items = ChecklistItem.query.filter(
                getattr(ChecklistItem, f"applicable_to_{entry.class_type.lower()}") == True
            ).all()

            for item in applicable_items:
                new_item = InspectionItem(
                    checklist_id=checklist.id,
                    item_name=item.item_name,
                    brand_required=item.brand_required,
                    standard_required=item.standard_required,
                    expiry_date_required=item.expiry_date_required,
                    rops_required=item.rops_required
                )
                db.session.add(new_item)

            db.session.commit()

        # Retrieve checklist items for rendering
        items = InspectionItem.query.filter_by(checklist_id=checklist.id).all()
        print(f"Checklist ID: {checklist.id}, Number of items: {len(items)}")  # Debugging

        return render_template('checklist.html', checklist=checklist, items=items, entry=entry, scrutineers=scrutineers, current_date=datetime.now().strftime('%Y-%m-%d'), current_time=datetime.now().strftime('%H:%M:%S'))

    elif request.method == 'GET':
        checklist_id = request.args.get('checklist_id')  # Get checklist_id from query parameters
        checklist = db.session.get(InspectionChecklist, int(checklist_id)) if checklist_id else None

        if not checklist:
            return jsonify({'error': "Checklist not found!"}), 404

        # Fetch associated entry
        entry = db.session.get(Entry, checklist.entry_id)
        items = InspectionItem.query.filter_by(checklist_id=checklist.id).all()
       

        return render_template(
            'checklist.html',
            checklist=checklist,
            items=items,
            entry=entry,
            scrutineers=scrutineers,
            current_date=datetime.now().strftime('%Y-%m-%d'),
            current_time=datetime.now().strftime('%H:%M:%S')
        )

# Route: View Checklist2 (GET & POST)
@app.route('/view_checklist2', methods=['GET', 'POST'])
@login_required
def view_checklist2():
    user_role = current_user.role
    scrutineers = Officials.query.filter_by(role="Scrutineer").all()

    if request.method == 'POST':
        # Handle POST request: Create or fetch checklist based on entry_id
        entry_id = request.form.get('entry_id')  # Get entry_id from the form
        print(f"Received entry_id: {entry_id}")  # Debugging

        entry = db.session.get(Entry, entry_id)  # Retrieve the entry
        if not entry:
            return jsonify({'error': "Entry not found!"}), 404

        print(f"Found entry: {entry}")  # Debugging

        # Check if a checklist exists for this entry
        checklist = InspectionChecklist.query.filter_by(entry_id=entry.id).first()

        if not checklist:
            print("No checklist found. Creating a new checklist.")  # Debugging

            # Create a new checklist
            checklist = InspectionChecklist(entry_id=entry.id)
            db.session.add(checklist)
            db.session.commit()

            # Dynamically generate inspection items for this checklist
            applicable_items = ChecklistItem.query.filter(
                getattr(ChecklistItem, f"applicable_to_{entry.class_type.lower()}") == True
            ).all()

            for item in applicable_items:
                new_item = InspectionItem(
                    checklist_id=checklist.id,
                    item_name=item.item_name,
                    brand_required=item.brand_required,
                    standard_required=item.standard_required,
                    expiry_date_required=item.expiry_date_required,
                    rops_required=item.rops_required
                )
                db.session.add(new_item)

            db.session.commit()

        # Retrieve checklist items for rendering
        items = InspectionItem.query.filter_by(checklist_id=checklist.id).all()
        print(f"Checklist ID: {checklist.id}, Number of items: {len(items)}")  # Debugging

        return render_template(
            'checklist2.html',
            checklist=checklist,
            items=items,
            entry=entry,
            scrutineers=scrutineers,
            current_date=datetime.now().strftime('%Y-%m-%d'),
            current_time=datetime.now().strftime('%H:%M:%S')
        )

    elif request.method == 'GET':
        # Handle GET request: Fetch checklist based on checklist_id
        checklist_id = request.args.get('checklist_id')  # Get checklist_id from query parameters
        checklist = db.session.get(InspectionChecklist, int(checklist_id)) if checklist_id else None

        if not checklist:
            return jsonify({'error': "Checklist not found!"}), 404

        # Fetch associated entry
        entry = db.session.get(Entry, checklist.entry_id)
        items = InspectionItem.query.filter_by(checklist_id=checklist.id).all()

        return render_template(
            'checklist2.html',
            checklist=checklist,
            items=items,
            entry=entry,
            scrutineers=scrutineers,
            current_date=datetime.now().strftime('%Y-%m-%d'),
            current_time=datetime.now().strftime('%H:%M:%S'),
            user=current_user, role=user_role
        )    
# route: update checklist 2

@app.route('/update_checklist2', methods=['POST'])
@login_required

def update_checklist2():
    user_role = current_user.role
    print(request.form)  # Debug submitted form data
    try:
        checklist_id = request.form.get('checklist_id')
        checklist_items = InspectionItem.query.filter_by(checklist_id=checklist_id).all()

        vehicle_approved = False  # Initialize approval status

        # Use no_autoflush from the session
        with db.session.no_autoflush:
            for item in checklist_items:
                # Handle special items separately
                if item.item_name in ["Vehicle Weight", "Time", "Date", "Scrutineer Name", "Scrutineer Licence Number"]:
                    if item.item_name == "Vehicle Weight":
                        vehicle_weight = request.form.get(f'vehicle_weight_{item.id}')
                        if vehicle_weight:
                            item.value = vehicle_weight
                    elif item.item_name == "Time":
                        time_value = request.form.get('time')
                        if time_value:
                            item.value = time_value
                    elif item.item_name == "Date":
                        date_value = request.form.get('date')
                        if date_value:
                            item.value = date_value
                    continue  # Skip the rest of the loop for these items

                # Update the status from the form data
                status = request.form.get(f'status_{item.id}')
                if status:
                    item.status = status

                # Conditionally update extra fields based on item requirements
                if item.brand_required:
                    item.brand = request.form.get(f'brand_{item.id}')
                if item.standard_required:
                    item.standard = request.form.get(f'standard_{item.id}')
                if item.expiry_date_required:
                    expiry_date_value = request.form.get(f'expiry_date_{item.id}')
                    if expiry_date_value:
                        # Convert the string to a Python date object
                        item.expiry_date = datetime.strptime(expiry_date_value, '%Y-%m-%d').date()
                    else:
                        item.expiry_date = None
                if item.rops_required:
                    item.rops = request.form.get(f'rops_{item.id}')

                # Check if "Approved to Start" is set to True
                if item.item_name == 'Approved to Start' and item.status == 'Pass':
                    vehicle_approved = True

                db.session.add(item)

        # Update checklist-level attributes
        checklist = db.session.get(InspectionChecklist, checklist_id)
        checklist.approved_to_start = vehicle_approved
        checklist.scrutineer_name = request.form.get('scrutineer_name')
        checklist.scrutineer_licence_number = request.form.get('scrutineer_licence_number')

        # Convert date string to Python date object
        date_value = request.form.get('date')
        if date_value:
            checklist.date = datetime.strptime(date_value, '%Y-%m-%d').date()  # Convert to date object

        # Convert time string to Python time object
        time_value = request.form.get('time')
        if time_value:
            checklist.time = datetime.strptime(time_value, '%H:%M:%S').time()  # Convert to time object

        # Commit changes to the database
        db.session.commit()
        flash("Checklist updated successfully!", "success")
        return redirect(url_for('lookup_entry2', checklist_id=checklist_id))

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
        flash("An error occurred while updating the checklist. Please try again.", "error")
        return redirect(url_for('view_checklist2', checklist_id=checklist_id, user=current_user, role=user_role))
                            
# Route: Vehicle Weights
@app.route('/vehicle_weights')
@login_required
def vehicle_weights():
    # Fetch vehicle weights from the database
    vehicles = db.session.query(
        Entry.vehicle_number,
        Entry.driver_name,
        Entry.class_type,
        InspectionItem.value.label('vehicle_weight')
    ).join(InspectionChecklist, Entry.id == InspectionChecklist.entry_id) \
     .join(InspectionItem, InspectionChecklist.id == InspectionItem.checklist_id) \
     .filter(InspectionItem.item_name == "Vehicle Weight") \
     .order_by(
    func.cast(
        func.substr(
            Entry.vehicle_number,
            1,
            func.instr(Entry.vehicle_number + 'A', 'A') - 1
        ),
        Integer
    )
).all() 
## debug
    print("Vehicles Data:", vehicles)
    # Render the template and pass the vehicle data
    return render_template('vehicle_weights.html', vehicles=vehicles)

# Route: Outstanding Items
@app.route('/outstanding_items')
def outstanding_items():
    # Get the sorting preference from the query parameter (default is 'vehicle_number')
    order_by = request.args.get('order_by', 'vehicle_number')

    # Determine the sorting column
    if order_by == 'garage_number':
        order_column = func.cast(
            func.substr(
                Entry.garage_number,
                1,
                func.instr(Entry.garage_number + 'A', 'A') - 1
            ),
            Integer
        )
    else:
        order_column = func.cast(
            func.substr(
                Entry.vehicle_number,
                1,
                func.instr(Entry.vehicle_number + 'A', 'A') - 1
            ),
            Integer
        )
        

    # Fetch vehicles with unresolved inspection items
    items = db.session.query(
        Entry.id.label('entry_id'),
        Entry.vehicle_number,
        Entry.driver_name,
        Entry.class_type,
        Entry.garage_number,
        func.group_concat(InspectionItem.item_name).label('failed_items')
    ).join(InspectionChecklist, Entry.id == InspectionChecklist.entry_id) \
     .join(InspectionItem, InspectionChecklist.id == InspectionItem.checklist_id) \
     .filter(InspectionItem.status.in_(["Pending", "Failed"])) \
     .filter(~InspectionItem.item_name.in_([
         "Vehicle Weight", "Scrutineer Name", "Scrutineer Licence Number", "Date", "Time"
     ])) \
     .group_by(Entry.id) \
     .order_by(order_column).all()

    # Render the template and pass the data
    return render_template('outstanding_items.html', items=items, order_by=order_by)

# Route: Garage Numbers
@app.route('/garage_numbers')
@login_required
def garage_numbers():
    # Get the sorting preference from the query parameter (default is 'vehicle_number')
    order_by = request.args.get('order_by', 'vehicle_number')

    # Determine the sorting column
    if order_by == 'garage_number':
        order_column = func.cast(
            func.substr(
                Entry.garage_number,
                1,
                func.instr(Entry.garage_number + 'A', 'A') - 1
            ),
            Integer
        )
    else:
        order_column = func.cast(
            func.substr(
                Entry.vehicle_number,
                1,
                func.instr(Entry.vehicle_number + 'A', 'A') - 1
            ),
            Integer
        )

    # Fetch vehicle details and garage numbers from the database
    vehicles = db.session.query(
        Entry.vehicle_number,
        Entry.driver_name,
        Entry.class_type,
        Entry.garage_number
    ).order_by(order_column).all()

    # Render the template and pass the vehicle data
    return render_template('garage_numbers.html', vehicles=vehicles, order_by=order_by)

# Update Checklist
@app.route('/update_checklist', methods=['POST'])
@login_required
def update_checklist():
    print(request.form)  # Debug submitted form data
    try:
        checklist_id = request.form.get('checklist_id')
        checklist_items = InspectionItem.query.filter_by(checklist_id=checklist_id).all()

        vehicle_approved = False  # Initialize approval status

        # Use no_autoflush from the session
        with db.session.no_autoflush:
            for item in checklist_items:
                # Handle special items separately
                if item.item_name in ["Vehicle Weight", "Time", "Date", "Scrutineer Name", "Scrutineer Licence Number"]:
                    if item.item_name == "Vehicle Weight":
                        vehicle_weight = request.form.get(f'vehicle_weight_{item.id}')
                        if vehicle_weight:
                            item.value = vehicle_weight
                    elif item.item_name == "Time":
                        time_value = request.form.get('time')
                        if time_value:
                            item.value = time_value
                    elif item.item_name == "Date":
                        date_value = request.form.get('date')
                        if date_value:
                            item.value = date_value
                    continue  # Skip the rest of the loop for these items

                # Update the status from the form data
                status = request.form.get(f'status_{item.id}')
                if status:
                    item.status = status

                # Conditionally update extra fields based on item requirements
                if item.brand_required:
                    item.brand = request.form.get(f'brand_{item.id}')
                if item.standard_required:
                    item.standard = request.form.get(f'standard_{item.id}')
                if item.expiry_date_required:
                    expiry_date_value = request.form.get(f'expiry_date_{item.id}')
                    if expiry_date_value:
                        # Convert the string to a Python date object
                        item.expiry_date = datetime.strptime(expiry_date_value, '%Y-%m-%d').date()
                    else:
                        item.expiry_date = None
                if item.rops_required:
                    item.rops = request.form.get(f'rops_{item.id}')

                # Check if "Approved to Start" is set to True
                if item.item_name == 'Approved to Start' and item.status == 'Pass':
                    vehicle_approved = True

                db.session.add(item)

        # Update checklist-level attributes
        checklist = db.session.get(InspectionChecklist, checklist_id)
        checklist.approved_to_start = vehicle_approved
        checklist.scrutineer_name = request.form.get('scrutineer_name')
        checklist.scrutineer_licence_number = request.form.get('scrutineer_licence_number')

        # Convert date string to Python date object
        date_value = request.form.get('date')
        if date_value:
            checklist.date = datetime.strptime(date_value, '%Y-%m-%d').date()  # Convert to date object

        # Convert time string to Python time object
        time_value = request.form.get('time')
        if time_value:
            checklist.time = datetime.strptime(time_value, '%H:%M:%S').time()  # Convert to time object

        # Commit changes to the database
        db.session.commit()
        flash("Checklist updated successfully!", "success")
        return redirect(url_for('lookup_entry'))

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
        flash("An error occurred while updating the checklist. Please try again.", "error")
        return redirect(url_for('view_checklist', checklist_id=checklist_id))
    
# Route: Denied Start
@app.route('/denied_start')
@login_required
def denied_start():
    # Get the sorting preference from the query parameter (default is 'vehicle_number')
    order_by = request.args.get('order_by', 'vehicle_number')

    # Determine the sorting column
    if order_by == 'garage_number':
        order_column = func.cast(
            func.substr(
                Entry.garage_number,
                1,
                func.instr(Entry.garage_number + 'A', 'A') - 1
            ),
            Integer
        )
    else:
        order_column = func.cast(
            func.substr(
                Entry.vehicle_number,
                1,
                func.instr(Entry.vehicle_number + 'A', 'A') - 1
            ),
            Integer
        )

    # Fetch vehicles where "Approved to Start" is "Fail"
    items = db.session.query(
        Entry.id.label('entry_id'),
        Entry.vehicle_number,
        Entry.driver_name,
        Entry.class_type,
        Entry.garage_number
    ).join(InspectionChecklist, Entry.id == InspectionChecklist.entry_id) \
     .join(InspectionItem, InspectionChecklist.id == InspectionItem.checklist_id) \
     .filter(InspectionItem.item_name == "Approved to Start") \
     .filter(InspectionItem.status == "Fail") \
     .order_by(order_column).all()

    # Render the template and pass the data
    return render_template('denied_start.html', items=items, order_by=order_by)

# Route: Not Approved to start
@app.route('/not_approved')
@login_required
def not_approved():
    # Get the sorting preference from the query parameter (default is 'vehicle_number')
    order_by = request.args.get('order_by', 'vehicle_number')

    # Determine the sorting column
    if order_by == 'garage_number':
        order_column = func.cast(
            func.substr(
                Entry.garage_number,
                1,
                func.instr(Entry.garage_number + 'A', 'A') - 1
            ),
            Integer
        )
    else:
        order_column = func.cast(
            func.substr(
                Entry.vehicle_number,
                1,
                func.instr(Entry.vehicle_number + 'A', 'A') - 1
            ),
            Integer
        )

    # Fetch vehicles where "Approved to Start" is "Pending" or "N/A"
    items = db.session.query(
        Entry.id.label('entry_id'),
        Entry.vehicle_number,
        Entry.driver_name,
        Entry.class_type,
        Entry.garage_number
    ).join(InspectionChecklist, Entry.id == InspectionChecklist.entry_id) \
     .join(InspectionItem, InspectionChecklist.id == InspectionItem.checklist_id) \
     .filter(InspectionItem.item_name == "Approved to Start") \
     .filter(InspectionItem.status.in_(["Pending", "NA"])) \
     .order_by(order_column).all()
    # Render the template and pass the data
    return render_template('not_approved.html', items=items, order_by=order_by)

# Route: Denied Start Counter
@app.route('/denied_start_count')
@login_required
def denied_start_count():
    # Count vehicles where "Approved to Start" is "Fail"

    count = db.session.query(Entry).join(InspectionChecklist, Entry.id == InspectionChecklist.entry_id) \
        .join(InspectionItem, InspectionChecklist.id == InspectionItem.checklist_id) \
        .filter(InspectionItem.item_name == "Approved to Start") \
        .filter(InspectionItem.status == "Fail").count()

    # Return the count as JSON
    return jsonify({'denied_start_count': count})

# Route: Not Presented
@app.route('/not_presented')
@login_required
def not_presented():
    # Get the sorting preference from the query parameter (default is 'vehicle_number')
    order_by = request.args.get('order_by', 'vehicle_number')

    # Determine the sorting column
    if order_by == 'garage_number':
        order_column = func.cast(
            func.substr(
                Entry.garage_number,
                1,
                func.instr(Entry.garage_number + 'A', 'A') - 1
            ),
            Integer
        )
    else:
        order_column = func.cast(
            func.substr(
                Entry.vehicle_number,
                1,
                func.instr(Entry.vehicle_number + 'A', 'A') - 1
            ),
            Integer
        )

    # Fetch vehicles without an associated checklist
    vehicles = db.session.query(
        Entry.id,
        Entry.vehicle_number,
        Entry.driver_name,
        Entry.class_type,
        Entry.garage_number
    ).outerjoin(InspectionChecklist, Entry.id == InspectionChecklist.entry_id) \
     .filter(InspectionChecklist.id == None) \
     .order_by(order_column).all()

    # Render the template and pass the vehicle data
    return render_template('not_presented.html', vehicles=vehicles, order_by=order_by)

# Route: Print Scrutiners
@app.route('/scrutineers')
@admin_required
def scrutineers_list():
    user_role = current_user.role
    scrutineers = Officials.query.filter_by(role="Scrutineer").order_by(Officials.name.asc()).all()
    return render_template('scrutineers.html', scrutineers=scrutineers, user=current_user, role=user_role)

# Route: Add Officals
@app.route('/add_official', methods=['GET', 'POST'])
@admin_required
def add_official():
    user_role = current_user.role
    if request.method == 'POST':
        # Get data from the form
        name = request.form.get('name')
        role = request.form.get('role')
        licence_number = request.form.get('licence_number')
        contact_info = request.form.get('contact_info')

        # Validate required fields
        if not name or not role or not licence_number:
            roles = Roles.query.all()
            return render_template('add_official.html', error="Please fill in all required fields.", roles=roles)

        # Create a new Official object
        new_official = Officials(
            name=name,
            role=role,
            licence_number=licence_number,
            contact_info=contact_info,
        )

        try:
            db.session.add(new_official)
            db.session.commit()
            return redirect('/add_official')
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            roles = Roles.query.all()
            return render_template('add_official.html', error="Failed to add official. Please try again.", roles=roles, user=current_user, role=user_role)

    # Handle GET request
    roles = Roles.query.all()
    return render_template('add_official.html', roles=roles)

@app.route('/manage_entries', methods=['GET', 'POST'])
@admin_required
def manage_entries():
    # List of valid classes for the dropdown.
    valid_classes = ["Tuner", "Clubsprint", "Open", "Pro Open", "Pro Am", "Pro", "Flying 500", "Demo"]
    
    if request.method == 'POST':
        action = request.form.get('action')
        entry_id = request.form.get('entry_id')
        entry = db.session.get(Entry, entry_id)
        if not entry:
            flash("Entry not found.", "danger")
            return redirect(url_for('manage_entries'))
        
        if action == 'save':
            # Update all editable fields.
            entry.vehicle_number = request.form.get('vehicle_number')
            entry.driver_name = request.form.get('driver_name')
            new_class = request.form.get('class_type')
            if new_class:
                entry.class_type = new_class.replace(' ', '_').lower()
            entry.garage_number = request.form.get('garage_number')
            
            try:
                db.session.commit()
                flash("Entry updated successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Failed to update the entry.", "danger")
        
        elif action == 'delete':
            try:
                # If an associated checklist exists, delete it and its related items.
                checklist = InspectionChecklist.query.filter_by(entry_id=entry.id).first()
                if checklist:
                    InspectionItem.query.filter_by(checklist_id=checklist.id).delete()
                    db.session.delete(checklist)
                db.session.delete(entry)
                db.session.commit()
                flash("Entry (and its associated checklist, if any) deleted successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Failed to delete the entry.", "danger")
        
        return redirect(url_for('manage_entries'))
    
    # For GET requests, fetch and order all entries by the numeric portion of vehicle_number.
    order_num = func.cast(
        func.substr(Entry.vehicle_number, 1, func.instr(Entry.vehicle_number + 'A', 'A') - 1),
        Integer
    )
    entries = Entry.query.order_by(order_num.asc()).all()
    
    return render_template('manage_entries.html', entries=entries, valid_classes=valid_classes)

# Route: Admin View/Delete Checklists
@app.route('/manage_checklists', methods=['GET', 'POST'])
@admin_required
def manage_checklists():
    if request.method == 'POST':
        action = request.form.get('action')
        checklist_id = request.form.get('checklist_id')
        checklist = db.session.get(InspectionChecklist, checklist_id)
        if not checklist:
            flash("Checklist not found.", "danger")
            return redirect(url_for('manage_checklists'))
        
        if action == 'delete':
            try:
                # Delete associated inspection items first, if any.
                InspectionItem.query.filter_by(checklist_id=checklist.id).delete()
                db.session.delete(checklist)
                db.session.commit()
                flash("Checklist deleted successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Failed to delete the checklist.", "danger")
            return redirect(url_for('manage_checklists'))
    
    # For GET requests, we need to fetch all checklists along with related Entry info.
    # We also want to extract the numeric part of the vehicle_number for proper sorting.
    order_num = func.cast(
        func.substr(Entry.vehicle_number, 1, func.instr(Entry.vehicle_number + 'A', 'A') - 1),
        Integer
    )
    # Define conditional aggregation for checking if any item is failed or pending.
    failed_flag = func.max(case((InspectionItem.status == 'Fail', 1), else_=0)).label('has_failed')
    pending_flag = func.max(case((InspectionItem.status == 'Pending', 1), else_=0)).label('has_pending')
    
    # Build the query joining InspectionChecklist to Entry and left joining InspectionItem.
    checklists = db.session.query(
        InspectionChecklist.id.label('checklist_id'),
        Entry.vehicle_number,
        Entry.driver_name,
        InspectionChecklist.approved_to_start,
        failed_flag,
        pending_flag
    ).join(Entry, InspectionChecklist.entry_id == Entry.id) \
     .outerjoin(InspectionItem, InspectionChecklist.id == InspectionItem.checklist_id) \
     .group_by(InspectionChecklist.id, Entry.vehicle_number, Entry.driver_name, InspectionChecklist.approved_to_start) \
     .order_by(order_num.asc()).all()
    
    return render_template('manage_checklists.html', checklists=checklists)

# Route: Admin View/Delete Officials
@app.route('/manage_officials', methods=['GET', 'POST'])
@admin_required
def manage_officials():
    if request.method == 'POST':
        action = request.form.get('action')
        official_id = request.form.get('official_id')
        # Use the new API to retrieve the official record.
        official = db.session.get(Officials, official_id)
        if not official:
            flash("Official not found.", "danger")
            return redirect(url_for('manage_officials'))

        if action == 'save':
            # Update all editable fields.
            official.name = request.form.get('name')
            official.licence_number = request.form.get('licence_number')
            official.contact_info = request.form.get('contact_info')
            new_role = request.form.get('role')
            if new_role:
                official.role = new_role
            try:
                db.session.commit()
                flash("Official updated successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Failed to update the official.", "danger")
        
        elif action == 'delete':
            try:
                db.session.delete(official)
                db.session.commit()
                flash("Official deleted successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Failed to delete the official.", "danger")

        return redirect(url_for('manage_officials'))
    
    # For GET requests, fetch and order all officials by name.
    officials = Officials.query.order_by(Officials.name.asc()).all()

    # Get valid roles for the drop-down.
    # We assume you have a Roles model and want to list them in alphabetical order.
    roles_query = Roles.query.order_by(Roles.role_name.asc()).all()
    roles_list = [role.role_name for role in roles_query]
    # Fallback to a default list if no roles are defined.
    if not roles_list:
        roles_list = ["Admin", "Scrutineer", "User", "Other"]

    return render_template('manage_officials.html', officials=officials, roles_list=roles_list)

# Route: Admin Import CSV to Entries
@app.route('/import_entries', methods=['GET', 'POST'])
@admin_required
def import_entries():
    if request.method == 'POST':
        print("Request Files:", request.files)  # Debug
        csv_file = request.files.get('csv_file')
        
        if not csv_file or csv_file.filename == '':
            flash("No file uploaded", "danger")
            print("No file selected")  # Debug
            return redirect(url_for('import_entries'))
            
        if not csv_file.filename.endswith('.csv'):
            flash("Please upload a CSV file", "danger")
            print("Invalid file type")  # Debug
            return redirect(url_for('import_entries'))
            
        try:
            # Read CSV with UTF-8-SIG to handle BOM
            content = csv_file.stream.read().decode('utf-8-sig')
            print("Raw content (first 500 chars):", content[:500])  # Debug
            
            # Get CSV headers and data
            csv_reader = csv.reader(io.StringIO(content))
            headers = next(csv_reader)  # Get headers
            csv_data = list(csv_reader)  # Get all rows
            
            print("CSV Headers:", headers)  # Debug
            print(f"Rows read: {len(csv_data)}")  # Debug
            
            # Define the database columns we want to map
            db_columns = [
                'vehicle_number',
                'driver_name',
                'vehicle_make',
                'vehicle_model',
                'class_type',
                'team_name',
                'garage_number',
                'log_book_number',
                'licence_number'
            ]
            
            # Convert data to JSON-safe format
            json_safe_data = []
            for row in csv_data:
                json_safe_data.append([str(cell) for cell in row])
            
            return render_template(
                'mapping.html',
                csv_headers=headers,
                db_columns=db_columns,
                csv_data=json_safe_data
            )
            
        except Exception as e:
            flash(f"Error processing file: {str(e)}", "danger")
            print(f"Error: {str(e)}")  # Debug
            return redirect(url_for('import_entries'))
            
    return render_template('import.html')

@app.route('/preview_data', methods=['POST'])
@admin_required
def preview_data():
    try:
        print("Form data received:", request.form)  # Debug
        
        # Get raw CSV data and headers
        raw_csv_data = json.loads(request.form.get('raw_csv_data'))
        raw_csv_headers = json.loads(request.form.get('raw_csv_headers'))
        
        # Get mappings
        mappings = {}
        for key, value in request.form.items():
            if key.startswith('mapping['):
                db_field = key[8:-1]  # Remove 'mapping[' and ']'
                mappings[db_field] = value if value else ''
        
        # Valid classes list - now including "Blank"
        valid_classes = ['Tuner', 'Clubsprint', 'Open', 'Pro Open', 'Pro Am', 
                        'Pro', 'Flying 500', 'Demo', 'Blank']
        
        # Process rows
        processed_rows = []
        for row_data in raw_csv_data:
            # Create a dictionary from the row using headers
            row = dict(zip(raw_csv_headers, row_data))
            
            processed_row = {}
            
            # Map CSV columns to database fields
            for db_col, csv_col in mappings.items():
                if csv_col:  # Only map if a column was selected
                    processed_row[db_col] = row.get(csv_col, '')
                else:
                    processed_row[db_col] = ''

            # Set default vehicle type
            processed_row['vehicle_type'] = 'W'

            # Normalize class type
            class_type = processed_row.get('class_type', '').lower()
            class_mapping = {
                'proam': 'Pro Am',
                'proopen': 'Pro Open',
                'demonstration': 'Demo',
                'flying500': 'Flying 500',
                'drift': 'Blank',  # Map drift to Blank
                '': 'Blank'  # Map empty to Blank
            }
            
            # Get normalized class or title case the existing value
            normalized_class = class_mapping.get(class_type, class_type.title())
            
            # If normalized class isn't in valid_classes or is Blank, set to "Blank" and mark for exclusion
            if normalized_class not in valid_classes or normalized_class == 'Blank':
                processed_row['class_type'] = 'Blank'
                processed_row['should_exclude'] = True  # Mark for exclusion
            else:
                processed_row['class_type'] = normalized_class
                processed_row['should_exclude'] = False

            # Add class suffix to vehicle number if numeric
            if processed_row.get('vehicle_number', '').isdigit():
                suffix_mapping = {
                    'Tuner': 'T',
                    'Clubsprint': 'C',
                    'Open': 'O',
                    'Pro Open': 'PO',
                    'Pro Am': 'PA',
                    'Pro': 'P',
                    'Flying 500': 'F',
                    'Demo': 'D',
                    'Blank': ''  # No suffix for Blank class
                }
                suffix = suffix_mapping.get(processed_row['class_type'], '')
                if suffix:
                    processed_row['vehicle_number'] = f"{processed_row['vehicle_number']}{suffix}"

            processed_rows.append(processed_row)

        print(f"Processed {len(processed_rows)} rows")  # Debug

        return render_template('preview_data.html',
                             rows=processed_rows,
                             valid_classes=valid_classes)

    except Exception as e:
        print(f"Error in preview_data: {str(e)}")  # Debug
        print(f"Request form data: {request.form}")  # Debug
        flash(f"Error processing data: {str(e)}", "danger")
        return redirect(url_for('import_entries'))

@app.route('/import_data', methods=['POST'])
@admin_required
def import_data():
    try:
        print("Starting data import...")  # Debug
        
        # Get all form data
        form_data = request.form.to_dict(flat=False)  # Get as multidict to handle arrays
        
        # Get the number of entries based on vehicle numbers length
        num_entries = len(form_data.get('vehicle_number[]', []))
        print(f"Number of entries to process: {num_entries}")  # Debug
        
        # Track duplicates for reporting
        duplicates = []
        imported = []
        
        # Get existing vehicle numbers
        existing_numbers = {
            number[0] for number in 
            db.session.query(Entry.vehicle_number).all()
        }
        
        # Process each entry
        entries = []
        for i in range(num_entries):
            # Skip if this row is marked for exclusion
            if form_data.get('exclude[]', []):
                if len(form_data['exclude[]']) > i and form_data['exclude[]'][i] == 'true':
                    print(f"Skipping excluded row {i}")  # Debug
                    continue
            
            vehicle_number = form_data['vehicle_number[]'][i] if i < len(form_data['vehicle_number[]']) else ''
            
            # Skip entries with no vehicle number or marked as NULL
            if not vehicle_number or vehicle_number == 'NULL':
                print(f"Skipping entry with no vehicle number")  # Debug
                continue
            
            # Check for duplicates both in database and current import
            if vehicle_number in existing_numbers:
                print(f"Duplicate vehicle number found in database: {vehicle_number}")  # Debug
                duplicates.append(vehicle_number)
                continue

            # Get values with safe fallbacks for all fields
            log_book = form_data.get('log_book_number[]', [''])[i] if i < len(form_data.get('log_book_number[]', [])) else ''
            licence = form_data.get('licence_number[]', [''])[i] if i < len(form_data.get('licence_number[]', [])) else ''
                
            entry = Entry(
                vehicle_number=vehicle_number,
                driver_name=form_data['driver_name[]'][i] if i < len(form_data['driver_name[]']) else '',
                vehicle_make=form_data['vehicle_make[]'][i] if i < len(form_data['vehicle_make[]']) else '',
                vehicle_model=form_data['vehicle_model[]'][i] if i < len(form_data['vehicle_model[]']) else '',
                class_type=form_data['class_type[]'][i] if i < len(form_data['class_type[]']) else '',
                team_name=form_data['team_name[]'][i] if i < len(form_data['team_name[]']) else '',
                garage_number=form_data['garage_number[]'][i] if i < len(form_data['garage_number[]']) else '',
                log_book_number=log_book,
                licence_number=licence,
                vehicle_type='W'  # Default value
            )
            entries.append(entry)
            imported.append(vehicle_number)
            # Add to existing numbers to catch duplicates within current import
            existing_numbers.add(vehicle_number)
        
        print(f"Processed {len(entries)} valid entries")  # Debug
        
        try:
            # Add all entries to the session
            for entry in entries:
                db.session.add(entry)
            
            # Commit the transaction
            db.session.commit()
            
            # Create appropriate flash messages
            if imported:
                flash(f"Successfully imported {len(imported)} entries", "success")
            if duplicates:
                flash(f"Skipped {len(duplicates)} duplicate entries: {', '.join(duplicates)}", "warning")
            if not imported and duplicates:
                flash("No new entries were imported - all were duplicates", "warning")
            
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")  # Debug
            flash(f"Error importing data: {str(e)}", "danger")
            
        return redirect(url_for('manage_entries'))
        
    except Exception as e:
        print(f"Error in import_data: {str(e)}")  # Debug
        print(f"Form data: {request.form}")  # Debug
        flash(f"Error importing data: {str(e)}", "danger")
        return redirect(url_for('import_entries'))

# Route: Admin Import CSV to Officials
@app.route('/import_officials')
@admin_required
def import_officials():
    raise NotImplementedError("This route is not implemented yet.")

# Route: Delete Entries and Checklists
@app.route('/purge_database', methods=['GET', 'POST'])
@admin_required
def purge_database():
    if request.method == 'POST':
        try:
            # Delete all inspection items first.
            num_items = InspectionItem.query.delete()
            # Delete all checklists.
            num_checklists = InspectionChecklist.query.delete()
            # Finally, delete all entries.
            num_entries = Entry.query.delete()
            db.session.commit()
            flash(
                f"Purged database: Deleted {num_entries} entries, {num_checklists} checklists, and {num_items} inspection items.",
                "success"
            )
        except Exception as e:
            db.session.rollback()
            flash("Error purging database: " + str(e), "danger")
        return redirect(url_for('wtac_dashboard'))
    # For a GET request, render a confirmation template.
    return render_template('purge_confirmation.html')

# Endpoint: Get total entries with vehicle_type 'W'
@app.route('/total_entries', methods=['GET'])
@login_required
def total_entries():
    total = Entry.query.filter_by(vehicle_type='W').count()
    return jsonify({'total_entries': total})

# Endpoint: Get total entries per class
@app.route('/class_entries', methods=['GET'])
@login_required
def class_entries():
    entries = db.session.query(Entry.class_type, db.func.count(Entry.class_type)) \
                        .filter_by(vehicle_type='W') \
                        .group_by(Entry.class_type) \
                        .all()
    return jsonify({'class_entries': [{row[0]: row[1]} for row in entries]})

# Endpoint: Get total entries without inspection reports
@app.route('/missing_inspections', methods=['GET'])
@login_required
def missing_inspections():
    # Query entries without matching checklists
    entries = Entry.query.filter(
        ~Entry.id.in_(db.session.query(InspectionChecklist.entry_id))
    ).all()
    return jsonify({'missing_inspections': [entry.id for entry in entries]})

# Endpoint: Get total entries not approved to start
@app.route('/not_approved_to_start', methods=['GET'])
@login_required
def not_approved_to_start():
    try:
        # Query entries where approved_to_start is FALSE
        not_approved_entries = db.session.query(Entry.id).join(InspectionChecklist).filter(
            InspectionChecklist.approved_to_start == False
        ).distinct().all()

        # Extract the IDs into a list
        not_approved_entry_ids = [entry[0] for entry in not_approved_entries]

        # Return the count and IDs of entries without approval to start
        return jsonify({
            'not_approved_to_start_count': len(not_approved_entry_ids),
            'not_approved_entries': not_approved_entry_ids
        })

    except Exception as e:
        # Handle any errors
        return jsonify({'error': str(e)})

# Endpoint: Get total entries with failed items
@app.route('/failed_items', methods=['GET'])
@login_required
def failed_items():
    try:
        # Query entries that have at least one failed item
        failed_entries = db.session.query(Entry.id).join(InspectionChecklist).join(InspectionItem).filter(
            InspectionItem.status == 'Fail'
        ).distinct().all()

        # Extract the IDs into a list
        failed_entry_ids = [entry[0] for entry in failed_entries]

        # Return the count and IDs of entries with failed items
        return jsonify({
            'failed_items_count': len(failed_entry_ids),
            'failed_entries': failed_entry_ids
        })

    except Exception as e:
        # Handle any errors
        return jsonify({'error': str(e)})

# Formula Ford Routes
@app.route('/formula_ford/round1')
@login_required
def formula_ford_round1():
    # Get the round 1 event
    event = FormulaFordEvent.query.filter_by(round_number=1).first_or_404()
    return render_template('formula_ford/round1.html', 
                           user=current_user, 
                           role=current_user.role,
                           event=event)

@app.route('/formula_ford/round2')
@login_required
def formula_ford_round2():
    # Get the round 2 event
    event = FormulaFordEvent.query.filter_by(round_number=2).first_or_404()
    return render_template('formula_ford/round2.html', 
                           user=current_user, 
                           role=current_user.role,
                           event=event)

@app.route('/formula_ford/round3')
@login_required
def formula_ford_round3():
    # Get the round 3 event
    event = FormulaFordEvent.query.filter_by(round_number=3).first_or_404()
    return render_template('formula_ford/round3.html', 
                           user=current_user, 
                           role=current_user.role,
                           event=event)

@app.route('/formula_ford/round4')
@login_required
def formula_ford_round4():
    # Get the round 4 event
    event = FormulaFordEvent.query.filter_by(round_number=4).first_or_404()
    return render_template('formula_ford/round4.html', 
                           user=current_user, 
                           role=current_user.role,
                           event=event)

@app.route('/formula_ford/round5')
@login_required
def formula_ford_round5():
    # Get the round 5 event
    event = FormulaFordEvent.query.filter_by(round_number=5).first_or_404()
    return render_template('formula_ford/round5.html', 
                           user=current_user, 
                           role=current_user.role,
                           event=event)

@app.route('/formula_ford/round6')
@login_required
def formula_ford_round6():
    # Get the round 6 event
    event = FormulaFordEvent.query.filter_by(round_number=6).first_or_404()
    return render_template('formula_ford/round6.html', 
                           user=current_user, 
                           role=current_user.role,
                           event=event)

@app.route('/formula_ford/round7')
@login_required
def formula_ford_round7():
    # Get the round 7 event
    event = FormulaFordEvent.query.filter_by(round_number=7).first_or_404()
    return render_template('formula_ford/round7.html', 
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
    record.qual_weight = float(qual_weight) if qual_weight and qual_weight.strip() else None
    record.qual_height = qual_height
    
    # Update race 1 data
    r1_weight = request.form.get(f'weight_r1_{competitor_id}')
    r1_height = request.form.get(f'height_r1_{competitor_id}')
    record.r1_weight = float(r1_weight) if r1_weight and r1_weight.strip() else None
    record.r1_height = r1_height
    
    # Update race 2 data
    r2_weight = request.form.get(f'weight_r2_{competitor_id}')
    r2_height = request.form.get(f'height_r2_{competitor_id}')
    record.r2_weight = float(r2_weight) if r2_weight and r2_weight.strip() else None
    record.r2_height = r2_height
    
    # Update race 3 data
    r3_weight = request.form.get(f'weight_r3_{competitor_id}')
    r3_height = request.form.get(f'height_r3_{competitor_id}')
    record.r3_weight = float(r3_weight) if r3_weight and r3_weight.strip() else None
    record.r3_height = r3_height
    
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
        record.qual_weight = float(qual_weight) if qual_weight and qual_weight.strip() else None
        record.qual_height = qual_height
        
        # Update race 1 data
        r1_weight = request.form.get(f'weight_r1_{competitor_id}')
        r1_height = request.form.get(f'height_r1_{competitor_id}')
        record.r1_weight = float(r1_weight) if r1_weight and r1_weight.strip() else None
        record.r1_height = r1_height
        
        # Update race 2 data
        r2_weight = request.form.get(f'weight_r2_{competitor_id}')
        r2_height = request.form.get(f'height_r2_{competitor_id}')
        record.r2_weight = float(r2_weight) if r2_weight and r2_weight.strip() else None
        record.r2_height = r2_height
        
        # Update race 3 data
        r3_weight = request.form.get(f'weight_r3_{competitor_id}')
        r3_height = request.form.get(f'height_r3_{competitor_id}')
        record.r3_weight = float(r3_weight) if r3_weight and r3_weight.strip() else None
        record.r3_height = r3_height
        
        saved_count += 1
    
    db.session.commit()
    flash(f'Successfully updated {saved_count} competitor records.', 'success')
    return redirect(url_for('weight_height_tracking', event_id=event_id))

@app.route('/formula_ford/events/<int:event_id>/technical_check')
@login_required
def technical_check(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    check_type = request.args.get('check_type', 'ecu')
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    
    # For each entry, load the competitor data
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        
        # Load any existing check for this competitor
        check = TechnicalCheck.query.filter_by(
            event_id=event_id,
            competitor_id=entry.competitor_id,
            check_type=check_type
        ).first()
        
        # If a check exists, parse the result for display in the template.
        # This needs to be specific to the check_type being loaded.
        if check and check.result:
            if check_type == 'ecu':
                # Use regex to find number and tune, handling missing values.
                num_match = re.search(r'Number:\s*([^,]+)', check.result)
                tune_match = re.search(r'Tune:\s*(.*)', check.result)
                check.ecu_number = num_match.group(1).strip() if num_match else ''
                check.ecu_tune = tune_match.group(1).strip() if tune_match else ''
            elif check_type == 'engine':
                check.engine_number = check.result
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
                         check_type=check_type)

@app.route('/formula_ford/events/<int:event_id>/technical_check/save', methods=['POST'])
@login_required
def save_technical_check(event_id):
    competitor_id = request.form.get('competitor_id')
    check_type = request.form.get('check_type')
    
    # Get the result based on the check type
    result = None
    if check_type == 'weight':
        result = request.form.get('weight', '')
    elif check_type == 'ecu':
        ecu_number = request.form.get('ecu_number', '')
        ecu_tune = request.form.get('ecu_tune', '')
        result = f"Number: {ecu_number}, Tune: {ecu_tune}"
    elif check_type == 'engine':
        result = request.form.get('engine_number', '')
    elif check_type == 'other':
        other_check_name = request.form.get('other_check_name', '')
        other_status = request.form.get('other_status', '')
        result = f"{other_check_name}: {other_status}"
    else:
        result = request.form.get(f'{check_type}_status', '')
    
    notes = request.form.get('notes', '').strip()
    
    # Check if record already exists
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

@app.route('/formula_ford/events/<int:event_id>/technical_requirements')
@login_required
def event_technical_requirements(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    requirements = EventTechnicalRequirements.query.filter_by(event_id=event_id).first()
    
    return render_template('formula_ford/technical_requirements.html',
                         event=event,
                         requirements=requirements)

@app.route('/formula_ford/events/<int:event_id>/technical_checks')
@login_required
def event_technical_checks(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    
    # Get all technical checks for this event
    technical_checks = TechnicalCheck.query.filter_by(event_id=event_id).all()
    
    # Group checks by competitor
    checks_by_competitor = {}
    for check in technical_checks:
        if check.competitor_id not in checks_by_competitor:
            checks_by_competitor[check.competitor_id] = []
        checks_by_competitor[check.competitor_id].append(check)
    
    # Get all competitors in this event
    entries = FormulaFordEventEntry.query.filter_by(event_id=event_id).all()
    for entry in entries:
        entry.competitor = db.session.get(FormulaFordCompetitor, entry.competitor_id)
        entry.checks = checks_by_competitor.get(entry.competitor_id, [])
    
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
    
    return render_template('formula_ford/technical_checks.html',
                         event=event,
                         entries=entries)

@app.route('/formula_ford/events/<int:event_id>/tyre_requirements')
@login_required
def event_tyre_requirements(event_id):
    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    requirements = EventTyreRequirements.query.filter_by(event_id=event_id).first()
    
    return render_template('formula_ford/tyre_requirements.html',
                         event=event,
                         requirements=requirements)

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
    
    for competitor_id in competitor_ids:
        # Get the result based on the check type
        result = ''
        notes = request.form.get(f'notes_{competitor_id}', '').strip()
        has_data = False

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
            other_check_name = request.form.get('other_check_name', '')
            other_status = request.form.get(f'other_status_{competitor_id}', '')
            # Only create a result if both name and status are present
            if other_check_name and other_status:
                result = f"{other_check_name}: {other_status}"
                has_data = True
            else:
                result = '' # Ensure result is empty if no data
        else:
            result = request.form.get(f'{check_type}_status_{competitor_id}', '')
            if result: has_data = True
        
        # Skip if no meaningful data for this competitor
        if not has_data and not notes:
            continue
            
        # Check if record already exists
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
        
        saved_count += 1
    
    try:
        db.session.commit()
        flash(f'{saved_count} {check_type.replace("_", " ").title()} checks saved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving checks: {str(e)}', 'error')
    
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

# Run the application
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    args = parser.parse_args()
    
    app.run(host='0.0.0.0', debug=True, port=args.port)
