import sqlite3
import os
import json

# Database Configuration
DB_NAME = "resumes.db"

# Use SQLite for now (MySQL setup later)

# --- INITIALIZE DATABASE ---
def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_NAME)
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
    
    # AI Feedback Table for RAG System
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            resume_id INTEGER,
            match_percentage REAL,
            admin_feedback TEXT,
            error_description TEXT,
            correction_suggestion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job_posts (id),
            FOREIGN KEY (resume_id) REFERENCES resumes (id)
        )
    """)
    
    # Enhanced Prompts Table for RAG
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enhanced_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_type TEXT,
            original_prompt TEXT,
            enhanced_prompt TEXT,
            feedback_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # HR Users Table for HR profiles
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hr_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            department TEXT,
            position TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
            # Generate AI analysis for why not 100%
            ai_analysis = ""
            if match_percent == 100:
                ai_analysis = "Perfect match! Candidate meets all job requirements."
            elif match_percent >= 90:
                ai_analysis = f"Excellent match! Candidate meets most requirements ({match_percent}% match). Minor improvements needed for 100%."
            elif match_percent >= 70:
                ai_analysis = f"Good match! Candidate meets many requirements ({match_percent}% match). Some key skills or experience may be missing."
            elif match_percent >= 50:
                ai_analysis = f"Fair match! Candidate meets some requirements ({match_percent}% match). Significant gaps in skills or experience."
            else:
                ai_analysis = f"Poor match! Candidate meets few requirements ({match_percent}% match). Major gaps in skills or experience."
            
            # Add specific missing skills information if available
            if match_percent < 100 and len(matched_keywords) < len(job_skills):
                missing_skills = [skill for skill in job_skills if skill not in matched_keywords]
                ai_analysis += f" Missing skills: {', '.join(missing_skills[:3])}. Candidate has {len(matched_keywords)}/{len(job_skills)} required skills."
            
            matches.append({
                "id": r[0],
                "name": r[1],
                "email": r[2],
                "phone": r[3] if len(r) > 3 else None,
                "file_path": r[4] if len(r) > 4 else None,  # Add file_path
                "summary": r[5] or "",
                "match": match_percent,
                "match_percentage": match_percent,  # Add this key for template
                "matched_skills": matched_keywords,
                "ai_analysis": ai_analysis  # 
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


def verify_admin(username, password):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
    user = cur.fetchone()
    conn.close()
    return user is not None

# --- AI FEEDBACK FUNCTIONS FOR RAG SYSTEM ---
def add_ai_feedback(job_id, resume_id, match_percentage, admin_feedback, error_description, correction_suggestion):
    """Add admin feedback for AI results"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ai_feedback (job_id, resume_id, match_percentage, admin_feedback, error_description, correction_suggestion)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (job_id, resume_id, match_percentage, admin_feedback, error_description, correction_suggestion))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_ai_feedback_by_type(prompt_type):
    """Get feedback for specific prompt type"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT error_description, correction_suggestion 
        FROM ai_feedback 
        WHERE admin_feedback = ? OR correction_suggestion LIKE ?
        ORDER BY created_at DESC 
        LIMIT 5
    """, (prompt_type, f"%{prompt_type}%"))
    feedback = cur.fetchall()
    conn.close()
    return feedback

def add_enhanced_prompt(prompt_type, original_prompt, enhanced_prompt):
    """Add enhanced prompt to database"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO enhanced_prompts (prompt_type, original_prompt, enhanced_prompt, feedback_count)
        VALUES (?, ?, ?, COALESCE((SELECT feedback_count FROM enhanced_prompts WHERE prompt_type = ?) + 1, 1))
    """, (prompt_type, original_prompt, enhanced_prompt, prompt_type))
    conn.commit()
    conn.close()

def get_enhanced_prompt(prompt_type):
    """Get enhanced prompt for specific type"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT enhanced_prompt FROM enhanced_prompts 
        WHERE prompt_type = ? 
        ORDER BY feedback_count DESC 
        LIMIT 1
    """, (prompt_type,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_ai_feedback():
    """Get all AI feedback for admin review"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT af.*, j.title, r.name 
        FROM ai_feedback af
        JOIN job_posts j ON af.job_id = j.id
        JOIN resumes r ON af.resume_id = r.id
        ORDER BY af.created_at DESC
    """)
    feedback = cur.fetchall()
    conn.close()
    return feedback

def add_hr_user(username, email, password, full_name, phone, department, position):
    """Add HR user to database"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO hr_users (username, email, password, full_name, phone, department, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, password, full_name, phone, department, position))
        new_id = cur.lastrowid
        conn.commit()
        return new_id
    except Exception as e:
        conn.close()
        return f"Error adding HR user: {e}"

def get_hr_user_by_username(username):
    """Get HR user by username"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM hr_users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def get_all_hr_users():
    """Get all HR users"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM hr_users ORDER BY created_at DESC")
    users = cur.fetchall()
    conn.close()
    return users

def update_hr_user_profile(user_id, full_name, phone, department, position):
    """Update HR user profile"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE hr_users 
            SET full_name = ?, phone = ?, department = ?, position = ?
            WHERE id = ?
        """, (full_name, phone, department, position, user_id))
        conn.commit()
        return True
    except Exception as e:
        conn.close()
        return f"Error updating HR user: {e}"