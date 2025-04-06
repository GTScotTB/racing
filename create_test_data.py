from app import app, db
from models import User, FormulaFordEvent, FormulaFordCompetitor, FormulaFordEventEntry
from datetime import date
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('password'),
            role='admin'
        )
        db.session.add(admin)
        print("Created admin user")
    
    # Create event
    if not FormulaFordEvent.query.filter_by(round_number=1).first():
        event = FormulaFordEvent(
            round_number=1,
            location="Sydney Motorsport Park",
            event_date=date(2025, 5, 1)
        )
        db.session.add(event)
        print("Created test event")
    
    # Create competitor
    if not FormulaFordCompetitor.query.filter_by(car_number=1).first():
        competitor = FormulaFordCompetitor(
            first_name="John",
            last_name="Doe",
            team_association="Test Team",
            vehicle_make="Mygale",
            vehicle_type="Formula Ford",
            car_number=1
        )
        db.session.add(competitor)
        print("Created test competitor")
    
    db.session.commit()
    
    # Now that we have the event and competitor, create an entry
    event = FormulaFordEvent.query.filter_by(round_number=1).first()
    competitor = FormulaFordCompetitor.query.filter_by(car_number=1).first()
    
    if event and competitor and not FormulaFordEventEntry.query.filter_by(event_id=event.id, competitor_id=competitor.id).first():
        entry = FormulaFordEventEntry(
            event_id=event.id,
            competitor_id=competitor.id,
            entry_status="Confirmed",
            notes="Test entry"
        )
        db.session.add(entry)
        db.session.commit()
        print("Created test event entry")
    
    print("Test data created successfully!") 