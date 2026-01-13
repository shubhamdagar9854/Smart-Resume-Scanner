import os
import re
import PyPDF2
import docx

# =====================================================
# ENV CHECK
# =====================================================
IS_PRODUCTION = os.environ.get('RENDER') or not os.system(
    'which ollama > /dev/null 2>&1'
) == 0

if not IS_PRODUCTION:
    import ollama


# =====================================================
# SAFETY HELPERS (NO PHONE / EMAIL EVER)
# =====================================================
def contains_phone_or_email(text: str) -> bool:
    if re.search(r'\b\d{8,}\b', text):  # 8+ digit numbers
        return True
    if re.search(r'\w+@\w+\.\w+', text):
        return True
    if any(x in text.lower() for x in ['gmail', 'yahoo', 'hotmail', '@']):
        return True
    return False


# =====================================================
# RESUME TEXT EXTRACTION
# =====================================================
def get_text_from_resume(file_path):
    text = ""
    try:
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            parts = []

            for para in doc.paragraphs:
                if para.text.strip():
                    parts.append(para.text.strip())

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            parts.append(cell.text.strip())

            text = "\n".join(parts)

        return text if text.strip() else None

    except Exception:
        return None


# =====================================================
# TECH STACK RATINGS (FIXED & SAFE)
# =====================================================
def extract_tech_ratings(text):
    tech_ratings = []

    ALLOWED_TECH = [
        'python', 'java', 'javascript', 'react', 'node', 'angular', 'vue',
        'django', 'flask', 'sql', 'mysql', 'mongodb', 'aws',
        'docker', 'git', 'api', 'html', 'css'
    ]

    pattern = r'(python|java|javascript|react|node|angular|vue|django|flask|sql|mysql|mongodb|aws|docker|git|html|css)\s*[:\-]?\s*([⭐★☆●○•\d]{1,10})'

    matches = re.findall(pattern, text, re.IGNORECASE)

    for tech, rating in matches:
        tech = tech.lower().strip()
        rating = rating.strip()

        combined = f"{tech} {rating}"

        # 🔒 HARD BLOCK
        if contains_phone_or_email(combined):
            continue

        if tech not in ALLOWED_TECH:
            continue

        tech_ratings.append(f"📊 {tech.title()}: {rating}")

    return tech_ratings[:3]


# =====================================================
# DOMAIN EXTRACTION
# =====================================================
def extract_domain_info(text):
    domains = [
        'fintech', 'healthcare', 'education',
        'ecommerce', 'banking', 'startup'
    ]
    text_lower = text.lower()

    for d in domains:
        if d in text_lower:
            return f"🏢 Domain Expertise: {d.title()} industry"

    return None


# =====================================================
# PROJECT EXTRACTION
# =====================================================
def extract_projects_info(text):
    if 'project' in text.lower():
        return "🚀 Projects: Hands-on project development experience"
    return None


# =====================================================
# RESUME SUMMARY (SLIGHTLY EXPANDED)
# =====================================================
def create_resume_summary(text):
    if not text or len(text.strip()) < 20:
        return "• No valid resume content found"

    bullets = []

    tech = extract_tech_ratings(text)
    domain = extract_domain_info(text)
    projects = extract_projects_info(text)

    bullets.extend(tech)

    if domain:
        bullets.append(domain)

    if projects:
        bullets.append(projects)

    text_lower = text.lower()

    if 'experience' in text_lower:
        bullets.append("💼 Demonstrated professional experience in relevant technical roles.")

    if any(x in text_lower for x in ['developer', 'engineer']):
        bullets.append("👨‍💻 Worked as a software developer/engineer on real-world applications.")

    if any(x in text_lower for x in ['api', 'backend', 'server']):
        bullets.append("🔗 Experience in backend development and API integration.")

    if any(x in text_lower for x in ['frontend', 'react', 'ui']):
        bullets.append("🎨 Hands-on experience with frontend technologies and UI development.")

    if any(x in text_lower for x in ['database', 'sql', 'mongodb']):
        bullets.append("🗄️ Strong understanding of databases and data management.")

    if any(x in text_lower for x in ['cloud', 'aws', 'deployment']):
        bullets.append("☁️ Exposure to cloud platforms and application deployment.")

    if len(bullets) < 5:
        bullets.append("Skilled professional with a strong technical foundation.")

    return "• " + "\n• ".join(bullets[:10])


# =====================================================
# JOB MATCHING
# =====================================================
def match_resume_with_job(resume_summary, job_title, job_description):

    if IS_PRODUCTION:
        job_text = f"{job_title} {job_description}".lower()
        resume_text = resume_summary.lower()

        keywords = [
            'python', 'java', 'react', 'sql',
            'aws', 'docker', 'git', 'agile',
            'bsc', 'msc'
        ]

        matched = [k for k in keywords if k in job_text and k in resume_text]
        percent = int((len(matched) / max(len(keywords), 1)) * 100)

        return f"Match: {percent}% | Skills: {', '.join(matched)}"

    prompt = f"""
    JOB TITLE: {job_title}
    JOB DESCRIPTION: {job_description}

    CANDIDATE SUMMARY:
    {resume_summary}

    Provide:
    1. Match %
    2. Key reasons
    3. Final verdict
    """

    try:
        res = ollama.generate(model='llama3', prompt=prompt)
        return res['response']
    except Exception:
        return "AI matching failed"
