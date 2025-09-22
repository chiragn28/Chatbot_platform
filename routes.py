# Flask routes for the chatbot platform
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    session, render_template, redirect, url_for, request, 
    jsonify, flash, current_app, g, make_response
)

from app import app, db
from models import User, Project, Prompt, ChatSession, ChatMessage, UploadedFile
from openai_client import chat_with_openai, upload_file_to_openai
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity, set_access_cookies, verify_jwt_in_request
from models import User, jwt_required_with_user
from app import csrf
import pdfplumber
import docx

# Configure file upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_auth():
    """Check if user is authenticated via JWT"""
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
        if current_user_id:
            user = User.query.get(current_user_id)
            if user:
                g.current_user = user
                return True
    except:
        pass
    return False

@app.before_request
def load_user():
    """Load user before each request"""
    g.current_user = None
    check_auth()

@app.route('/')
def index():
    """Landing page - shows login or dashboard based on auth status"""
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
        if current_user_id:
            return redirect(url_for('dashboard'))
    except:
        pass
    return render_template('landing.html')

@app.route('/dashboard')
@jwt_required_with_user
def dashboard():
    """Main dashboard for logged-in users"""
    projects = Project.query.filter_by(user_id=g.current_user.id).all()
    return render_template('dashboard.html', projects=projects, user=g.current_user)

@app.route('/projects')
@jwt_required_with_user
def projects():
    """List all user projects"""
    user_projects = Project.query.filter_by(user_id=g.current_user.id).all()
    return render_template('projects.html', projects=user_projects)

