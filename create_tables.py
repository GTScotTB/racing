from app import app, db
from models import EventTechnicalRequirements, CompetitorTechnicalRecord, EventTyreRequirements, CompetitorTyreRecord

with app.app_context():
    # Create the new tables
    db.create_all()
    print('Tables created successfully') 