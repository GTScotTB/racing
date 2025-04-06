from app import app, db
from models import User, FormulaFordEvent, FormulaFordCompetitor, FormulaFordEventEntry

with app.app_context():
    print("Checking database records:")
    
    # Check events
    events = FormulaFordEvent.query.all()
    print(f"\nEvents: {len(events)}")
    for event in events:
        print(f"  Event ID: {event.id}, Round: {event.round_number}, Location: {event.location}")
        # Get entries directly from FormulaFordEventEntry
        entries = FormulaFordEventEntry.query.filter_by(event_id=event.id).all()
        print(f"  Entries: {len(entries)}")
        for entry in entries:
            print(f"    Entry ID: {entry.id}, Competitor ID: {entry.competitor_id}")
    
    # Check competitors
    competitors = FormulaFordCompetitor.query.all()
    print(f"\nCompetitors: {len(competitors)}")
    for competitor in competitors:
        print(f"  Competitor ID: {competitor.id}, Name: {competitor.first_name} {competitor.last_name}, Car #: {competitor.car_number}")
    
    # Check entries
    entries = FormulaFordEventEntry.query.all()
    print(f"\nEntries: {len(entries)}")
    for entry in entries:
        print(f"  Entry ID: {entry.id}, Event ID: {entry.event_id}, Competitor ID: {entry.competitor_id}, Status: {entry.entry_status}")
        
    # Check users
    users = User.query.all()
    print(f"\nUsers: {len(users)}")
    for user in users:
        print(f"  User ID: {user.id}, Username: {user.username}, Role: {user.role}") 