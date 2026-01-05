from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import os
import threading
from werkzeug.utils import secure_filename

# Production environment setup
if os.environ.get('FLASK_ENV') == 'production':
    debug_mode = False
else:
    debug_mode = True

from ollama_service import (
    get_text_from_resume,
    create_resume_summary,
    match_resume_with_job
)

from database import (
    add_job_post,
    get_all_job_posts,
    get_job_post_by_id,
    add_resume,
    get_all_resumes,
    get_resume_by_id,
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


def generate_summary_in_background(app, resume_id, filepath, name):
    with app.app_context():
        print("BACKGROUND SUMMARY STARTED")
        print(f"Processing resume ID: {resume_id}")
        print(f"File path: {filepath}")

        try:
            text = get_text_from_resume(filepath)
            print(f"Extracted text length: {len(text) if text else 0}")

            if not text:
                print("No text extracted from resume")
                update_resume_summary(resume_id, "Failed to extract resume text")
                return

            summary = create_resume_summary(text)
            print(f"Generated summary: {summary[:100]}...")

            if not summary:
                print("Summary generation failed")
                update_resume_summary(resume_id, f"{name} - Resume uploaded successfully. Processing complete.")
            else:
                update_resume_summary(resume_id, summary)
                print("SUMMARY UPDATED SUCCESSFULLY")

        except Exception as e:
            print(f"ERROR in background processing: {e}")
            update_resume_summary(resume_id, f"Error: {str(e)}")


# =========================
# ROUTES
# =========================

@app.route("/", methods=["GET", "POST"])
def home():
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
            resume_text = get_text_from_resume(file_path)
            summary = ""

            if resume_text:
                try:
                    summary = create_resume_summary(resume_text)
                except Exception as e:
                    print(f"Summary generation failed: {e}")
                    summary = "Summary generation failed. Please check resume file."
            else:
                summary = "Could not extract text from resume. Please check file format."

            # Add to database
            add_resume(name, email, phone, "", file_path, summary)

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
    
    # Get all resumes (no search functionality)
    resumes = get_all_resumes()
    
    print(f"DEBUG: Total resumes found: {len(resumes)}")
    for r in resumes:
        print(f"DEBUG: Resume - ID: {r[0]}, Name: {r[1]}")
    
    # Pagination logic
    total = len(resumes)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_resumes = resumes[start:end]
    
    print(f"DEBUG: Paginated resumes: {len(paginated_resumes)}")
    
    # Calculate pagination info
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
# JOB POSTS
# =========================

@app.route("/admin/jobs", methods=["GET", "POST"])
def admin_jobs():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if title and description:
            add_job_post(title, description)
            flash("Job posted successfully", "success")

    # Sirf LATEST job post lena hai
    posts = get_all_job_posts()
    latest_post = posts[0] if posts else None
    
    jobs_with_matches = []
    if latest_post:
        matches = get_job_matches(latest_post[0])
        jobs_with_matches.append({
            "job": latest_post,
            "matches": matches
        })

    return render_template(
        "admin_jobs.html",
        jobs_with_matches=jobs_with_matches
    )



@app.route("/admin/job/<int:post_id>")
def admin_job_matches(post_id):
    return redirect(url_for("admin_jobs"))



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
        # Handle both production and local paths
        uploads_dir = app.config['UPLOAD_FOLDER']
        file_path = os.path.join(uploads_dir, filename)
        
        print(f"Serving file: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
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


@app.route("/admin/database-info")
def admin_database_info():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    from database import get_all_resumes
    resumes = get_all_resumes()
    
    return render_template("database_info.html", resumes=resumes)


@app.route("/api/get_matches/<int:job_id>")
def api_get_matches(job_id):
    matches = get_job_matches(job_id)
    return jsonify(matches)


# =========================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
    

