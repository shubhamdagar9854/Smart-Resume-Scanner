from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import os
import threading
from werkzeug.utils import secure_filename

# Production environment setup
if os.environ.get('FLASK_ENV') == 'production':
    debug_mode = False
else:
    debug_mode = True

from rag_summary import (
    analyze_resume_text,
    analyze_job_text,
    match_resume_with_job,
    extract_text_from_resume,
    normalize_resume_json,
    normalize_skills,
    calculate_match_percentage
)

from database import (
    add_job_post,
    get_all_job_posts,
    get_all_resumes,
    add_resume,
    get_resume_by_id,
    get_job_post_by_id,
    update_resume_summary,
    verify_admin,
    filter_resumes_by_keyword,
    get_job_matches,
    init_db
)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            
            if resume_text:
                try:
                    print("DEBUG: Starting resume analysis...")
                    resume_analysis = analyze_resume_text(resume_text)
                    print(f"DEBUG: Resume analysis: {resume_analysis}")
                    
                    # Generate summary from analysis
                    if resume_analysis and resume_analysis.get("skills"):
                        skills_str = ", ".join(resume_analysis["skills"][:5])
                        exp_years = resume_analysis.get("experience_years", 0)
                        role_level = resume_analysis.get("role_level", "professional")
                        
                        summary = f"• {role_level.title()} technology professional with {exp_years}+ years of experience.\n"
                        summary += f"• Proficient in {skills_str} with focus on scalable solutions.\n"
                        
                        if resume_analysis.get("projects_count", 0) > 0:
                            summary += f"• Successfully delivered {resume_analysis['projects_count']} technical projects.\n"
                        
                        if resume_analysis.get("domain") and resume_analysis["domain"] != "general":
                            summary += f"• Strong background in {resume_analysis['domain'].title()} industry.\n"
                        
                        if resume_analysis.get("key_achievements"):
                            summary += f"• Experience with {', '.join(resume_analysis['key_achievements'][:2])}."
                    else:
                        summary = "• Technology professional with comprehensive software development expertise."
                        
                    print(f"DEBUG: Generated summary: {summary}")
                        
                except Exception as e:
                    print(f"DEBUG: Resume analysis failed: {e}")
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

                # AI extracts data ONLY
                ai_raw = match_resume_with_job(resume_text, description)
                
                # ========================================
                # 🔥 NORMALIZE JD JSON
                # ========================================
                raw_jd = ai_raw.get("job_data", {})
                jd_json = {
                    "skills": raw_jd.get("must_have", []) if isinstance(raw_jd.get("must_have"), list) else [],
                    "projects": raw_jd.get("projects_required", []) if isinstance(raw_jd.get("projects_required"), list) else [],
                    "experience_years": raw_jd.get("experience_years_required", 0) if isinstance(raw_jd.get("experience_years_required"), (int, float)) else 0
                }
                
                # ========================================
                # 🔥 NORMALIZE & CLEAN RESUME JSON
                # ========================================
                raw_resume = ai_raw.get("resume_data", {})
                normalized_resume = normalize_resume_json(raw_resume)
                
                GARBAGE_VALUES = {
                    "project", "projects", "experience", "experiences",
                    "requirement", "requirements", "skill", "skills",
                    "year", "years", "work", "education", "any", "the"
                }
                
                # Clean JD skills - remove duplicates and garbage
                jd_skills_clean = []
                jd_seen = set()
                for skill in jd_json["skills"]:
                    skill_lower = str(skill).strip().lower()
                    if skill_lower and skill_lower not in GARBAGE_VALUES and skill_lower not in jd_seen and len(skill_lower) > 1:
                        jd_skills_clean.append(skill_lower)
                        jd_seen.add(skill_lower)
                
                # Clean Resume skills - remove duplicates and garbage
                resume_skills_clean = []
                resume_seen = set()
                for skill in normalized_resume.get("skills", []):
                    skill_lower = str(skill).strip().lower()
                    if skill_lower and skill_lower not in GARBAGE_VALUES and skill_lower not in resume_seen and len(skill_lower) > 1:
                        resume_skills_clean.append(skill_lower)
                        resume_seen.add(skill_lower)
                
                # Final clean JSON structures
                jd_json["skills"] = jd_skills_clean
                
                resume_json = {
                    "skills": resume_skills_clean,
                    "projects": normalized_resume.get("projects", []) if isinstance(normalized_resume.get("projects"), list) else [],
                    "experience_years": normalized_resume.get("experience_years", 0) if isinstance(normalized_resume.get("experience_years"), (int, float)) else 0
                }

                # ========================================
                # 🔥 CALCULATE FINAL PERCENTAGE
                # ========================================
                final_percentage = calculate_match_percentage(jd_json, resume_json)
                
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
                print("=" * 70 + "\n")

                match_results.append({
                    "name": r[1],
                    "email": r[2],
                    "match": final_percentage,  # <--- Ye 'match' key hona zaroori hai
                    "match_percentage": final_percentage,  # For consistency
                    "suggestions": ai_raw.get("explanation", ""),
                    "matched_skills": matched_skills_for_ui,
                    "missing_skills": [],
                    "summary": r[6] if len(r) > 6 else ""
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


@app.route("/uploads/<filename>")
def serve_upload(filename):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    try:
        uploads_dir = app.config['UPLOAD_FOLDER']
        file_path = os.path.join(uploads_dir, filename)
        
        if os.path.exists(file_path):
            return send_from_directory(uploads_dir, filename)
        else:
            print(f"File not found: {file_path}")
            flash("Resume file not found", "error")
            return redirect(url_for("admin_dashboard"))
            
    except Exception as e:
        print(f"Error serving file: {e}")
        flash("Error opening resume file", "error")
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/db-check")
def admin_db_check():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    from database import get_all_resumes
    resumes = get_all_resumes()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Check</title>
        <style>
            body {{ font-family: Arial; margin: 20px; }}
            table {{ border: 1px solid #ccc; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; }}
            th {{ background: #f0f0f0; }}
        </style>
    </head>
    <body>
        <h1>🗄️ Database Check</h1>
        <p>Total Resumes: {len(resumes)}</p>
        <a href="/admin/dashboard">← Back to Dashboard</a>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>File</th>
                <th>Summary</th>
            </tr>
    """
    
    for resume in resumes:
        html += f"""
            <tr>
                <td>{resume[0]}</td>
                <td>{resume[1]}</td>
                <td>{resume[2]}</td>
                <td>{resume[3] or 'N/A'}</td>
                <td>{resume[5] or 'No file'}</td>
                <td>{(resume[6] or '')[:50] + '...' if resume[6] else 'No summary'}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html


@app.route("/admin/export-db")
def export_database():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    import csv
    from io import StringIO
    from database import get_all_resumes
    from flask import send_file
    
    resumes = get_all_resumes()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Photo', 'File Path', 'Summary'])
    
    for resume in resumes:
        writer.writerow([
            resume[0],
            resume[1],
            resume[2],
            resume[3] or '',
            resume[4] or '',
            resume[5] or '',
            resume[6] or ''
        ])
    
    output.seek(0)
    response = send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='resumes_database.csv'
    )
    
    return response


@app.route("/api/get_matches/<int:job_id>")
def api_get_matches(job_id):
    matches = get_job_matches(job_id)
    return jsonify(matches)


# =========================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)