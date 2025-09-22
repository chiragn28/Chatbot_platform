from flask import render_template, request, redirect, url_for, flash, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from datetime import timedelta
from app import app, db
from models import User
import re
import uuid

def validate_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/auth/login', methods=['GET', 'POST'])
def web_login():
    """Web-based login page and handler."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        # Create JWT access token
        access_token = create_access_token(
            identity=user.id, 
            expires_delta=timedelta(hours=24)
        )
        
        # Set JWT in cookie and redirect
        response = make_response(redirect(url_for('dashboard')))
        response.set_cookie(
            'access_token_cookie', 
            access_token, 
            max_age=24*60*60,
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        flash(f'Welcome back, {user.first_name or user.email}!', 'success')
        return response
    
    return render_template('login.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def web_register():
    """Web-based registration page and handler."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        
        # Validate input
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Invalid email format', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login instead.', 'error')
            return render_template('register.html')
        
        try:
            # Create new user
            user = User()
            user.id = str(uuid.uuid4())
            user.email = email
            user.firstname = firstname
            user.lastname = lastname
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Create JWT access token
            access_token = create_access_token(
                identity=user.id, 
                expires_delta=timedelta(hours=24)
            )
            
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie(
                'access_token_cookie', 
                access_token, 
                max_age=24*60*60,
                httponly=True,
                secure=False,
                samesite='Lax'
            )
            flash(f'Registration successful! Welcome, {firstname or email}!', 'success')
            return response
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/auth/logout')
@jwt_required()
def web_logout():
    """Web-based logout handler."""
    response = make_response(redirect(url_for('index')))
    unset_jwt_cookies(response)
    flash('You have been logged out successfully', 'success')
    return response
