# Smart-Resume-Scanner
AI Resume Analyzer with professional summary generation and intelligent job matching capabilities.

## Features
- 📄 PDF/DOCX resume processing with pdfplumber
- 🤖 Hybrid AI + Rules-based analysis (Ollama + Regex)
- 📊 Professional 8-point summary generation
- 🎯 Intelligent skill matching with percentage scoring
- 👨‍💼 Admin dashboard for candidate management
- 🔍 Job posting and automated matching
- 📱 Responsive web interface

## Technology Stack
- **Backend**: Python 3.11.9, Flask 2.3.3
- **AI**: Local Ollama with llama3.2:1b model
- **Database**: SQLite
- **Document Processing**: pdfplumber, python-docx
- **Deployment**: Production ready with Gunicorn

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Start Ollama server: `ollama serve`
4. Run the application: `python app.py`

## Usage
- Upload resumes for AI analysis
- Admin can post jobs and view matching candidates
- Professional summaries generated automatically
- Skill-based matching with accurate percentages
