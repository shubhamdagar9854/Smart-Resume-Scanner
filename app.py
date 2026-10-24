import sqlite3
import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Cloudinary for persistent file storage
import cloudinary
import cloudinary.uploader

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Cloudinary configuration from environment variables
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Production environment setup - FIXED FOR DEPLOYMENT
if os.environ.get('FLASK_ENV') == 'production':
    debug_mode = False
    # Use deployment-safe paths
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp')  # Cloudinary used in production
    DB_NAME = os.environ.get('DATABASE_PATH', '/tmp/resumes.db')
else:
    debug_mode = True
    # Local development paths
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp')
    DB_NAME = os.environ.get('DATABASE_PATH', 'resumes.db')

# Simple functions without AI for now
AI_AVAILABLE = False

def extract_text_from_resume(file_path):
    """Basic text extraction without AI"""
    try:
        import pdfplumber
        import docx
        
        if file_path.endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text: {e}")
    return ""

def calculate_match_percentage_full_ai_rag(resume_text, job_description):
    """Basic keyword matching without AI"""
    resume_text = resume_text.lower()
    job_desc = job_description.lower()
    
    # Extract basic skills from job description
    job_skills = ['python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'node']
    found_skills = [skill for skill in job_skills if skill in job_desc]
    
    # Count matches in resume
    matches = sum(1 for skill in found_skills if skill in resume_text)
    
    if len(found_skills) > 0:
        return (matches / len(found_skills)) * 100
    return 0.0

def generate_professional_summary_rag(resume_text):
    """Simple summary without AI"""
    # Extract basic info from resume
    lines = resume_text.split('\n')
    skills = []
    experience = []
    
    for line in lines:
        line_lower = line.lower()
        if any(tech in line_lower for tech in ['python', 'java', 'javascript', 'sql', 'react', 'node']):
            if len(line.strip()) < 100:
                skills.append(line.strip())
        if any(word in line_lower for word in ['lead', 'senior', 'consultant', 'engineer', 'developer']):
            if len(line.strip()) < 100:
                experience.append(line.strip())
    
    summary = "* " + " ".join(skills[:3]) if skills else "* Experienced professional with diverse technical skills"
    summary += "\n* " + (experience[0] if experience else "Software professional with proven track record")
    summary += "\n* Strong problem-solving and analytical capabilities"
    summary += "\n* Proficient in modern development tools and methodologies"
    summary += "\n* Excellent collaboration and communication skills"
    
    return summary

def normalize_resume_json(resume_text):
    """Basic normalization without AI"""
    return {"skills": [], "experience": "", "education": ""}

# Import AI functions from rag_summary
try:
    from rag_summary import (
        extract_text_from_resume as ai_extract_text,
        generate_professional_summary_rag as ai_generate_summary,
        calculate_match_percentage_full_ai_rag as ai_calculate_match,
        get_ai_match_analysis as ai_get_analysis
    )
    AI_AVAILABLE = True
    print("✅ AI modules loaded successfully")
except Exception as e:
    print(f"⚠️ AI modules not available: {e}")
    AI_AVAILABLE = False

def get_ai_match_analysis(resume_text, job_description, match_percentage):
    """Basic analysis without AI"""
    return f"Basic keyword matching shows {match_percentage:.1f}% compatibility"

from database import (
    add_job_post,
    get_all_job_posts,
    get_job_post_by_id,
    get_all_resumes,
    add_resume,
    get_resume_by_id,
    update_resume_summary,
    get_all_resumes,
    verify_admin,
    get_job_matches,
    init_db,
    add_ai_feedback,
    get_ai_feedback_by_type,
    add_enhanced_prompt,
    get_enhanced_prompt,
    get_all_ai_feedback,
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

# Use environment-aware upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


# DB init
init_db()


# =========================
# HELPERS
# =========================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    # Get summary from session if available
    summary = session.pop('last_summary', None)
    name = session.pop('last_name', None)
    return render_template("index.html", summary=summary, name=name)

@app.route("/", methods=["POST"])
def home_post():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone", "")

        if not name or not email:
            flash("Name and email are required!")
            return redirect(url_for("home"))

        if "resume_file" not in request.files:
            flash("Please upload a resume file!")
            return redirect(url_for("home"))

        file = request.files["resume_file"]
        if file.filename == "":
            flash("No file selected!")
            return redirect(url_for("home"))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Save temporarily for text extraction
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            # Extract text using AI function if available, else basic
            if AI_AVAILABLE:
                resume_text = ai_extract_text(temp_path)
            else:
                resume_text = extract_text_from_resume(temp_path)
            
            # Upload to Cloudinary for permanent storage
            try:
                upload_result = cloudinary.uploader.upload(
                    temp_path,
                    resource_type="raw",
                    folder="resumes",
                    public_id=f"{filename}_{int(os.times().elapsed)}"
                )
                cloudinary_url = upload_result['secure_url']
                print(f"✅ Uploaded to Cloudinary: {cloudinary_url}")
            except Exception as e:
                print(f"❌ Cloudinary upload failed: {e}")
                cloudinary_url = temp_path  # Fallback to local path
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            if resume_text:
                try:
                    if AI_AVAILABLE:
                        summary = ai_generate_summary(resume_text)
                    else:
                        summary = generate_professional_summary_rag(resume_text)
                    
                    # Check if summary is actually an error (contains specific error patterns)
                    if summary and ("Error generating summary:" in summary or "AI quota exceeded" in summary or "AI API Key Error:" in summary or "AI Error:" in summary):
                        summary = f"AI Summary Error: {summary}"
                    
                except Exception as e:
                    summary = f"AI Summary Error: Unable to generate summary - {str(e)}"
            else:
                summary = "Summary Error: Could not extract text from resume. Please check file format."

            # Add to database with Cloudinary URL
            add_resume(name, email, phone, "", cloudinary_url, summary)

            # Store summary in session to display after upload
            session['last_summary'] = summary
            session['last_name'] = name

            flash("Resume submitted successfully!")
            return redirect(url_for("home"))
        else:
            flash("Invalid file format! Please upload PDF, DOC, or DOCX file.")
            return redirect(url_for("home"))

    return render_template("index.html")


# =========================
# ADMIN AUTH
# =========================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if verify_admin(username, password):
            session["admin_logged_in"] = True
            session['dashboard_first_load'] = False  # Reset flag on fresh login
            flash("Login successful", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials", "error")

    return render_template("admin_login.html")


@app.route("/admin/candidate/<int:candidate_id>")
def admin_candidate_detail(candidate_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    candidate = get_resume_by_id(candidate_id)
    if not candidate:
        flash("Candidate not found", "error")
        return redirect(url_for("admin_dashboard"))
    
    return render_template("candidate_detail.html", candidate=candidate)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("admin_login"))


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    # Check if this is a reload (no session flag)
    if not session.get('dashboard_first_load', False):
        session['dashboard_first_load'] = True
        # Show blank page on first load/reload
        return render_template("admin_dashboard.html", resumes=[], page=1, has_prev=False, has_next=False, prev_page=None, next_page=None, total=0, per_page=5)
    
    # Show paginated resumes
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    if page < 1:
        page = 1
    
    resumes = get_all_resumes()
    
    total = len(resumes)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_resumes = resumes[start:end]
    
    has_prev = page > 1
    has_next = end < total
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    return render_template(
        "admin_dashboard.html", 
        resumes=paginated_resumes,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
        prev_page=prev_page,
        next_page=next_page,
        total=total,
        per_page=per_page
    )


# =========================
# 🔥 FIXED JOB POSTS WITH AI MATCHING
# =========================

@app.route("/admin/jobs", methods=["GET", "POST"])
def admin_jobs():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    jobs_with_matches = []

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if title and description:
            # Add job to database
            add_job_post(title, description)
            flash("Job posted successfully", "success")
            
            print(f"\n🔍 ANALYZING JOB: {title}")
            print(f"Description: {description}")
            
            # ========================================
            # 🔥 AI MATCHING LOGIC - FULLY FIXED
            # ========================================
            resumes = get_all_resumes()
            match_results = []

            for r in resumes:
                resume_path = r[5]
                if not resume_path:
                    continue

                # Extract resume text - try to get from file if local, or download from Cloudinary
                resume_text = ""
                try:
                    # Check if it's a Cloudinary URL
                    if resume_path.startswith('http') or 'cloudinary.com' in resume_path:
                        # For Cloudinary URLs, we need to download or use stored text
                        # Since we store summary in DB, use that for matching
                        resume_text = r[6] if len(r) > 6 and r[6] else ""
                    elif os.path.exists(resume_path):
                        if AI_AVAILABLE:
                            resume_text = ai_extract_text(resume_path)
                        else:
                            resume_text = extract_text_from_resume(resume_path)
                except Exception as e:
                    print(f"❌ Error extracting resume text: {e}")
                    resume_text = r[6] if len(r) > 6 and r[6] else ""
                
                if not resume_text:
                    continue

                # ========================================
                # 🔥 CALCULATE FINAL PERCENTAGE - AI POWERED
                # ========================================
                try:
                    if AI_AVAILABLE:
                        # Use full AI matching with RAG
                        final_percentage = ai_calculate_match(resume_text, description)
                        ai_analysis = ai_get_analysis(resume_text, description, final_percentage)
                    else:
                        # Fallback to basic calculation
                        final_percentage = calculate_match_percentage_full_ai_rag(resume_text, description)
                        if final_percentage == 0.0:
                            final_percentage = 50.0  # Default fallback
                        ai_analysis = get_ai_match_analysis(resume_text, description, final_percentage)
                except Exception as e:
                    print(f"❌ Matching error: {e}")
                    final_percentage = 0.0
                    ai_analysis = "Matching analysis unavailable"
                
                # Find matched skills for UI display (extract from job description)
                import re
                job_skills = re.findall(r'\b(python|java|javascript|html|css|sql|react|node|aws|docker|kubernetes|git|api|rest|graphql|spring|django|flask|machine learning|ai|ml|data|analytics)\b', description.lower())
                matched_skills_for_ui = list(set(job_skills))
                
                print("\n" + "=" * 70)
                print(f"📋 CANDIDATE: {r[1]}")
                print("=" * 70)
                print(f"🎯 PERCENTAGE: {final_percentage}%")
                print(f"🤖 AI ANALYSIS: {ai_analysis}")
                print("=" * 70 + "\n")

                # Show all candidates
                if final_percentage >= 0:
                    match_results.append({
                        "id": r[0],
                        "name": r[1],
                        "email": r[2],
                        "match": final_percentage,
                        "match_percentage": final_percentage,
                        "suggestions": "AI-powered matching analysis",
                        "matched_skills": matched_skills_for_ui,
                        "missing_skills": [],
                        "summary": r[6] if len(r) > 6 and r[6] else "",
                        "ai_analysis": ai_analysis
                    })

            # Sort by percentage (highest first)
            match_results.sort(key=lambda x: x["match_percentage"], reverse=True)
            
            # Get latest job post for display
            posts = get_all_job_posts()
            latest_post = posts[0] if posts else None
            
            if latest_post:
                jobs_with_matches.append({
                    "job": latest_post,
                    "matches": match_results
                })
    else:
        # GET request - show latest job with its matches
        posts = get_all_job_posts()
        latest_post = posts[0] if posts else None
        
        if latest_post:
            matches = get_job_matches(latest_post[0])
            # Ensure matches have both 'match' and 'match_percentage' keys
            formatted_matches = []
            for match in matches:
                if isinstance(match, dict):
                    match['match'] = match.get('match_percentage', 0)
                formatted_matches.append(match)
            
            jobs_with_matches.append({
                "job": latest_post,
                "matches": formatted_matches
            })

    return render_template(
        "admin_jobs.html",
        jobs_with_matches=jobs_with_matches
    )


# =========================
# API
# =========================

@app.route("/api/get_jobs")
def api_get_jobs():
    posts = get_all_job_posts()
    return jsonify({
        "jobs": [{"id": p[0], "title": p[1], "requirements": p[2]} for p in posts]
    })


@app.route("/api/get_matches/<int:job_id>")
def api_get_matches(job_id):
    matches = get_job_matches(job_id)
    return jsonify(matches)



@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve resume files - redirect to Cloudinary if URL, else local"""
    # If it's a Cloudinary URL, redirect directly
    if filename.startswith('http') or 'cloudinary.com' in filename:
        return redirect(filename)
    
    # If it's a full Cloudinary URL stored in DB
    if 'res.cloudinary.com' in filename:
        return redirect(filename)
    
    # Otherwise serve from local (fallback for old files)
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except:
        flash("File not found")
        return redirect(url_for('admin_dashboard'))

# 🤖 AI FEEDBACK SYSTEM FOR RAG
# =========================

@app.route("/admin/feedback", methods=["POST"])
def admin_feedback():
    """Handle admin feedback for AI results"""
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    job_id = request.form.get("job_id")
    resume_id = request.form.get("resume_id")
    match_percentage = request.form.get("match_percentage")
    correction_suggestion = request.form.get("correction_suggestion")
    
    if all([job_id, resume_id, match_percentage, correction_suggestion]):
        try:
            # Add feedback to database with RAG enhancement
            feedback_id = add_ai_feedback(
                int(job_id), 
                int(resume_id), 
                float(match_percentage), 
                "percentage",  # Use "percentage" as feedback type for RAG
                correction_suggestion,  # Use correction as error description
                correction_suggestion  # Use correction as suggestion
            )
            
            flash("✅ Feedback submitted successfully! AI will learn from this correction.", "success")
            print(f"🤖 AI Feedback Added: ID={feedback_id}, Job={job_id}, Resume={resume_id}")
            print(f"📝 Correction: {correction_suggestion}")
            
        except Exception as e:
            flash(f"❌ Error saving feedback: {str(e)}", "error")
            print(f"❌ Feedback Error: {e}")
    else:
        flash("❌ Please provide feedback for AI improvement", "error")
    
    # Redirect back to jobs page
    return redirect(url_for("admin_jobs"))

@app.route("/api/rate_match", methods=["POST"])
def api_rate_match():
    """Quick rating endpoint for match accuracy improvement"""
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized", "status": "error"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided", "status": "error"}), 400
    
    job_id = data.get('job_id')
    resume_id = data.get('resume_id')
    rating = data.get('rating')  # 'correct', 'high', 'low'
    ai_score = data.get('ai_score')
    correct_pct = data.get('correct_pct')
    
    if not all([job_id, resume_id, rating, ai_score is not None]):
        return jsonify({"error": "Missing required fields", "status": "error"}), 400
    
    # Determine feedback text based on rating
    if rating == 'correct':
        feedback_text = f"Match {ai_score}% was correct"
        error_desc = f"AI gave {ai_score}%"
        correction = f"Correct percentage: {correct_pct or ai_score}%"
    elif rating == 'high':
        feedback_text = f"Match {ai_score}% was too high (overestimated)"
        error_desc = f"AI overestimated: gave {ai_score}%"
        correction = f"Should be lower: {correct_pct or 'reduce by 15-20%'}%"
    else:  # low
        feedback_text = f"Match {ai_score}% was too low (underestimated)"
        error_desc = f"AI underestimated: gave {ai_score}%"
        correction = f"Should be higher: {correct_pct or 'increase by 15-20%'}%"
    
    try:
        # Save to existing ai_feedback table (RAG system reads this!)
        add_ai_feedback(
            int(job_id), 
            int(resume_id), 
            float(ai_score), 
            feedback_text, 
            error_desc, 
            correction
        )
        return jsonify({"message": f"Feedback saved: {rating}", "status": "success"})
    except Exception as e:
        print(f"❌ Rating Error: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/admin/feedback_history")
def admin_feedback_history():
    """Show all AI feedback history"""
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    try:
        feedback_list = get_all_ai_feedback()
        return render_template("feedback_history.html", feedback_list=feedback_list)
    except Exception as e:
        flash(f" Error loading feedback: {str(e)}", "error")
        return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)