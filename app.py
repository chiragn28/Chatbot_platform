"""
Flask chatbot platform with authentication and OpenAI/OpenRouter integration.
Handles app configuration, security, database, and JWT setup.
"""

import os
import logging
from datetime import timedelta
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import JWTManager

from dotenv import load_dotenv
load_dotenv()  # <-- Add this to ensure .env variables are loaded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)

# Create instance folder BEFORE SQLAlchemy tries to connect
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)

# Dynamically fix DATABASE_URL if using SQLite and not absolute
db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
    abs_db_path = os.path.join(instance_path, "app.db")
    db_url = f"sqlite:///{abs_db_path}"
    os.environ["DATABASE_URL"] = db_url

# Validate required environment variables
required_env_vars = ["SESSION_SECRET", "DATABASE_URL", "JWT_SECRET_KEY"]
for var in required_env_vars:
    if not os.environ.get(var):
        logger.critical(f"Required environment variable {var} is not set")
        raise RuntimeError(f"Required environment variable {var} is not set")

app.secret_key = os.environ["SESSION_SECRET"]
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Security configurations for session cookies
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize database
db = SQLAlchemy(app, model_class=Base)

import models  # <-- Only after db is defined

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'

jwt = JWTManager(app)

# Global JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {"error": "Token has expired"}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {"error": "Invalid token"}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {"error": "Authorization token is missing"}, 401

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    from models import User
    return User.query.get(identity)

@app.context_processor
def inject_current_user():
    return dict(current_user=getattr(g, "current_user", None))

# Create database tables (only once, after models are imported)
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise