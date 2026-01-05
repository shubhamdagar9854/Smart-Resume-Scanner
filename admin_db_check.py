# 🔍 Database Check via Admin Dashboard
# Add this to app.py for database viewing

@app.route("/admin/db-check")
def admin_db_check():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    from database import get_all_resumes
    resumes = get_all_resumes()
    
    # Create HTML table
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Check</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            table { border: 1px solid #ccc; width: 100%; }
            th, td { border: 1px solid #ccc; padding: 8px; }
            th { background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>🗄️ Database Check</h1>
        <p>Total Resumes: {}</p>
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
    """.format(len(resumes))
    
    for resume in resumes:
        html += """
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>
        """.format(
            resume[0], resume[1], resume[2], 
            resume[3] or 'N/A', 
            resume[5] or 'No file', 
            (resume[6] or '')[:50] + '...' if resume[6] else 'No summary'
        )
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html
