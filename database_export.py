# 📤 Database Export Feature

@app.route("/admin/export-db")
def export_database():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    import csv
    from io import StringIO
    from database import get_all_resumes
    
    resumes = get_all_resumes()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Photo', 'File Path', 'Summary'])
    
    # Data
    for resume in resumes:
        writer.writerow([
            resume[0],  # ID
            resume[1],  # Name
            resume[2],  # Email
            resume[3] or '',  # Phone
            resume[4] or '',  # Photo
            resume[5] or '',  # File Path
            resume[6] or ''   # Summary
        ])
    
    # Create response
    output.seek(0)
    response = send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='resumes_database.csv'
    )
    
    return response
