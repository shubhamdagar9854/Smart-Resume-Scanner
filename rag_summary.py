import json
import requests
import re
import pdfplumber
from PyPDF2 import PdfReader
import docx

class MistralClient:
    def __init__(self, model="llama3.2:1b"):
        self.model = model
        self.base_url = "http://localhost:11434/api/generate"
    
    def generate(self, prompt):
        try:
            response = requests.post(self.base_url, 
                json={"model": self.model, "prompt": prompt, "stream": False}, 
                timeout=15)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except:
            return ""
        return ""

def analyze_resume_text(text):
    # 1. PEHLE: AI se nikalne ki koshish (Mistral)
    # 2. SAATH MEIN: Manual check (Regex) taaki agar AI miss kare toh hum pakad lein
    
    common_skills = ['python', 'java', 'flask', 'sql', 'javascript', 'node', 'react', 'html', 'css', 'mongodb']
    found_skills = set()

    # Manual extraction (Pure Logic)
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
            found_skills.add(skill.title())

    # AI extraction (Mistral)
    client = MistralClient()
    prompt = f"Extract only technical skills as a JSON list from this text: {text[:4000]}"
    try:
        raw_res = client.generate(prompt)
        # JSON extract karne ka logic yahan aayega
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            ai_data = json.loads(match.group(0))
            ai_skills = ai_data.get("skills", [])
            # AI skills ko manual skills ke saath merge karo
            for skill in ai_skills:
                found_skills.add(skill.title())
    except:
        pass

    return {"skills": list(found_skills)} # Dono ka mix return karo

# --- APP.PY COMPATIBILITY FUNCTIONS ---
def analyze_resume_with_rules(text): return analyze_resume_text(text)
def normalize_resume_json(data): return data

def extract_text_from_resume(file_path):
    """Extract text from PDF or DOCX using pdfplumber for better accuracy"""
    text = ""
    try:
        if file_path.endswith('.pdf'):
            # pdfplumber complex layouts ke liye best hai
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        print(f"Extraction Error: {e}")
        return "resume text available"
    
    return text.strip()

# Additional compatibility functions for app.py
def analyze_job_text(text):
    """Simple job analysis for compatibility"""
    skills_db = ["python", "flask", "sql", "java", "javascript", "react", "node", "aws", "docker"]
    found = [s.title() for s in skills_db if s in text.lower()]
    return {"must_have": found, "experience_years_required": 2}

def match_resume_with_job(resume_text, job_text):
    """Simple matching for compatibility"""
    resume_data = analyze_resume_text(resume_text)
    job_data = analyze_job_text(job_text)
    return {"resume_data": resume_data, "job_data": job_data}

def calculate_match_percentage(jd_json, resume_json):
    """
    PURE DETERMINISTIC CALCULATION
    Ensures that if Python is in JD and Resume, score is NOT 0.
    """
    # 1. Extract and Clean Skills
    jd_skills = set([str(s).lower().strip() for s in jd_json.get("skills", [])])
    res_skills = set([str(s).lower().strip() for s in resume_json.get("skills", [])])
    
    if not jd_skills:
        return 0.0

    # 2. Match Skills
    matched_skills = jd_skills.intersection(res_skills)
    
    # 3. Calculate Base Score (Skills only for now to keep it simple)
    # Formula: (Matched / Total Required) * 100
    score = (len(matched_skills) / len(jd_skills)) * 100
    
    # 4. Optional: Add Experience Weight if needed
    # (Abhi ke liye sirf skills rakhte hain taaki 0% na aaye)
    
    print(f"--- MATCH ENGINE DEBUG ---")
    print(f"JD Skills: {jd_skills}")
    print(f"Resume Skills: {res_skills}")
    print(f"Matched: {matched_skills}")
    print(f"Final Score: {round(score, 2)}%")
    print(f"--------------------------")
    
    return round(float(score), 2)

def calculate_match_score(resume_data, job_data):
    # 1. Skills ko clean list mein convert karo
    # Resume skills extract karo
    r_skills = [s.lower().strip() for s in resume_data.get("skills", [])]
    
    # JD skills extract karo (Check both 'must_have' and 'skills' keys)
    j_skills = job_data.get("must_have", [])
    if not j_skills:
        j_skills = job_data.get("skills", [])
        
    j_skills = [s.lower().strip() for s in j_skills]

    print(f"DEBUG: Comparing Resume {r_skills} with JD {j_skills}") # Terminal mein dikhega

    # 2. Match nikaalo
    matched = [s for s in j_skills if s in r_skills]
    
    # 3. Score Calculate Karo
    total_required = len(j_skills)
    if total_required == 0:
        score = 0
    else:
        # Score ko 100 se multiply karna mat bhulna
        score = round((len(matched) / total_required) * 100, 2)

    print(f"DEBUG: Matched count: {len(matched)}, Total: {total_required}, Score: {score}")

    # 4. Result Return Karo (Make sure keys match what app.py expects)
    return {
        "total_score": float(score),  # Ensure it's a number
        "match_percentage": float(score), # Backup key
        "matched_skills": matched,
        "match_type": "EXCELLENT" if score > 75 else "GOOD" if score > 40 else "POOR"
    }

def get_resume_summary(text):
    """Compatibility function"""
    return analyze_resume_text(text)

def generate_match_explanation(r, j, s):
    """Simple explanation for compatibility"""
    return "Skills-based analysis completed."

def normalize_skills(skills):
    """Normalize skills for compatibility"""
    if not skills:
        return []
    return list(set([s.lower().strip() for s in skills if s]))
