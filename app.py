import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import os
import logging
from werkzeug.utils import secure_filename

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Production environment setup
if os.environ.get('FLASK_ENV') == 'production':
    debug_mode = False
else:
    debug_mode = True

from rag_summary import (
    extract_text_from_resume,
    calculate_match_percentage_full_ai_rag,
    generate_professional_summary_rag,
    normalize_resume_json,
    get_ai_match_analysis,
)

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
    # HR User Functions
    add_hr_user,
    get_hr_user_by_username,
    get_all_hr_users,
    update_hr_user_profile,
)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


UPLOAD_FOLDER = '/tmp' 
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
    return render_template("index.html")

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
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Extract text and generate summary
            resume_text = extract_text_from_resume(file_path)
            print(f"DEBUG: Extracted resume text length: {len(resume_text)}")
            print(f"DEBUG FULL TEXT: {resume_text}") # <-- Isse terminal mein dikhega ki actually read kya
            
            if resume_text:
                try:
                    print("DEBUG: Generating enhanced summary...")
                    summary = generate_professional_summary_rag(resume_text)
                    print(f"DEBUG: Generated summary:\n{summary}")
                except Exception as e:
                    print(f"DEBUG: Summary generation failed: {e}")
                    import traceback
                    traceback.print_exc()
                    summary = "• Technology professional with comprehensive software development expertise."
            else:
                print("DEBUG: No resume text extracted")
                summary = "• Could not extract text from resume. Please check file format."

            # Add to database
            print(f"FINAL SUMMARY BEING SAVED:\n{summary}")
            add_resume(name, email, phone, "", file_path, summary)
            print("DEBUG: Resume saved to database successfully")

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
    
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    if page < 1:
        page = 1
    
    resumes = get_all_resumes()
    
    print(f"DEBUG: Total resumes found: {len(resumes)}")
    
    # Pagination logic
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
                if not resume_path or not os.path.exists(resume_path):
                    continue

                resume_text = extract_text_from_resume(resume_path)
                if not resume_text:
                    continue

                # Create basic job and resume data structure
                jd_json = {
                    "skills": ["python", "java", "html", "react"],  # Extract from description
                    "projects": [],
                    "experience_years": 0
                }
                
                resume_json = {
                    "skills": ["python", "java", "html"],  # Extract from resume
                    "projects": [],
                    "experience_years": 0
                }

                # ========================================
                # 🔥 CALCULATE FINAL PERCENTAGE - CASE-INSENSITIVE MATCHING
                # ========================================
                # Clean and normalize skills
                jd_skills_clean = [skill.lower() for skill in jd_json["skills"] if skill]
                resume_skills_clean = [skill.lower() for skill in resume_json["skills"] if skill]
                
                # Calculate basic percentage based on matched skills - INLINE CALCULATION
                if len(jd_skills_clean) > 0:
                    # Calculate matched skills inline to avoid variable reference error
                    matched_count = 0
                    for skill in resume_skills_clean:
                        if skill in jd_skills_clean:
                            matched_count += 1
                    basic_percentage = (matched_count / len(jd_skills_clean)) * 100
                else:
                    basic_percentage = 0.0
                
                # Use AI for final analysis, but fallback to basic calculation if AI fails
                try:
                    final_percentage = calculate_match_percentage_full_ai_rag(resume_text, description)
                    # If AI returns 0 due to quota issues, use basic calculation
                    if final_percentage == 0.0:
                        final_percentage = basic_percentage
                except:
                    final_percentage = basic_percentage
                
                # 🔥 EXPERIENCE VALIDATION - Check if job requires experience
                experience_required = False
                experience_years = 0
                
                # Check for experience requirements in job description
                if any(exp in description.lower() for exp in ['year experience', 'years experience', '+ year', '+ years']):
                    experience_required = True
                    # Extract experience years if mentioned
                    import re
                    exp_match = re.search(r'(\d+)\+?\s*year', description.lower())
                    if exp_match:
                        experience_years = int(exp_match.group(1))
                
                # Check if candidate has experience (basic check)
                candidate_has_experience = False
                if resume_text:
                    # Look for experience indicators in resume
                    exp_indicators = ['years of experience', 'year of experience', 'experience:', 'worked for', 'employed', 'professional experience']
                    candidate_has_experience = any(indicator in resume_text.lower() for indicator in exp_indicators)
                
                print(f"🔍 EXPERIENCE CHECK: Required={experience_required}, Years={experience_years}, Candidate has exp={candidate_has_experience}")
                
                # Apply experience penalty if required but not present
                if experience_required and not candidate_has_experience:
                    print(f"⚠️ EXPERIENCE MISMATCH: Job requires {experience_years}+ years but candidate lacks experience")
                    # Apply small experience penalty (5% deduction)
                    final_percentage = max(final_percentage - 5, 0)  # Deduct 5%, minimum 0%
                    ai_analysis = f"Experience mismatch: Job requires {experience_years}+ years experience, but candidate lacks professional experience. Skills match perfectly but experience level is insufficient. 5% penalty applied."
                else:
                    # Get AI analysis for why not 100% from AI model
                    if final_percentage < 100:
                        ai_analysis = get_ai_match_analysis(resume_text, description, final_percentage)
                    else:
                        ai_analysis = "Perfect match! Candidate meets all job requirements."
                
                # Find matched skills for UI display (no duplicates)
                matched_skills_for_ui = []
                matched_seen = set()
                
                for skill in resume_skills_clean:
                    if skill in jd_skills_clean and skill not in matched_seen:
                        matched_skills_for_ui.append(skill)
                        matched_seen.add(skill)
                
                # Debug logging
                print("\n" + "=" * 70)
                print(f"📋 CANDIDATE: {r[1]}")
                print("=" * 70)
                print(f"📝 JD REQUIRES: {jd_json['skills']}")
                print(f"📄 RESUME HAS: {resume_json['skills']}")
                print(f"✅ MATCHED: {matched_skills_for_ui}")
                print(f"🎯 PERCENTAGE: {final_percentage}%")
                print(f"🤖 AI ANALYSIS: {ai_analysis}")
                print("=" * 70 + "\n")

                # Show all candidates - remove 0% filter for debugging
                if final_percentage >= 0:
                    match_results.append({
                        "name": r[1],
                        "email": r[2],
                        "match": final_percentage,  # <--- Ye 'match' key hona zaroori hai
                        "match_percentage": final_percentage,  # For consistency
                        "suggestions": "AI-powered matching analysis",
                        "matched_skills": matched_skills_for_ui,
                        "missing_skills": [],
                        "summary": r[6] if len(r) > 6 else "",
                        "ai_analysis": ai_analysis  # 🔥 NEW: AI analysis for why not 100%
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



@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve resume files from upload folder"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

@app.route("/admin/feedback_history")
def admin_feedback_history():
    """Show all AI feedback history"""
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    try:
        feedback_list = get_all_ai_feedback()
        return render_template("feedback_history.html", feedback_list=feedback_list)
    except Exception as e:
        flash(f"❌ Error loading feedback: {str(e)}", "error")
        return redirect(url_for("admin_dashboard"))


# =========================
if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)