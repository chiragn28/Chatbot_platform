# Chatbot Platform - Flask Web Application

## Project Overview
A comprehensive Flask-based chatbot platform with user authentication, project management, and OpenAI integration. Users can create AI agents, manage conversations, upload files, and interact with state-of-the-art language models.

## Recent Changes
- **September 20, 2025**: Complete chatbot platform implementation with all core features
  - Set up Flask application with PostgreSQL database integration
  - Implemented Replit authentication for secure user login
  - Created comprehensive project/agent management system
  - Built real-time chat interface with OpenAI GPT-5 integration
  - Added file upload functionality with OpenAI Files API support
  - Developed responsive web interface with Bootstrap 5
  - Implemented RESTful API endpoints for all functionality

## User Preferences
- Platform: Flask (Python web framework)
- Database: PostgreSQL with SQLAlchemy ORM
- Authentication: Replit Auth (supports Google, GitHub, X, Apple, email/password)
- AI Integration: OpenAI GPT-5 with chat completions API
- Frontend: Bootstrap 5 with responsive design
- File Management: Local storage with OpenAI Files API integration

## Project Architecture

### Backend Structure
- **app.py**: Flask application configuration and database setup
- **models.py**: SQLAlchemy database models for users, projects, chats, messages, prompts, and files
- **replit_auth.py**: Authentication integration with Replit OAuth2 system
- **routes.py**: All Flask routes and API endpoints
- **openai_client.py**: OpenAI API integration for chat and file operations
- **main.py**: Application entry point

### Database Schema
- **Users**: Managed by Replit Auth integration
- **Projects**: AI agents with custom system prompts
- **Prompts**: Reusable prompt templates for projects
- **ChatSessions**: Conversation containers
- **ChatMessages**: Individual chat messages (user/assistant)
- **UploadedFiles**: File management with OpenAI integration
- **OAuth**: Authentication token storage

### Key Features Implemented
1. **Authentication System**
   - Secure login/logout with Replit Auth
   - Session management and token refresh
   - User profile integration

2. **Project Management**
   - Create/edit/delete AI agent projects
   - Custom system prompts for agent behavior
   - Project statistics and management dashboard

3. **Chat Interface**
   - Real-time conversations with AI agents
   - Chat session management and history
   - Message persistence and retrieval

4. **File Upload System**
   - Local file storage with security validation
   - OpenAI Files API integration for AI processing
   - Support for multiple file formats (TXT, PDF, images, documents)

5. **Prompt Management**
   - Create and store reusable prompt templates
   - Copy-to-clipboard functionality
   - Project-specific prompt organization

6. **Responsive Web Interface**
   - Bootstrap 5 responsive design
   - Professional UI with proper navigation
   - Error handling and user feedback

### API Endpoints
- `GET /`: Landing page or dashboard (based on auth status)
- `GET /dashboard`: User dashboard with project overview
- `GET/POST /project/new`: Create new AI agent project
- `GET /project/<id>`: Project detail and management
- `GET/POST /project/<id>/edit`: Edit project settings
- `GET /chat/<project_id>`: Chat interface
- `POST /api/chat/<project_id>/<session_id>`: Send message API
- `GET/POST /project/<id>/upload`: File upload management
- `GET/POST /project/<id>/prompts/new`: Create prompt templates
- `POST /api/project/<id>/delete`: Delete project API

### Security Features
- CSRF protection with Flask-WTF
- Secure file upload with filename sanitization
- SQL injection prevention with SQLAlchemy ORM
- Session-based authentication with token refresh
- File type validation and size limits

### Deployment Configuration
- Configured for Replit hosting environment
- Environment variables for database and API keys
- Production-ready error handling
- Proper cache headers for development

## Current Status
✅ **COMPLETED**: Full chatbot platform with all requested features
- User authentication and session management
- Project/agent creation and management
- Interactive chat interface with OpenAI integration
- File upload functionality
- Prompt template system
- Responsive web interface
- Database persistence
- RESTful API design
- Error handling and security measures

## Next Steps (Future Enhancements)
- Analytics and usage tracking for projects
- Chat history search and filtering
- Project sharing and collaboration features
- Advanced file management with preview capabilities
- API rate limiting and request throttling
- Admin dashboard for user management
- Backup and data export functionality
- Mobile app development
- Integration with additional LLM providers

## Technical Requirements Met
✅ Authentication: JWT/OAuth2 with Replit Auth  
✅ User Registration: Automatic with Replit Auth  
✅ Project Management: Full CRUD operations  
✅ Prompt Storage: Database persistence  
✅ Chat Interface: Real-time with OpenAI API  
✅ File Upload: OpenAI Files API integration  
✅ Scalability: Multi-user concurrent support  
✅ Security: Protected routes and data validation  
✅ Extensibility: Modular architecture  
✅ Performance: Optimized database queries  
✅ Reliability: Comprehensive error handling