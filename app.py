from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import threading
from werkzeug.utils import secure_filename

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
        file = request.files.get("resume")

        if not file or file.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file type", "error")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        resume_id = add_resume(
            name=name,
            email=email,
            file_path=filepath,  
            summary="Processing summary..."
        )


        thread = threading.Thread(
            target=generate_summary_in_background,
            args=(app, resume_id, filepath, name)
        )
        thread.start()

        flash("Resume uploaded successfully!", "success")
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

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        resumes = filter_resumes_by_keyword(keyword) if keyword else get_all_resumes()
    else:
        resumes = get_all_resumes()

    return render_template("admin_dashboard.html", resumes=resumes)


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


@app.route("/api/get_matches/<int:job_id>")
def api_get_matches(job_id):
    matches = get_job_matches(job_id)
    return jsonify(matches)


# =========================
if __name__ == "__main__":
    app.run(debug=True)
