from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import os
import logging
import threading
from werkzeug.utils import secure_filename
import sqlite3
import io
from datetime import datetime
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Production environment setup
if os.environ.get('FLASK_ENV') == 'production':
    debug_mode = False
else:
    debug_mode = True

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

# Database setup with BLOB storage
def init_db():
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        skills TEXT,
        resume_text TEXT,
        file_data BLOB,
        file_name TEXT,
        file_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Text extraction functions
def extract_text_from_file(file, file_ext):
    """Extract text from PDF or DOCX"""
    try:
        if file_ext == '.pdf':
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        
        elif file_ext == '.docx':
            import docx
            doc = docx.Document(file)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text
            
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def extract_skills(text):
    """Extract skills from resume text"""
    import re
    skills_keywords = ['python', 'java', 'javascript', 'flask', 'django', 'react', 'node', 'sql']
    found_skills = []
    text_lower = text.lower()
    
    for skill in skills_keywords:
        if skill in text_lower:
            found_skills.append(skill)
    
    return ', '.join(found_skills)

# Upload route - Save file in database
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            print("DEBUG: POST request received")
            print(f"DEBUG: Form data: {request.form}")
            print(f"DEBUG: Files: {request.files}")
            
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            print(f"DEBUG: Extracted - Name: {name}, Email: {email}, Phone: {phone}")
            
            if not all([name, email, phone]):
                print("DEBUG: Missing required fields")
                flash('All fields are required!', 'error')
                return redirect(url_for('index'))
            
            # Get file
            if 'resume' not in request.files:
                print("DEBUG: No resume file in request")
                flash('No file uploaded!', 'error')
                return redirect(url_for('index'))
            
            file = request.files['resume']
            print(f"DEBUG: File object: {file}")
            print(f"DEBUG: File filename: {file.filename}")
            
            if file.filename == '':
                print("DEBUG: Empty filename")
                flash('No file selected!', 'error')
                return redirect(url_for('index'))
            
            # Validate file type
            allowed_extensions = ['.pdf', '.docx']
            file_ext = os.path.splitext(file.filename)[1].lower()
            print(f"DEBUG: File extension: {file_ext}")
            
            if file_ext not in allowed_extensions:
                print("DEBUG: Invalid file type")
                flash('Only PDF and DOCX files allowed!', 'error')
                return redirect(url_for('index'))
            
            # Read file content
            file_data = file.read()
            file_name = secure_filename(file.filename)
            file_type = file.content_type or 'application/octet-stream'
            
            print(f"DEBUG: File size: {len(file_data)} bytes")
            print(f"DEBUG: File name: {file_name}")
            print(f"DEBUG: File type: {file_type}")
            
            # Extract text from file
            file.seek(0)  # Reset file pointer
            resume_text = extract_text_from_file(file, file_ext)
            print(f"DEBUG: Extracted text length: {len(resume_text)}")
            
            # Extract skills
            skills = extract_skills(resume_text)
            print(f"DEBUG: Extracted skills: {skills}")
            
            # Save to database
            conn = sqlite3.connect('resumes.db')
            c = conn.cursor()
            c.execute('''INSERT INTO resumes 
                        (name, email, phone, skills, resume_text, file_data, file_name, file_type) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (name, email, phone, skills, resume_text, file_data, file_name, file_type))
            conn.commit()
            conn.close()
            
            print("DEBUG: Successfully saved to database")
            flash('Resume uploaded successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Error uploading resume: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    return render_template('index_database.html')

# Serve file from database
@app.route('/uploads/<int:resume_id>')
def serve_upload(resume_id):
    try:
        conn = sqlite3.connect('resumes.db')
        c = conn.cursor()
        c.execute('SELECT file_data, file_name, file_type FROM resumes WHERE id = ?', (resume_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            file_data, file_name, file_type = result
            return send_file(
                io.BytesIO(file_data),
                download_name=file_name,
                mimetype=file_type,
                as_attachment=False
            )
        else:
            return "File not found", 404
            
    except Exception as e:
        print(f"ERROR serving file: {e}")
        return "Error loading file", 500

# Simple admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

# Admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page
    
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    
    # Get total count
    c.execute('SELECT COUNT(*) FROM resumes')
    total = c.fetchone()[0]
    
    # Get paginated resumes
    c.execute('''SELECT id, name, email, phone, skills, file_name, created_at 
                 FROM resumes 
                 ORDER BY created_at DESC 
                 LIMIT ? OFFSET ?''', (per_page, offset))
    resumes = c.fetchall()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('admin_dashboard.html',
                         resumes=resumes,
                         page=page,
                         total_pages=total_pages,
                         total_resumes=total)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
