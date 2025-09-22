import os
import logging
from datetime import timedelta
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Create instance folder if it does not exist
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)

# Configure database URL and fix for SQLite relative paths
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("sqlite:///") and not os.path.isabs(db_url[10:]):
    abs_path = os.path.join(instance_path, 'app.db')
    db_url = f"sqlite:///{abs_path}"
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security config
required_env_vars = ['SESSION_SECRET', 'DATABASE_URL', 'JWT_SECRET_KEY']
for var in required_env_vars:
    if not os.environ.get(var):
        logger.critical(f"Required environment variable {var} is not set")
        raise RuntimeError(f"Required environment variable {var} not set")

app.secret_key = os.environ['SESSION_SECRET']
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Session cookie security
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

csrf = CSRFProtect(app)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# JWT Config
app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'

jwt = JWTManager(app)

# Import models AFTER db is initialized
import models  

# JWT user loader callback
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return models.User.query.get(identity)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {"error": "Token has expired"}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {"error": "Invalid token"}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {"error": "Authorization token is missing"}, 401

# Context processor to inject current user
@app.context_processor
def inject_current_user():
    return dict(current_user=getattr(g, 'current_user', None))

# Create tables once (e.g. at app start)
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise
