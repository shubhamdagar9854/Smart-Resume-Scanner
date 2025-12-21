
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from werkzeug.utils import secure_filename
from database import init_db, add_resume, get_all_resumes, verify_admin, filter_resumes_by_post, update_resume_summary
from ollama_service import get_text_from_resume, create_resume_summary, match_resume_with_job

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  


UPLOAD_FOLDER = 'uploads'  # Resumes yahan save honge
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}  # Sirf ye file types allow
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database on startup
init_db()

def allowed_file(filename):
    if '.' not in filename:
        return False
    
    ext = filename.split('.')[-1].lower()
    if ext in ALLOWED_EXTENSIONS:
        return True
    else:
        return False

# ============================================
# ROUTES - Different Pages Ke Liye
# ============================================

# Route 1: Home Page - User Resume Upload Form
@app.route("/", methods=['GET', 'POST'])
def home():
    # Agar user ne form submit kiya hai (POST request)
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        
        # Check if file is present
        if 'resume' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['resume']
        
        # Check if file is selected
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        # Check if file is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Save to database (summary will be generated later by admin from dashboard)
            # Summary generation removed from upload to make it faster
            resume_id = add_resume(name, email, filepath, summary=None)
            
            # Print information
            print(f"Name: {name}")
            print(f"Email: {email}")
            print(f"File: {filename}")
            print(f"Resume ID: {resume_id}")
            
            flash(f'Resume uploaded successfully! Thank you {name}!', 'success')
            return redirect(url_for('home'))
        else:
            # Agar file type galat hai to error dikhao
            flash('Invalid file type! Only PDF, DOC, DOCX files are allowed.', 'error')
            return redirect(request.url)
    
    # Agar GET request hai to form page dikhao
    return render_template('index.html')

# Route 2: Admin Login Page
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Agar admin ne login form submit kiya hai
    if request.method == 'POST':
        # Step 1: Form se username aur password lelo
        admin_username = request.form.get('username')
        admin_password = request.form.get('password')
        
        # Step 2: Database mein check karo ki credentials sahi hain ya nahi
        is_valid_admin = verify_admin(admin_username, admin_password)
        
        if is_valid_admin:
            # Step 3: Agar sahi hai to session mein login status save karo
            session['admin_logged_in'] = True
            session['admin_username'] = admin_username
            
            # Step 4: Success message dikhao
            flash('Login successful!', 'success')
            
            # Step 5: Dashboard par redirect karo
            return redirect(url_for('admin_dashboard'))
        else:
            # Agar galat credentials hain to error dikhao
            flash('Invalid username or password!', 'error')
    
    # Agar GET request hai to login page dikhao
    return render_template('admin_login.html')

# Route 3: Admin Logout
@app.route('/admin/logout')
def admin_logout():
    # Step 1: Session se login status hata do
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    
    # Step 2: Success message dikhao
    flash('Logged out successfully!', 'success')
    
    # Step 3: Login page par redirect karo
    return redirect(url_for('admin_login'))

# Route 4: Admin Dashboard - Sabhi Resumes Dikhane Ke Liye
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # Step 1: Check karo ki admin login hai ya nahi
    is_admin_logged_in = session.get('admin_logged_in')
    
    if not is_admin_logged_in:
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    # Step 2: Sabhi resumes dikhao (GET request ya empty POST)
    # Agar POST request hai aur search kiya hai to filter karo
    if request.method == 'POST':
        # Form se post type lelo (jaise "Software Engineer")
        searched_post_type = request.form.get('post_type', '').strip()
        
        # Agar kuch search kiya hai
        if searched_post_type:
            # Step 3: Database se matching resumes nikalo
            all_matching_resumes = filter_resumes_by_post(searched_post_type)
            
            # Step 4: Ollama se check karo ki kaun se candidates perfect match hain
            perfect_match_resumes = []
            
            for each_resume in all_matching_resumes:
                resume_summary = each_resume[4]  # Summary index 4 par hai (id, name, email, file_path, summary, post_type)
                
                # Agar summary hai to Ollama se match check karo
                if resume_summary and resume_summary != "Ollama AI is not running.":
                    ollama_match_result = match_resume_with_job(resume_summary, searched_post_type)
                    
                    # Agar Ollama ne YES kaha to perfect match hai
                    if 'YES' in ollama_match_result.upper() or 'SUITABLE' in ollama_match_result.upper():
                        perfect_match_resumes.append(each_resume)
                else:
                    # Agar summary nahi hai to bhi add karo
                    perfect_match_resumes.append(each_resume)
            
            # Final list - perfect matches ya sab matching resumes
            final_resumes_list = perfect_match_resumes if perfect_match_resumes else all_matching_resumes
        else:
            # Agar kuch search nahi kiya to sabhi resumes dikhao
            final_resumes_list = get_all_resumes()
    else:
        # Agar GET request hai to sabhi resumes dikhao
        final_resumes_list = get_all_resumes()
    
    # Step 5: Dashboard page dikhao with resumes list
    return render_template('admin_dashboard.html', resumes=final_resumes_list)

# Route 5: Resume Summary Generate Karne Ke Liye (Agar Pehle Se Na Ho)
@app.route('/admin/generate_summary/<int:resume_id>')
def generate_resume_summary(resume_id):
    # Step 1: Check karo ki admin login hai
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    # Step 2: Database se resume details lelo
    from database import get_resume_by_id
    resume_data = get_resume_by_id(resume_id)
    
    # Step 3: Agar resume mila hai
    if resume_data:
        resume_file_path = resume_data[3]  # File path 3rd index par hai
        
        # Step 4: Resume se text extract karo
        extracted_resume_text = get_text_from_resume(resume_file_path)
        
        # Step 5: Agar text extract ho gaya
        if extracted_resume_text:
            # Step 6: Ollama se summary generate karo
            new_summary = create_resume_summary(extracted_resume_text)
            
            # Step 7: Database mein summary update karo
            update_resume_summary(resume_id, new_summary)
            
            flash('Summary generated successfully!', 'success')
        else:
            # Agar text extract nahi ho paya
            flash('Unable to extract text from resume!', 'error')
    
    # Step 8: Dashboard par wapas redirect karo
    return redirect(url_for('admin_dashboard'))


if __name__ == "__main__":
    app.run(debug=True)