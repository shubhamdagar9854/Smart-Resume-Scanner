# Resume Scanner

AI-powered resume analysis and job matching system using Google Gemini AI. Automatically analyzes resumes, extracts skills, and matches candidates with job descriptions.

## Features

- **Resume Upload & Analysis**: Upload PDF/DOCX files for AI analysis
- **Skill Extraction**: Automatically identifies candidate skills
- **Job Matching**: Matches resumes with job descriptions
- **Smart Scoring**: Ranks candidates based on compatibility
- **Learning System**: Improves accuracy over time

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/shubhamdagar9854/Smart-Resume-Scanner.git
cd Smart-Resume-Scanner

# Setup environment
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python database.py

# Run the app
python app.py
```

### Setup Required

1. **Get Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)
2. **Create `.env` file** with your API key:
   ```
   GOOGLE_API_KEY=your-api-key-here
   ```

### How to Use

1. **Open browser** and go to `http://localhost:5000`
2. **Upload resume** (PDF or DOCX format)
3. **View analysis** - AI will extract:
   - Skills and experience
   - Education details
   - Summary and recommendations
4. **Create job posting** to match candidates
5. **View matches** with compatibility scores

##  Tech Stack

- **Backend**: Python Flask
- **AI**: Google Gemini API
- **Database**: SQLite (default) / PostgreSQL
- **File Processing**: PDF/DOCX parsing
- **Frontend**: HTML/CSS/JavaScript

##  Requirements

- Python 3.9+
- Google Gemini API Key
- 2GB+ RAM recommended
- 500MB+ disk space

##  Deployment

### Local Development
```bash
python app.py
```

### Docker (Optional)
```bash
docker build -t resume-scanner .
docker run -p 5000:5000 resume-scanner
```

##  Troubleshooting

**Common Issues:**
- **API Key Error**: Make sure `.env` file contains valid Google API key
- **File Upload Error**: Check file format (PDF/DOCX only) and size limit
- **Database Error**: Run `python database.py` to initialize database

##  Support

- **GitHub Issues**: [Report bugs here](https://github.com/shubhamdagar9854/Smart-Resume-Scanner/issues)
- **Email**: shubhamdagar9854@gmail.com

---

**Made with  by Shubham Dagar**
