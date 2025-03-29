from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from models import db,User, Entry, InspectionChecklist, InspectionItem, ChecklistItem, Officials, Roles
from sqlalchemy import or_, func, Integer, text
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


# Initialize Flask app
app = Flask(__name__)

# Secret Key For Flash Messages
app.secret_key = os.getenv('FLASK_SECRET_KEY', '85d85388ef8d36d589777628f0c6a3c6')

# Configure the app with SQLAlchemy settings
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

#Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Fetch user by ID


# Initialize SQLAlchemy with Flask
db.init_app(app)

# Enable Foreign Key Constraints in SQLite
@app.before_request
def enable_foreign_keys():
    if 'sqlite' in SQLALCHEMY_DATABASE_URI:
        with db.engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys=ON"))

# Route: Login (GET AND POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # Replace with hashed password check
            login_user(user)
            return redirect(url_for('index'))  # Redirect to the dashboard after login
        else:
            return "Invalid credentials. Please try again.", 401
        
    return render_template('login.html')  # Render login form

# Route: Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))  # Redirect to login page after logout

# Route: Home 
@app.route('/')
@login_required
def index():
    user_role = current_user.role  # Get the role of the logged-in user
    return render_template('index.html', user=current_user, role=user_role)  # Render the home page

# Route: Add Entry (GET)
@app.route('/add_entry', methods=['GET'])
def show_add_entry():
    # Define valid classes or fetch them from your system
    classes = [
        "Tuner", "Clubsprint", "Open", "Pro Open",
        "Pro Am", "Pro", "Flying 500", "Demo"
    ]
    return render_template('add_entry.html', classes=classes)  # Pass classes to the template

# Route: Add Entry (POST)
@app.route('/add_entry', methods=['POST'])
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
        checklist = db.session.get(InspectionChecklist, checklist_id)

        if not checklist:
            return jsonify({'error': "Checklist not found!"}), 404

        # Fetch associated entry
        entry = Entry.query.get(checklist.entry_id)
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
def view_checklist2():
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
        checklist = InspectionChecklist.query.get(checklist_id)

        if not checklist:
            return jsonify({'error': "Checklist not found!"}), 404

        # Fetch associated entry
        entry = Entry.query.get(checklist.entry_id)
        items = InspectionItem.query.filter_by(checklist_id=checklist.id).all()

        return render_template(
            'checklist2.html',
            checklist=checklist,
            items=items,
            entry=entry,
            scrutineers=scrutineers,
            current_date=datetime.now().strftime('%Y-%m-%d'),
            current_time=datetime.now().strftime('%H:%M:%S')
        )    
# route: update checklist 2

@app.route('/update_checklist2', methods=['POST'])
def update_checklist2():
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
        return redirect(url_for('view_checklist2', checklist_id=checklist_id))
                            
# Route: Vehicle Weights
@app.route('/vehicle_weights')
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

# Route: Print Scrut
@app.route('/scrutineers')
def scrutineers_list():
    scrutineers = Officials.query.filter_by(role="Scrutineer").all()
    return render_template('scrutineers.html', scrutineers=scrutineers)

# Route: Add Officals
@app.route('/add_official', methods=['GET', 'POST'])
def add_official():
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
            return render_template('add_official.html', error="Failed to add official. Please try again.", roles=roles)

    # Handle GET request
    roles = Roles.query.all()
    return render_template('add_official.html', roles=roles)

# Route: Admin View/Delete Entries

# Route: Admin View/Delete Checklists

# Route: Admin View/Delete Officials

# Route: Admin Import CSV to Entries

# Route: Admin Import CSV to Officials

# Endpoint: Get total entries with vehicle_type 'W'
@app.route('/total_entries', methods=['GET'])
def total_entries():
    total = Entry.query.filter_by(vehicle_type='W').count()
    return jsonify({'total_entries': total})

# Endpoint: Get total entries per class
@app.route('/class_entries', methods=['GET'])
def class_entries():
    entries = db.session.query(Entry.class_type, db.func.count(Entry.class_type)) \
                        .filter_by(vehicle_type='W') \
                        .group_by(Entry.class_type) \
                        .all()
    return jsonify({'class_entries': [{row[0]: row[1]} for row in entries]})

# Endpoint: Get total entries without inspection reports
@app.route('/missing_inspections', methods=['GET'])
def missing_inspections():
    # Query entries without matching checklists
    entries = Entry.query.filter(
        ~Entry.id.in_(db.session.query(InspectionChecklist.entry_id))
    ).all()
    return jsonify({'missing_inspections': [entry.id for entry in entries]})

# Endpoint: Get total entries not approved to start
@app.route('/not_approved_to_start', methods=['GET'])
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
# END OF WORLD TIME ATTACK PROGRAMMING

# Route: Formula Ford Home

# Route: Formula Ford Compeditors

# Route: Formula Ford Engines

# Route: Formula Ford ECU

# Route: Formula Ford Tyres

# Route: Formula Ford Weights

# Route: Formula Ford Height

# Route: Formula Ford Dash Data

# Route: Formula Ford Eligibility Test

# Route: Formula Ford View Checks

# Route: Formula Ford Import via CSV

# Route: Formula Ford Weekend Report

# Route: Formula Ford Issue Tracking

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Enable debug mode for development