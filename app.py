# Flask chatbot platform with authentication and OpenAI integration
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
import os
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)

# Validate required environment variables
required_env_vars = ["SESSION_SECRET", "DATABASE_URL"]
for var in required_env_vars:
    if not os.environ.get(var):
        raise RuntimeError(f"Required environment variable {var} is not set")

app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Security configurations for session cookies
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize database
db = SQLAlchemy(app, model_class=Base)

# Create tables
# Need to put this in module-level to make it work with Gunicorn.
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    logging.info("Database tables created")