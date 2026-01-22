import os
from flask import Flask, request, render_template, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# RENDER PE UPLOADS FOLDER FIX
UPLOAD_FOLDER = '/tmp/uploads' # Render/Cloud par /tmp use karna best hota hai
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Check karo ki kya file aayi hai (name attribute 'resume_file' hai index.html mein)
        if 'resume_file' not in request.files:
            flash("No file part")
            return redirect(url_for('upload_file'))
        
        file = request.files['resume_file']
        
        if file.filename == '':
            flash("No selected file")
            return redirect(url_for('upload_file'))

        if file and allowed_file(file.filename):
            # File ko safe location pe save karo
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # ABHI KE LIYE SIRF SUCCESS MESSAGE DIKHAO (AI CALL MAT KARNA)
            flash(f"File {file.filename} uploaded successfully!")
            return redirect(url_for('upload_file'))
        else:
            flash("Invalid file type!")
            return redirect(url_for('upload_file'))
            
    return render_template("index.html")

# Admin routes (simplified)
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin":
            session["admin_logged_in"] = True
            flash("Login successful", "success")
            return redirect("/admin/dashboard")
        else:
            flash("Invalid credentials", "error")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")
    return "<h1>Admin Dashboard - Working!</h1><a href='/admin/logout'>Logout</a>"

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out", "success")
    return redirect("/admin/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
