import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_secure_random_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///racing/racing.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False