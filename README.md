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
   GOOGLE_API_KEY=your-gemini-api-key-here
   ```

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
