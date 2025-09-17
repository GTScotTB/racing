from app import app, db
from models import FormulaFordEvent
from datetime import datetime
from flask import request, redirect, url_for, flash
from flask_login import login_required

def add_events():
    events = [
        {
            'round_number': 1,
            'location': 'Round 1',
            'event_date': datetime(2024, 5, 16)
        },
        {
            'round_number': 2,
            'location': 'Round 2',
            'event_date': datetime(2024, 6, 6)
        },
        {
            'round_number': 3,
            'location': 'Round 3',
            'event_date': datetime(2024, 7, 25)
        },
        {
            'round_number': 4,
            'location': 'Round 4',
            'event_date': datetime(2024, 8, 22)
        },
        {
            'round_number': 5,
            'location': 'Round 5',
            'event_date': datetime(2024, 9, 19)
        },
        {
            'round_number': 6,
            'location': 'Round 6',
            'event_date': datetime(2024, 10, 3)
        }
    ]

    with app.app_context():
        # Clear existing events
        FormulaFordEvent.query.delete()
        
        # Add new events
        for event_data in events:
            event = FormulaFordEvent(**event_data)
            db.session.add(event)
        
        # Commit changes
        db.session.commit()
        print("Events added successfully!")

@app.route('/update_formula_ford_event', methods=['POST'])
@login_required
def update_formula_ford_event():
    event_id = request.form.get('event_id')
    location = request.form.get('location')
    date = request.form.get('date')

    event = db.session.get(FormulaFordEvent, event_id) or abort(404)
    event.location = location
    event.event_date = date

    db.session.commit()
    flash('Event updated successfully!', 'success')
    return redirect(url_for('manage_formula_ford_events'))

if __name__ == '__main__':
    add_events() 