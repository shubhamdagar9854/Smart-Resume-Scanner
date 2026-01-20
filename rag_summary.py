import json
import requests
import re
import pdfplumber
import docx
import os

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

def extract_text_from_resume(file_path):
    text = ""
    try:
        if file_path.endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Extraction Error: {e}")
    
    return text.strip() if text.strip() else "No text found"

def analyze_resume_text(text):
    # Standard technical skills list for manual backup
    skills_db = ['python', 'java', 'flask', 'sql', 'javascript', 'node', 'react', 'html', 'css', 'mongodb', 'express', 'git', 'docker']
    found_skills = set()

    # 1. Logic Check (Regex)
    for skill in skills_db:
        if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
            found_skills.add(skill.title())

    # 2. AI Check (Mistral)
    client = MistralClient()
    prompt = f"Identify technical skills in this text and return only a JSON with 'skills' list: {text[:2000]}"
    try:
        raw_res = client.generate(prompt)
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            ai_data = json.loads(match.group(0))
            for s in ai_data.get("skills", []):
                found_skills.add(s.title())
    except:
        pass

    return {"skills": list(found_skills)}

def analyze_job_text(text):
    # Job description se skills nikalne ke liye dynamic cleaning
    # Split by comma, space or newline
    potential_skills = re.split(r'[,\n\s/]', text.lower())
    common_tech = {'python', 'java', 'flask', 'sql', 'javascript', 'react', 'node', 'html', 'css', 'mongodb', 'docker', 'aws'}
    
    found = set()
    for word in potential_skills:
        word = word.strip('.,()')
        if word in common_tech or len(word) > 2: # Length check to avoid garbage
            if len(word) > 1: found.add(word.title())

    return {"skills": list(found), "must_have": list(found)}

def match_resume_with_job(resume_text, job_text):
    resume_data = analyze_resume_text(resume_text)
    job_data = analyze_job_text(job_text)
    return {
        "resume_data": resume_data, 
        "job_data": job_data,
        "explanation": "Matching based on detected keywords and AI parsing."
    }

def calculate_match_percentage(jd_json, resume_json):
    # Ensuring keys are handled correctly from app.py
    j_skills = set([str(s).lower().strip() for s in jd_json.get("skills", jd_json.get("must_have", []))])
    r_skills = set([str(s).lower().strip() for s in resume_json.get("skills", [])])
    
    if not j_skills: return 0.0
    matched = j_skills.intersection(r_skills)
    score = (len(matched) / len(j_skills)) * 100
    return round(float(score), 2)

# --- APP.PY COMPATIBILITY STUBS ---
def analyze_resume_with_rules(text): return analyze_resume_text(text)
def normalize_resume_json(data): return data

