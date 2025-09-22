# Database models for the chatbot platform
from datetime import datetime
from app import db
from sqlalchemy import UniqueConstraint, Text, ForeignKey
from sqlalchemy.orm import relationship
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from flask import g
from passlib.hash import pbkdf2_sha256 as hasher

# models.py

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)  # You can change this to Integer if preferred
    email = db.Column(db.String, unique=True, nullable=False)  # Make email required
    password_hash = db.Column(db.String(255), nullable=True)  # New field for password
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

    # Password management methods
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = hasher.hash(password)

    def check_password(self, password):
        """Check if provided password matches the hash."""
        return hasher.verify(password, self.password_hash) if self.password_hash else False

    @property
    def is_authenticated(self):
        return True



# Project/Agent model
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    system_prompt = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.String, ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    prompts = relationship("Prompt", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan")
    uploaded_files = relationship("UploadedFile", back_populates="project", cascade="all, delete-orphan")

# Prompt storage for projects
class Prompt(db.Model):
    __tablename__ = 'prompts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.Integer, ForeignKey('projects.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    project = relationship("Project", back_populates="prompts")

# Chat sessions for tracking conversations
class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), default="New Chat")
    project_id = db.Column(db.Integer, ForeignKey('projects.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    project = relationship("Project", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")

# Individual chat messages
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    chat_session_id = db.Column(db.Integer, ForeignKey('chat_sessions.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")

# File uploads for projects
class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    openai_file_id = db.Column(db.String(255), nullable=True)  # OpenAI file ID for API usage
    project_id = db.Column(db.Integer, ForeignKey('projects.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    project = relationship("Project", back_populates="uploaded_files")

def jwt_required_with_user(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}, 404
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper