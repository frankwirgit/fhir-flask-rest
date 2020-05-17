"""
Global Configuration for Application
"""
import os
from dotenv import load_dotenv

#Load the .env file to get environment variables
#For example: FLASK_APP=service:app

load_dotenv()

# Get configuration from environment
# DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///../development.db")
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret for session management
#SECRET_KEY = os.getenv("SECRET_KEY", "s3cr3t-key-shhhh")