@app.route('/project/new', methods=['GET', 'POST'])
@jwt_required_with_user
def create_project():
    """Create a new project/agent"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        system_prompt = request.form.get('system_prompt', '')
        
        if not name:
            flash('Project name is required', 'error')
            return render_template('create_project.html')
        
        project = Project(
            name=name,
            description=description,
            system_prompt=system_prompt,
            user_id=g.current_user.id
        )
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('create_project.html')

@app.route('/project/<int:project_id>')
@jwt_required_with_user
def project_detail(project_id):
    """Project detail and management page"""
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
    chat_sessions = ChatSession.query.filter_by(project_id=project_id).order_by(ChatSession.updated_at.desc()).all()
    return render_template('project_detail.html', project=project, chat_sessions=chat_sessions)

@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@jwt_required_with_user
def edit_project(project_id):
    """Edit project settings"""
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
    
    if request.method == 'POST':
        project.name = request.form.get('name', project.name)
        project.description = request.form.get('description', project.description)
        project.system_prompt = request.form.get('system_prompt', project.system_prompt)
        project.updated_at = datetime.now()
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('edit_project.html', project=project)

@app.route('/project/<int:project_id>/prompts')
@jwt_required_with_user
def project_prompts(project_id):
    """Manage project prompts"""
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
    prompts = Prompt.query.filter_by(project_id=project_id).all()
    return render_template('project_prompts.html', project=project, prompts=prompts)

@app.route('/project/<int:project_id>/prompts/new', methods=['GET', 'POST'])
@jwt_required_with_user
def create_prompt(project_id):
    """Create a new prompt for a project"""
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return render_template('create_prompt.html', project=project)
        
        prompt = Prompt(
            title=title,
            content=content,
            project_id=project_id
        )
        db.session.add(prompt)
        db.session.commit()
        
        flash('Prompt created successfully!', 'success')
        return redirect(url_for('project_prompts', project_id=project_id))
    
    return render_template('create_prompt.html', project=project)

@app.route('/chat/<int:project_id>')
@jwt_required_with_user
def chat_interface(project_id):
    """Chat interface for a project"""
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
    
    # Get or create a chat session
    session_id = request.args.get('session_id')
    if session_id:
        chat_session = ChatSession.query.filter_by(id=session_id, project_id=project_id).first_or_404()
    else:
        # Create new chat session
        chat_session = ChatSession(
            title="New Chat",
            project_id=project_id
        )
        db.session.add(chat_session)
        db.session.commit()
        return redirect(url_for('chat_interface', project_id=project_id, session_id=chat_session.id))
    
    messages = ChatMessage.query.filter_by(chat_session_id=chat_session.id).order_by(ChatMessage.created_at.asc()).all()
    return render_template('chat.html', project=project, chat_session=chat_session, messages=messages)

@csrf.exempt
@app.route('/api/chat/<int:project_id>/<int:session_id>', methods=['POST'])
def send_message(project_id, session_id):
    """API endpoint to send a message and get AI response"""
    try:
        # Check authentication
        if not check_auth():
            return jsonify({'error': 'Authentication required'}), 401
        
        project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
        chat_session = ChatSession.query.filter_by(id=session_id, project_id=project_id).first_or_404()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Save user message
        user_msg = ChatMessage(
            role='user',
            content=user_message,
            chat_session_id=session_id
        )
        db.session.add(user_msg)
        
        # Get conversation history
        previous_messages = ChatMessage.query.filter_by(
            chat_session_id=session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # File processing
        uploaded_files = UploadedFile.query.filter_by(project_id=project_id).all()
        file_summaries = []
        for f in uploaded_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
            try:
                # TXT files
                if f.file_type in ['text/plain', 'txt']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read(2048)
                        file_summaries.append(f"File '{f.original_filename}':\n{content}\n")
                # PDF files
                elif f.file_type in ['application/pdf', 'pdf']:
                    with pdfplumber.open(file_path) as pdf:
                        text = ''
                        for page in pdf.pages[:3]:
                            text += page.extract_text() or ''
                        file_summaries.append(f"File '{f.original_filename}' (PDF):\n{text[:2048]}\n")
                # DOCX files
                elif f.file_type in [
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/msword', 'docx', 'doc'
                ]:
                    doc = docx.Document(file_path)
                    text = '\n'.join([para.text for para in doc.paragraphs])
                    file_summaries.append(f"File '{f.original_filename}' (DOCX):\n{text[:2048]}\n")
                # Images and others
                elif f.file_type.startswith('image/'):
                    file_summaries.append(f"File '{f.original_filename}' is an image. (Image content not extracted.)\n")
                else:
                    file_summaries.append(f"File '{f.original_filename}' is of type {f.file_type}. Content extraction not supported.\n")
            except Exception as e:
                current_app.logger.warning(f"Could not read file {f.filename}: {e}")
        files_context = "\n".join(file_summaries) if file_summaries else ""

        # Prepare messages for OpenAI
        messages = []
        if files_context:
            messages.append({
                'role': 'system',
                'content': f"The following files are available for this project:\n{files_context}"
            })
        for msg in previous_messages:
            messages.append({
                'role': msg.role,
                'content': msg.content
            })
        messages.append({'role': 'user', 'content': user_message})
        
        # Generate AI response
        try:
            ai_response = chat_with_openai(messages, project.system_prompt)
        except Exception as openai_error:
            db.session.rollback()
            current_app.logger.error(f"OpenAI API error: {openai_error}", exc_info=True)
            error_message = f"AI error: {openai_error}"
            return jsonify({'error': error_message}), 503
        
        # Save AI response
        ai_msg = ChatMessage(
            role='assistant',
            content=ai_response,
            chat_session_id=session_id
        )
        db.session.add(ai_msg)
        chat_session.updated_at = datetime.now()
        if chat_session.title == "New Chat" and len(previous_messages) == 0:
            title_words = user_message.split()[:5]
            chat_session.title = ' '.join(title_words) + ('...' if len(title_words) == 5 else '')
        db.session.commit()
        
        return jsonify({
            'user_message': {
                'id': user_msg.id,
                'content': user_message,
                'timestamp': user_msg.created_at.isoformat()
            },
            'ai_response': {
                'id': ai_msg.id,
                'content': ai_response,
                'timestamp': ai_msg.created_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({'error': f'Unexpected error: {e}'}), 500

@app.route('/project/<int:project_id>/upload', methods=['GET', 'POST'])
@jwt_required_with_user
def upload_file(project_id):
    """Upload files to a project"""
    project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            file.save(file_path)
            
            try:
                # Upload to OpenAI
                openai_file_id = upload_file_to_openai(file_path)
                
                # Save file record
                uploaded_file = UploadedFile(
                    filename=filename,
                    original_filename=file.filename,
                    file_size=os.path.getsize(file_path),
                    file_type=file.content_type or 'unknown',
                    openai_file_id=openai_file_id,
                    project_id=project_id
                )
                db.session.add(uploaded_file)
                db.session.commit()
                
                flash('File uploaded successfully!', 'success')
                
            except Exception as e:
                current_app.logger.error(f"File upload error: {e}")
                flash('Failed to process file upload', 'error')
                # Clean up local file if OpenAI upload failed
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash('File type not allowed', 'error')
    
    files = UploadedFile.query.filter_by(project_id=project_id).all()
    return render_template('upload_file.html', project=project, files=files)

@app.route('/api/project/<int:project_id>/delete', methods=['POST'])
@csrf.exempt
@jwt_required_with_user
def delete_project(project_id):
    """Delete a project and all associated data"""
    try:
        project = Project.query.filter_by(id=project_id, user_id=g.current_user.id).first_or_404()
        
        # Delete associated files from OpenAI (if any)
        for uploaded_file in project.uploaded_files:
            try:
                if uploaded_file.openai_file_id:
                    # Note: OpenAI file deletion would go here
                    pass
                # Delete local file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting file: {e}")
        
        # Delete project (cascade will handle related records)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Project deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Project deletion error: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete project'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
