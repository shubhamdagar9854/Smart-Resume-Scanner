# 🚀 Resume Scanner

🤖 **AI-powered resume analysis and job matching system using Google Gemini AI.** Automatically analyzes resumes, extracts skills, and matches candidates with job descriptions.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange.svg)](https://ai.google.dev/gemini)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 📄 **Resume Upload & Analysis** - Upload PDF/DOCX files for AI analysis
- 🧠 **Skill Extraction** - Automatically identifies candidate skills
- 🎯 **Job Matching** - Matches resumes with job descriptions
- 📊 **Smart Scoring** - Ranks candidates based on compatibility
- 🔄 **Learning System** - Improves accuracy over time
- 🎨 **Modern Interface** - Clean and responsive UI design

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.9 or higher
- Google Gemini API Key
- Git installed

### 🔧 Installation

```bash
# 1. Clone the repository
git clone https://github.com/shubhamdagar9854/Smart-Resume-Scanner.git
cd Smart-Resume-Scanner

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup database
python database.py

# 6. Run the application
python app.py
```

### ⚙️ Setup Required

1. **🔑 Get Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)
2. **📝 Create `.env` file** with your API key:
   ```bash
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
   ⚠️ **IMPORTANT**: Never commit `.env` file to GitHub or share your API key!
3. **🔒 Security**: The `.env` file is already in `.gitignore` to protect your API key

### 🎯 How to Use

1. **🌐 Open browser** and go to `http://localhost:5000`
2. **📄 Upload resume** (PDF or DOCX format)
3. **📊 View analysis** - AI will extract:
   - 🧠 Skills and experience
   - 🎓 Education details  
   - 📝 Summary and recommendations
4. **💼 Create job posting** to match candidates
5. **📈 View matches** with compatibility scores

## 🛠 Tech Stack

- 🐍 **Backend**: Python Flask
- 🤖 **AI**: Google Gemini API
- 🗄️ **Database**: SQLite (default) / PostgreSQL
- 📄 **File Processing**: PDF/DOCX parsing
- 🎨 **Frontend**: HTML/CSS/JavaScript

## 📋 Requirements

- 🐍 Python 3.9 or higher
- 🔑 Google Gemini API Key
- 💾 2GB+ RAM recommended
- 💿 500MB+ disk space

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Docker (Optional)
```bash
docker build -t resume-scanner .
docker run -p 5000:5000 resume-scanner
```

### Production Deployment
- ✅ **Heroku Ready**
- ✅ **Render Compatible**
- ✅ **Railway Support**
- ✅ **Docker Support**

## 🔧 Troubleshooting

### ❌ Common Issues

- **🔑 API Key Error**: Make sure `.env` file contains valid Google API key
- **📄 File Upload Error**: Check file format (PDF/DOCX only) and size limit
- **🗄️ Database Error**: Run `python database.py` to initialize database
- **🌐 Port Error**: Check if port 5000 is already in use

### 💡 Quick Fixes

```bash
# Reset database
python database.py

# Check API key
echo $GOOGLE_API_KEY

# Kill port process (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Kill port process (Linux/Mac)
lsof -ti:5000 | xargs kill -9
```

## 📞 Support