# =====================================================
# ENHANCED RESUME SUMMARY GENERATOR
# =====================================================
def generate_professional_summary(resume_text: str) -> str:
    """
    Generate comprehensive professional summary from resume
    Includes: Roles, Tech Stack, Domain, Certificates, Skills, Hobbies
    """
    
    resume_lower = resume_text.lower()
    summary_parts = []
    
    # ========================================
    # 1️⃣ EXTRACT PREVIOUS ROLES
    # ========================================
    roles = []
    role_keywords = [
        'software engineer', 'developer', 'senior developer', 'lead developer',
        'full stack', 'frontend', 'backend', 'data scientist', 'analyst',
        'project manager', 'team lead', 'architect', 'consultant',
        'intern', 'junior developer', 'ml engineer', 'devops engineer'
    ]
    
    for role in role_keywords:
        if role in resume_lower:
            roles.append(role.title())
    
    # Remove duplicates while preserving order
    roles = list(dict.fromkeys(roles))
    
    if roles:
        summary_parts.append(f"• Professional with experience as {', '.join(roles[:3])}")
    
    # ========================================
    # 2️⃣ EXTRACT TECH STACK & EXPERIENCE
    # ========================================
    tech_stack = {
        'Languages': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'ruby', 'php', 'typescript'],
        'Frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node', 'express'],
        'Databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle'],
        'Cloud/DevOps': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git'],
        'AI/ML': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp']
    }
    
    found_tech = {}
    for category, techs in tech_stack.items():
        found = [tech for tech in techs if tech in resume_lower]
        if found:
            found_tech[category] = found
    
    if found_tech:
        tech_summary = []
        for category, techs in found_tech.items():
            if techs:
                tech_summary.append(f"{', '.join(techs[:3])}")
        
        if tech_summary:
            summary_parts.append(f"• Proficient in {' | '.join(tech_summary[:2])} with hands-on experience")
    
    # ========================================
    # 3️⃣ EXTRACT DOMAIN EXPERTISE
    # ========================================
    domains = {
        'fintech': ['fintech', 'finance', 'banking', 'payment'],
        'healthcare': ['healthcare', 'medical', 'health'],
        'e-commerce': ['e-commerce', 'ecommerce', 'retail', 'shopping'],
        'education': ['education', 'edtech', 'learning'],
        'enterprise': ['enterprise', 'b2b', 'saas'],
        'gaming': ['gaming', 'game development'],
        'data analytics': ['analytics', 'data science', 'bi']
    }
    
    found_domains = []
    for domain, keywords in domains.items():
        if any(kw in resume_lower for kw in keywords):
            found_domains.append(domain.title())
    
    if found_domains:
        summary_parts.append(f"• Domain expertise in {', '.join(found_domains[:2])}")
    
    # ========================================
    # 4️⃣ EXTRACT CERTIFICATIONS
    # ========================================
    cert_keywords = [
        'certified', 'certification', 'aws certified', 'azure certified',
        'google cloud', 'pmp', 'scrum master', 'csm', 'comptia',
        'cissp', 'ceh', 'oracle certified', 'microsoft certified'
    ]
    
    certifications = []
    for cert in cert_keywords:
        if cert in resume_lower:
            # Extract the line containing certification
            for line in resume_text.split('\n'):
                if cert in line.lower():
                    certifications.append(line.strip()[:50])
                    break
    
    if certifications:
        summary_parts.append(f"• Certified professional: {certifications[0]}")
    
    # ========================================
    # 5️⃣ EXTRACT CROSS-FUNCTIONAL EXPERIENCE
    # ========================================
    cross_functional = []
    cf_keywords = {
        'team collaboration': ['collaboration', 'cross-functional', 'team work'],
        'agile methodologies': ['agile', 'scrum', 'kanban', 'sprint'],
        'client interaction': ['client', 'stakeholder', 'customer facing'],
        'leadership': ['led team', 'managed team', 'mentored', 'leadership'],
        'project management': ['project management', 'delivery', 'roadmap']
    }
    
    for skill, keywords in cf_keywords.items():
        if any(kw in resume_lower for kw in keywords):
            cross_functional.append(skill)
    
    if cross_functional:
        summary_parts.append(f"• Experience in {', '.join(cross_functional[:2])}")
    
    # ========================================
    # 6️⃣ EXTRACT INTERPERSONAL SKILLS
    # ========================================
    soft_skills = []
    skill_keywords = {
        'communication': ['communication', 'presentation', 'documentation'],
        'problem-solving': ['problem solving', 'analytical', 'critical thinking'],
        'adaptability': ['adaptable', 'flexible', 'quick learner'],
        'time management': ['time management', 'prioritization', 'multitasking']
    }
    
    for skill, keywords in skill_keywords.items():
        if any(kw in resume_lower for kw in keywords):
            soft_skills.append(skill)
    
    if soft_skills:
        summary_parts.append(f"• Strong {', '.join(soft_skills[:2])} skills")
    
    # ========================================
    # 7️⃣ EXTRACT HOBBIES/INTERESTS
    # ========================================
    hobbies = []
    hobby_keywords = [
        'reading', 'writing', 'blogging', 'open source', 'contributing',
        'hackathon', 'coding competitions', 'sports', 'travel',
        'photography', 'music', 'volunteering'
    ]
    
    for hobby in hobby_keywords:
        if hobby in resume_lower:
            hobbies.append(hobby)
    
    if hobbies:
        summary_parts.append(f"• Interests: {', '.join(hobbies[:3])}")
    
    # ========================================
    # 8️⃣ EXTRACT YEARS OF EXPERIENCE
    # ========================================
    experience_years = 0
    exp_patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
        r'experience\s*:?\s*(\d+)\+?\s*(?:years?|yrs?)'
    ]
    
    for pattern in exp_patterns:
        match = re.search(pattern, resume_lower)
        if match:
            experience_years = int(match.group(1))
            break
    
    # ========================================
    # 🎯 BUILD FINAL SUMMARY
    # ========================================
    if not summary_parts:
        return "• Technology professional with comprehensive software development expertise"
    
    # Add experience header if found
    if experience_years > 0:
        header = f"• {experience_years}+ years of professional experience\n"
        return header + "\n".join(summary_parts)
    
    return "\n".join(summary_parts)

def get_resume_summary(text): 
    return generate_professional_summary(text)