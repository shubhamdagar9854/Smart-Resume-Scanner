import sqlite3
import os
import json

# Database Configuration
DB_NAME = "resumes.db"

# Use SQLite for now (MySQL setup later)
def get_connection():
    """Get database connection (SQLite for now)"""
    return sqlite3.connect(DB_NAME)

# --- INITIALIZE DATABASE ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Resumes Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            photo TEXT,
            file_path TEXT,
            summary TEXT
        )
        """)

    # Job Posts Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Admin Table
    cur.execute("CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
    cur.execute("SELECT * FROM admin")
    if cur.fetchone() is None:
        cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("admin", "admin123"))
    conn.commit()
    conn.close()

# --- JOB FUNCTIONS ---
def add_job_post(title, description, requirements=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO job_posts (title, description, requirements) VALUES (?, ?, ?)",
        (title, description, requirements)
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_job_post_by_id(job_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM job_posts WHERE id = ?", (job_id,))
    job = cur.fetchone()
    conn.close()
    return job

def get_all_job_posts():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM job_posts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

# --- AI MATCHING LOGIC ---
# Note: Iska naam 'get_job_matches' rakha hai taaki app.py se match kare
def get_job_matches(job_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Job requirements - description se keywords extract karte hain
    cursor.execute("SELECT title, description, requirements FROM job_posts WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    if not job:
        return []

    # Title + description + requirements se keywords banate hain
    job_text = f"{job[0]} {job[1]} {job[2] or ''}".lower()
    
    # Common skills/keywords extract karte hain
    import re
    # Words ke liye regex (2+ letters)
    words = re.findall(r'\b[a-zA-Z]{2,}\b', job_text)
    
    # Common technical skills aur qualifications
    tech_keywords = ['python', 'java', 'javascript', 'react', 'node', 'sql', 'mongodb', 'aws', 'docker', 
                   'git', 'agile', 'scrum', 'api', 'rest', 'html', 'css', 'angular', 'vue', 'django', 
                   'flask', 'machine', 'learning', 'ai', 'data', 'science', 'analytics', 'devops']
    
    education_keywords = ['bsc', 'msc', 'bachelor', 'master', 'phd', 'degree', 'engineering', 
                         'computer', 'science', 'information', 'technology']
    
    # Unique words filter karte hain
    job_skills = list(set([word for word in words if len(word) > 2]))
    
    # Add specific tech/education keywords if present
    for keyword in tech_keywords + education_keywords:
        if keyword in job_text:
            job_skills.append(keyword)

    cursor.execute("SELECT id, name, email, phone, file_path, summary FROM resumes")
    resumes = cursor.fetchall()

    matches = []

    for r in resumes:
        resume_text = (r[5] or "").lower()  # Summary is now at index 5
        
        # Count matching keywords
        matched_keywords = []
        for skill in job_skills:
            if skill in resume_text:
                matched_keywords.append(skill)
        
        # Calculate match percentage
        match_percent = 0
        if job_skills:
            match_percent = int((len(matched_keywords) / len(job_skills)) * 100)
        
        # Only show matches with at least 10% match
        if match_percent >= 10:
            matches.append({
                "id": r[0],
                "name": r[1],
                "email": r[2],
                "phone": r[3] if len(r) > 3 else None,
                "file_path": r[4] if len(r) > 4 else None,  # Add file_path
                "summary": r[5] or "",
                "match": match_percent,
                "matched_skills": matched_keywords
            })

    # Sort by match percentage (highest first)
    matches.sort(key=lambda x: x["match"], reverse=True)
    
    conn.close()
    return matches

# --- RESUME UTILITIES ---
def add_resume(name, email, phone, photo, file_path, summary):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO resumes (name, email, phone, photo, file_path, summary) VALUES (?, ?, ?, ?, ?, ?)", 
                (name, email, phone, photo, file_path, summary))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_resume_summary(resume_id, summary):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE resumes SET summary = ? WHERE id = ?", (summary, resume_id))
    conn.commit()
    conn.close()

def get_all_resumes():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM resumes ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return data

def get_resume_by_id(resume_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
    resume = cur.fetchone()
    conn.close()
    return resume

def filter_resumes_by_keyword(keyword):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    query = f"%{keyword}%"
    cur.execute("SELECT * FROM resumes WHERE name LIKE ? OR email LIKE ? OR summary LIKE ? ORDER BY id DESC", (query, query, query))
    results = cur.fetchall()
    conn.close()
    return results

# def filter_resumes_by_post(post_type):
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM resumes WHERE post_type = ?", (post_type,))
#     results = cur.fetchall()
#     conn.close()
#     return results

def verify_admin(username, password):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
    user = cur.fetchone()
    conn.close()
    return user is not None