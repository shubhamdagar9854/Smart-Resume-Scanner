import sqlite3
import os
import json

# Database configuration - FIXED FOR DEPLOYMENT
DB_NAME = os.environ.get('DATABASE_PATH', 'resumes.db')

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
    
    # Common technical skills aur qualifications - comprehensive for all possible scenarios
    tech_keywords = [
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c', 'cpp', 'csharp', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala',
        # Web Technologies
        'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring', 'laravel', 'rails', 'asp', 'dotnet',
        'html', 'css', 'sass', 'less', 'bootstrap', 'tailwind', 'jquery', 'ajax', 'json', 'xml',
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'firebase',
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'terraform', 'ansible',
        'ci', 'cd', 'cicd', 'pipeline', 'deployment', 'monitoring', 'logging', 'security',
        # Software Engineering
        'agile', 'scrum', 'kanban', 'waterfall', 'tdd', 'bdd', 'unit', 'integration', 'e2e', 'testing',
        'api', 'rest', 'graphql', 'soap', 'microservices', 'monolith', 'serverless', 'lambda', 'functions',
        # Architecture & Design
        'architecture', 'design', 'pattern', 'solid', 'dry', 'kiss', 'mvp', 'mvc', 'mvp', 'clean', 'code',
        'algorithm', 'structure', 'optimization', 'performance', 'scalability', 'reliability', 'availability',
        # Data & Analytics
        'data', 'analytics', 'science', 'machine', 'learning', 'ai', 'ml', 'dl', 'nlp', 'cv', 'statistics',
        'tableau', 'powerbi', 'excel', 'python', 'r', 'sas', 'spss', 'mining', 'warehousing', 'etl',
        # Mobile Development
        'mobile', 'ios', 'android', 'reactnative', 'flutter', 'swift', 'kotlin', 'xamarin', 'cordova', 'phonegap',
        'pwa', 'responsive', 'adaptive', 'hybrid', 'native',
        # Leadership & Management
        'leader', 'leadership', 'team', 'manager', 'lead', 'senior', 'junior', 'principal', 'staff', 'head',
        'director', 'vp', 'cto', 'architect', 'consultant', 'advisor', 'mentor', 'coach', 'trainer',
        # Business & Domain
        'business', 'strategy', 'planning', 'execution', 'delivery', 'operations', 'finance', 'marketing', 'sales',
        'retail', 'insurance', 'banking', 'healthcare', 'education', 'government', 'manufacturing', 'logistics',
        'ecommerce', 'fintech', 'healthtech', 'edtech', 'saas', 'paas', 'iaas', 'b2b', 'b2c', 'c2c',
        # Experience & Skills
        'experience', 'expert', 'skilled', 'proficient', 'knowledge', 'hands', 'practical', 'theoretical',
        'handling', 'client', 'customer', 'stakeholder', 'vendor', 'partner', 'supplier', 'contractor',
        'communication', 'presentation', 'documentation', 'reporting', 'analysis', 'research', 'development',
        # Tools & Technologies
        'git', 'svn', 'mercurial', 'jira', 'confluence', 'slack', 'teams', 'zoom', 'office', 'gdrive',
        'vscode', 'intellij', 'eclipse', 'xcode', 'androidstudio', 'postman', 'swagger', 'insomnia',
        'webpack', 'vite', 'parcel', 'gulp', 'grunt', 'npm', 'yarn', 'maven', 'gradle', 'pip',
        # Security & Compliance
        'security', 'authentication', 'authorization', 'encryption', 'ssl', 'tls', 'oauth', 'jwt', 'saml',
        'gdpr', 'hipaa', 'sox', 'pci', 'compliance', 'audit', 'risk', 'vulnerability', 'penetration',
        # Emerging Technologies
        'blockchain', 'crypto', 'web3', 'metaverse', 'ar', 'vr', 'iot', 'edge', 'quantum', '5g',
        'robotics', 'automation', 'rpa', 'chatbot', 'voice', 'assistant', 'siri', 'alexa', 'google',
        # General Terms
        'developer', 'engineer', 'software', 'web', 'mobile', 'backend', 'frontend', 'fullstack', 'database',
        'cloud', 'testing', 'unit', 'integration', 'deployment', 'microservices', 'architecture', 'design',
        'pattern', 'algorithm', 'structure', 'domain', 'grpc', 'cicd', 'expert', 'handling', 'client'
    ]
    
    education_keywords = [
        # Degrees & Education Levels
        'bsc', 'msc', 'bachelor', 'master', 'phd', 'degree', 'engineering', 'computer', 'science', 'information', 'technology',
        'btech', 'mtech', 'be', 'me', 'bca', 'mca', 'bcom', 'mcom', 'ba', 'ma', 'bs', 'ms', 'mba', 'pgdm', 'diploma',
        'certificate', 'certification', 'course', 'training', 'workshop', 'seminar', 'conference', 'symposium', 'webinar',
        # Education Fields
        'computer', 'science', 'engineering', 'information', 'technology', 'software', 'hardware', 'networking', 'cybersecurity',
        'data', 'analytics', 'artificial', 'intelligence', 'machine', 'learning', 'deep', 'neural', 'robotics', 'automation',
        'business', 'administration', 'management', 'finance', 'accounting', 'marketing', 'sales', 'human', 'resources',
        'economics', 'statistics', 'mathematics', 'physics', 'chemistry', 'biology', 'biotechnology', 'pharmacy', 'medicine',
        'law', 'legal', 'arts', 'humanities', 'social', 'psychology', 'sociology', 'philosophy', 'history', 'geography',
        'architecture', 'civil', 'mechanical', 'electrical', 'electronics', 'telecommunication', 'chemical', 'aerospace',
        'agriculture', 'environmental', 'sustainable', 'renewable', 'energy', 'petroleum', 'mining', 'geology',
        'journalism', 'mass', 'communication', 'media', 'advertising', 'public', 'relations', 'design', 'fashion',
        'hospitality', 'tourism', 'hotel', 'management', 'culinary', 'arts', 'music', 'dance', 'theater', 'film',
        'education', 'teaching', 'academic', 'research', 'library', 'information', 'science', 'literature', 'linguistics',
        # Education Institutions
        'university', 'college', 'institute', 'school', 'academy', 'polytechnic', 'institution', 'center', 'department',
        'faculty', 'campus', 'online', 'distance', 'learning', 'virtual', 'remote', 'hybrid', 'part', 'time', 'full',
        # Education Quality
        'accredited', 'recognized', 'approved', 'licensed', 'certified', 'qualified', 'professional', 'technical',
        'vocational', 'industrial', 'commercial', 'government', 'private', 'public', 'international', 'global',
        # Education Terms
        'gpa', 'percentage', 'grade', 'score', 'rank', 'merit', 'distinction', 'first', 'class', 'honors', 'cum', 'laude',
        'thesis', 'dissertation', 'project', 'assignment', 'internship', 'apprenticeship', 'placement', 'campus', 'recruitment',
        'entrance', 'exam', 'test', 'assessment', 'evaluation', 'competition', 'olympiad', 'scholarship', 'fellowship',
        'grant', 'assistantship', 'research', 'assistant', 'teaching', 'assistant', 'lab', 'assistant', 'graduate',
        'undergraduate', 'postgraduate', 'doctoral', 'postdoctoral', 'continuing', 'professional', 'development',
        # Skills & Knowledge
        'knowledge', 'skill', 'ability', 'competency', 'expertise', 'proficiency', 'mastery', 'specialization',
        'general', 'studies', 'foundation', 'principles', 'fundamentals', 'basics', 'advanced', 'intermediate',
        'beginner', 'novice', 'expert', 'professional', 'practitioner', 'specialist', 'consultant', 'advisor'
    ]
    
    # Unique words filter karte hain
    job_skills = list(set([word for word in words if len(word) > 2]))
    
    # Add specific tech/education keywords if present
    for keyword in tech_keywords + education_keywords:
        if keyword in job_text:
            job_skills.append(keyword)
    
    # DEBUG: Print job requirements found
    print(f" JOB REQUIREMENTS FOUND: {job_skills}")
    print(f" JOB TEXT ANALYSIS: {job_text}")

    cursor.execute("SELECT id, name, email, phone, file_path, summary FROM resumes")
    resumes = cursor.fetchall()

    matches = []

    for r in resumes:
        resume_text = (r[5] or "").lower()  # Summary is now at index 5
        
        # DEBUG: Print resume analysis
        print(f" RESUME ANALYSIS: {resume_text[:500]}...")  # Show first 500 chars instead of 200
        
        # Count matching keywords
        matched_keywords = []
        for skill in job_skills:
            if skill in resume_text:
                matched_keywords.append(skill)
        
        # DEBUG: Print what matched
        print(f" MATCHED KEYWORDS: {matched_keywords}")
        print(f" TOTAL JOB SKILLS: {len(job_skills)}")
        
        # Calculate match percentage with experience and domain validation
        match_percent = 0
        if job_skills:
            # Basic keyword matching
            keyword_match = int((len(matched_keywords) / len(job_skills)) * 100)
            
            # Experience validation - check for years requirements
            experience_penalty = 0
            if any(year_req in job_text for year_req in ['10plus', '10+', '9+', '8+', '5+', '3+']):
                # Check if resume indicates sufficient experience
                resume_has_exp = any(exp_word in resume_text for exp_word in 
                    ['year', 'years', 'experience', 'exp', 'worked', 'employment'])
                # Also check for actual years mentioned in resume
                has_years = any(year_pattern in resume_text for year_pattern in 
                    ['10+', '9+', '8+', '5+', '3+', '10 years', '9 years', '8 years'])
                
                if not resume_has_exp and not has_years:
                    experience_penalty = 30  # Major penalty for missing experience
                # Don't penalize if "expected graduation" but also has experience indicators
                elif any(student_word in resume_text.lower() for student_word in 
                    ['student', 'graduate']) and not has_years:
                    experience_penalty = 25  # Penalty only if student without experience
            
            # Domain validation - check for specific domain requirements
            domain_penalty = 0
            if any(domain_req in job_text for domain_req in ['insurance', 'banking', 'healthcare', 'finance']):
                if not any(domain_word in resume_text for domain_word in 
                    ['insurance', 'banking', 'healthcare', 'finance', 'financial']):
                    domain_penalty = 25  # Major penalty for missing domain
            
            # Leadership validation - check for leadership requirements
            leadership_penalty = 0
            if any(lead_req in job_text for lead_req in ['leader', 'lead', 'team', 'manager', 'handle team']):
                if not any(lead_word in resume_text for lead_word in 
                    ['lead', 'leader', 'manager', 'team', 'managed', 'leadership']):
                    leadership_penalty = 20  # Penalty for missing leadership
            
            # Calculate final percentage with penalties
            match_percent = keyword_match - experience_penalty - domain_penalty - leadership_penalty
            match_percent = max(0, min(100, match_percent))  # Ensure within 0-100 range
        
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