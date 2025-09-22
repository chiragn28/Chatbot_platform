# auth_routes.py
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app import app, db
from models import User
import re
import uuid

def validate_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user.
    Expects JSON: { "email": "user@example.com", "password": "strongpassword123", "first_name": "John", "last_name": "Doe" }
    Returns JWT token and user info on success.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409

        # Create new user
        user = User()
        user.id = str(uuid.uuid4())  # Generate unique ID
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)  # Hash and set password

        db.session.add(user)
        db.session.commit()

        # Create JWT access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )

        # Return success response
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_image_url': user.profile_image_url
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during registration'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Log in an existing user.
    Expects JSON: { "email": "user@example.com", "password": "strongpassword123" }
    Returns JWT token and user info on success.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Verify password (returns False if user not found or password incorrect)
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401

        # Create JWT access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )

        # Return success response
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_image_url': user.profile_image_url
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during login'}), 500


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def profile():
    """
    Get the profile of the currently authenticated user.
    Requires valid JWT token in Authorization header or cookie.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_image_url': user.profile_image_url,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }), 200

    except Exception as e:
        current_app.logger.error(f"Profile fetch error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout endpoint (client-side token invalidation).
    In a JWT system, logout is handled client-side by deleting the token.
    This endpoint can be used to perform server-side cleanup if needed.
    Returns 200 to confirm successful logout.
    """
    return jsonify({'message': 'Successfully logged out'}), 200