- 🐛 **GitHub Issues**: [Report bugs here](https://github.com/shubhamdagar9854/Smart-Resume-Scanner/issues)
- 📧 **Email**: shubhamdagar9854@gmail.com
- 💬 **Discussions**: [Join our community](https://github.com/shubhamdagar9854/Smart-Resume-Scanner/discussions)

## 🌟 Show Your Support

If this project helped you, please give it a ⭐ on GitHub!

---

**Made with ❤️ by Shubham Dagar**

## ✨ Task Manager Pro - Complete Project & Task Management System

A comprehensive task management system with user authentication, project collaboration, and team management capabilities.

## 🚀 Features

### 🔐 **Authentication System**
- **User Registration & Login**: Secure signup/login with password hashing
- **Session Management**: Persistent user sessions with role-based access
- **Role-Based Access Control**: Admin, Manager, and User roles
- **Password Security**: SHA-256 password hashing for security

### 📁 **Project Management**
- **Create Projects**: Start new projects with descriptions and team assignments
- **Project Dashboard**: View all projects with status and progress tracking
- **Team Collaboration**: Add team members and assign roles
- **Project Ownership**: Clear ownership and permission management

### 📋 **Task Management**
- **Task Creation**: Create tasks with title, description, priority, and due dates
- **Task Assignment**: Assign tasks to team members with status tracking
- **Status Tracking**: Pending, In Progress, Completed status management
- **Priority Levels**: High, Medium, Low priority system
- **Due Date Management**: Calendar-based task scheduling
- **Overdue Alerts**: Automatic overdue task notifications

### 📊 **Dashboard & Analytics**
- **Personal Dashboard**: Task statistics and progress overview
- **Project Analytics**: Project completion rates and team performance
- **Task Statistics**: Total, completed, pending, in-progress tasks
- **Overdue Monitoring**: Real-time overdue task tracking
- **Team Performance**: Individual and team productivity metrics

### 🔗 **REST APIs**
- **User Management**: `/api/users` - User CRUD operations
- **Project APIs**: `/api/projects` - Project management endpoints
- **Task APIs**: `/api/tasks` - Complete task management
- **Team APIs**: `/api/teams` - Team collaboration endpoints
- **Validation**: Input validation and error handling
- **Security**: API authentication and authorization

## 🛠️ Technology Stack

### Backend
- **Framework**: Python Flask
- **Database**: SQLite with relational schema
- **Authentication**: Session-based auth with password hashing
- **API**: RESTful APIs with JSON responses
- **Security**: Input validation and SQL injection protection

### Frontend
- **Templates**: Jinja2 HTML templates
- **Styling**: Custom CSS with responsive design
- **JavaScript**: Vanilla JS for interactivity
- **UI/UX**: Modern, intuitive interface design

### Database Schema
- **users**: User accounts with roles and profiles
- **projects**: Project information with ownership
- **teams**: Team structure and member assignments
- **tasks**: Task details with status and assignments
- **team_members**: User-team relationships with roles

## 📋 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- SQLite3 database

### Quick Start
1. **Clone the repository**:
   ```bash
   git clone https://github.com/shubhamdagar9854/Task-Manager-Pro.git
   cd Task-Manager-Pro
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database**:
   ```bash
   python -c "from database import init_db; init_db()"
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the application**:
   - Open browser and navigate to `http://localhost:5000`
   - Create account and start managing tasks!

## 🔐 Default Access

### Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: `http://localhost:5000/admin/login`

### User Registration
- **Signup**: `http://localhost:5000/signup`
- **Login**: `http://localhost:5000/login`

## 📱 Application Features

### User Experience
- **Dashboard**: Personal task overview with statistics
- **Project View**: All projects with progress tracking
- **Task Management**: Create, assign, and update tasks
- **Team Collaboration**: Work together with team members
- **Calendar View**: Task scheduling and due date management

### Admin Experience
- **User Management**: Manage all user accounts and roles
- **Project Oversight**: Monitor all projects and teams
- **Task Analytics**: Comprehensive task and performance analytics
- **System Settings**: Configure application behavior

## 🗂️ Project Structure

```bash
Task-Manager-Pro/
├── app.py                    # Main Flask application
├── database.py                # Database operations and models
├── templates/                  # HTML templates
│   ├── signup.html             # User registration
│   ├── login.html              # User login
│   ├── dashboard.html           # User dashboard
│   ├── projects.html            # Project management
│   ├── tasks.html              # Task management
│   └── admin_dashboard.html     # Admin interface
├── static/                    # CSS and JavaScript files
├── uploads/                   # File upload storage
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables
```bash
FLASK_ENV=development          # or 'production' for deployment
SECRET_KEY=your-secret-key     # Flask session secret
UPLOAD_FOLDER=./uploads         # File upload directory
DATABASE_PATH=./tasks.db        # Database file path
```

### Database Configuration
- **Development**: SQLite database `./tasks.db`
- **Production**: Configurable via environment variables
- **Tables**: users, projects, teams, tasks, team_members

## 🚀 Deployment

### Production Setup
1. **Environment Variables**: Configure production environment variables
2. **Database**: Ensure proper database file permissions
3. **Security**: Use strong SECRET_KEY in production
4. **Web Server**: Use production WSGI server (Gunicorn, uWSGI)

### Docker Support
```bash
# Build Docker image
docker build -t task-manager-pro .

# Run container
docker run -p 5000:5000 task-manager-pro
```

## 📊 API Documentation

### Authentication Endpoints
- `POST /signup` - User registration
- `POST /login` - User authentication
- `POST /logout` - User logout

### Project Management APIs
- `GET /api/projects` - List user projects
- `POST /api/projects` - Create new project
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project

### Task Management APIs
- `GET /api/tasks/<project_id>` - List project tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/<id>` - Update task status
- `DELETE /api/tasks/<id>` - Delete task

### Team Management APIs
- `GET /api/teams/<project_id>` - List project teams
- `POST /api/teams` - Create new team
- `POST /api/teams/<id>/members` - Add team member

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Commit Changes**: `git commit -m 'Add amazing feature'`
4. **Push Branch**: `git push origin feature/amazing-feature`
5. **Pull Request**: Create detailed PR with description

### Development Guidelines
- Follow PEP 8 Python style guidelines
- Write clean, commented code
- Add tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support & Contact

- **GitHub**: [Task-Manager-Pro](https://github.com/shubhamdagar9854/Task-Manager-Pro)
- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check wiki for detailed guides
- **Community**: Join our Discord community for support

---
