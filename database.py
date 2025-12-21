import sqlite3

# Database ka naam
DB_NAME = "resumes.db"


# 🔹 Database aur tables banana
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Resume table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            file_path TEXT,
            summary TEXT,
            post_type TEXT
        )
    """)

    # Admin table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    # Default admin insert (agar admin nahi hai)
    cur.execute("SELECT * FROM admin")
    admin = cur.fetchone()

    if admin is None:
        cur.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )

    conn.commit()
    conn.close()


# 🔹 Resume add karna
def add_resume(name, email, file_path, summary=None, post_type=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO resumes (name, email, file_path, summary, post_type) VALUES (?, ?, ?, ?, ?)",
        (name, email, file_path, summary, post_type)
    )

    conn.commit()
    resume_id = cur.lastrowid
    conn.close()
    return resume_id


# 🔹 Saare resumes lana
def get_all_resumes():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM resumes ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()
    return data


# 🔹 Ek resume ID se lana
def get_resume_by_id(resume_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
    data = cur.fetchone()

    conn.close()
    return data


# 🔹 Admin login check
def verify_admin(username, password):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM admin WHERE username = ? AND password = ?",
        (username, password)
    )

    admin = cur.fetchone()
    conn.close()

    if admin:
        return True
    else:
        return False


# 🔹 Resume filter (post type se)
def filter_resumes_by_post(post_type):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM resumes WHERE post_type LIKE ? OR summary LIKE ?",
        ('%' + post_type + '%', '%' + post_type + '%')
    )

    data = cur.fetchall()
    conn.close()
    return data


# 🔹 Resume summary update karna
def update_resume_summary(resume_id, summary):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "UPDATE resumes SET summary = ? WHERE id = ?",
        (summary, resume_id)
    )

    conn.commit()
    conn.close()
