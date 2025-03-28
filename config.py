# config.py
import os

# SQLAlchemy Database Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Get the base directory of the app
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'DataBase', 'racing.db')}"  # Path to SQLite database
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Additional configurations
DEBUG = True
SECRET_KEY = 'Ajbseb14'