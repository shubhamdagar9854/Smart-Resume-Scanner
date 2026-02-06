import json
import re
import os
import time
import PyPDF2
from google import genai  
from dotenv import load_dotenv

load_dotenv()

# Gemini API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-api-key-here')

# Gemini client initialize (new syntax)
client = genai.Client(api_key=GEMINI_API_KEY)

# Model name
MODEL_NAME = 'models/gemini-2.5-flash'

# 1. Model Load karne ka function
def load_mistral_model():
    print("✅ Gemini API ready!")
    print("🌐 Using Google Gemini 2.0 Flash (Free tier)")
    return True

# 2. AI Summary banane ka function
def generate_professional_summary(resume_text: str) -> str:
    prompt = f"""
    Create EXACTLY 5 bullet point professional resume summary:
    
    Resume content: {resume_text[:5000]}
    
    Requirements:
    - Professional language
    - Key skills first
    - Experience summary  
    - Technical expertise
    - Soft skills last
    - Start each bullet with strong verb/action word
    
    Format exactly like this:
    * Skilled in [technologies]
    * Experienced [role] with expertise in  
    * Strong [skill] skills
    * Proficient in [methodologies/tools]  
    * Excellent [soft skill]
    
    Return ONLY the 5 bullet points, nothing else.
    """
    
    # Retry logic for 503 errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            
            # If model overloaded (503), wait and retry
            if '503' in error_msg or 'UNAVAILABLE' in error_msg:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                    print(f"Model busy, retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            
            # If quota exceeded (429), use fallback summary
            if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                return generate_fallback_summary(resume_text)
            
            # For other errors, return error message
            return f"Error generating summary: {error_msg}"
    
    # If all retries failed, use fallback
    return generate_fallback_summary(resume_text)


def generate_fallback_summary(resume_text: str) -> str:
    """Simple fallback summary when API fails"""
    lines = resume_text.split('\n')
    
    # Extract basic info
    skills = []
    experience = []
    
    for line in lines:
        line_lower = line.lower()
        if any(tech in line_lower for tech in ['java', 'python', 'sql', 'spring', 'docker', 'aws', 'kubernetes']):
            if len(line.strip()) < 100:
                skills.append(line.strip())
        if any(word in line_lower for word in ['lead', 'senior', 'consultant', 'engineer', 'developer']):
            if len(line.strip()) < 100:
                experience.append(line.strip())
    
    summary = "* " + " ".join(skills[:3]) if skills else "* Experienced professional with diverse technical skills"
    summary += "\n* " + (experience[0] if experience else "Software professional with proven track record")
    summary += "\n* Strong problem-solving and analytical capabilities"
    summary += "\n* Proficient in modern development tools and methodologies"
    summary += "\n* Excellent collaboration and communication skills"
    
    return summary

# 3. PDF se text nikalne ka function
def extract_text_from_resume(file_path):
    try:
        if not os.path.exists(file_path):
            return f"Error: File {file_path} nahi mili."
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = "".join([page.extract_text() for page in reader.pages])
            return text
    except Exception as e:
        return f"Error: {e}"

# 4. Main Process (Jo app.py call karega)
def main_process_resume(file_path):
    resume_text = extract_text_from_resume(file_path)
    summary = generate_professional_summary(resume_text) 
    return {
        "ai_summary": summary, 
        "raw_text": resume_text
    }



def normalize_resume_json(raw_resume):
    """Clean and normalize resume JSON structure"""
    normalized = {
        "skills": raw_resume.get("skills", []),
        "projects": raw_resume.get("projects", []),
        "experience_years": raw_resume.get("experience_years", 0)
    }
    
    # Clean skills (remove garbage words)
    clean_skills = []
    garbage = {"any", "the", "and", "project", "skill", "work", "experience"}
    for skill in normalized["skills"]:
        skill_str = str(skill).strip().lower()
        if len(skill_str) > 2 and skill_str not in garbage:
            clean_skills.append(skill_str)
    
    normalized["skills"] = clean_skills
    return normalized


# 5. Matching Logic Functions
def analyze_resume_text(text):
    # Enhanced skill extraction with Gemini
    try:
        prompt = f"Extract all technical skills from this resume as a comma-separated list. Only return skills, nothing else:\n{text[:3000]}"
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        skills_text = response.text
        # Parse skills from response
        skills = [s.strip() for s in skills_text.replace('\n', ',').split(',') if s.strip()]
        return {"skills": skills[:20]}  # Limit to top 20
    except:
        # Fallback to basic extraction
        potential_skills = re.split(r'[,\n\s/]', text.lower())
        common_tech = {'python', 'java', 'flask', 'sql', 'javascript', 'react', 'node', 'html', 'css', 'mongodb', 'docker', 'aws'}
        found = set()
        for word in potential_skills:
            word = word.strip('.,()')
            if word in common_tech:
                found.add(word.title())
        return {"skills": list(found)}

def analyze_job_text(text):
    potential_skills = re.split(r'[,\n\s/]', text.lower())
    common_tech = {'python', 'java', 'flask', 'sql', 'javascript', 'react', 'node', 'html', 'css', 'mongodb', 'docker', 'aws', 'kubernetes', 'django', 'fastapi', 'postgresql', 'redis', 'git', 'ci/cd', 'agile', 'scrum'}
    found = set()
    for word in potential_skills:
        word = word.strip('.,()')
        if word in common_tech:
            found.add(word.title())
    return {"skills": list(found), "must_have": list(found)}

def match_resume_with_job(resume_text, job_text):
    resume_data = analyze_resume_text(resume_text)
    job_data = analyze_job_text(job_text)
    return {
        "resume_data": resume_data, 
        "job_data": job_data,
        "explanation": "Matching based on AI-detected keywords and semantic parsing."
    }

def calculate_match_percentage(jd_json, resume_json):
    """
    AI-based percentage calculation using semantic understanding
    """
    try:
        # Convert JSON back to text for AI analysis
        job_skills = jd_json.get("skills", jd_json.get("must_have", []))
        resume_skills = resume_json.get("skills", [])
        
        # AI prompt for intelligent matching
        prompt = f"""
        Calculate the match percentage between job requirements and candidate resume:
        
        JOB REQUIRED SKILLS: {', '.join(job_skills)}
        CANDIDATE SKILLS: {', '.join(resume_skills)}
        
        Instructions:
        - Analyze semantic similarity (not just exact matching)
        - Consider related technologies and transferable skills
        - Evaluate experience level compatibility
        - Assess overall fit for the role
        
        Examples of semantic matching:
        - "Python" matches "Python Development", "Django", "Flask"
        - "JavaScript" matches "React", "Node.js", "Angular"
        - "Database" matches "SQL", "MongoDB", "PostgreSQL"
        - "Cloud" matches "AWS", "Azure", "GCP"
        
        Return ONLY a number between 0-100 representing the match percentage.
        Consider partial matches and related technologies.
        """
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        # Extract percentage from AI response
        ai_response = response.text.strip()
        
        # Find percentage in response
        percentage_match = re.search(r'\d+(\.\d+)?', ai_response)
        
        if percentage_match:
            percentage = float(percentage_match.group())
            # Ensure percentage is in valid range
            percentage = max(0, min(100, percentage))
            return round(percentage, 2)
        else:
            # Fallback to basic matching if AI doesn't return number
            j_skills = set([str(s).lower().strip() for s in job_skills])
            r_skills = set([str(s).lower().strip() for s in resume_skills])
            if not j_skills: 
                return 0.0
            matched = j_skills.intersection(r_skills)
            score = (len(matched) / len(j_skills)) * 100
            return round(float(score), 2)
            
    except Exception as e:
        print(f"AI percentage calculation failed: {e}")
        # Fallback to basic mathematical matching
        j_skills = set([str(s).lower().strip() for s in jd_json.get("skills", jd_json.get("must_have", []))])
        r_skills = set([str(s).lower().strip() for s in resume_json.get("skills", [])])
        if not j_skills: 
            return 0.0
        matched = j_skills.intersection(r_skills)
        score = (len(matched) / len(j_skills)) * 100
        return round(float(score), 2)

# 6. Self-Test Block
if __name__ == "__main__":
    # Testing mode
    test_pdf = "test_resume.pdf"
    if os.path.exists(test_pdf):
        print("Testing Mode...")
        load_mistral_model()
        res = main_process_resume(test_pdf)
        print("\n--- AI SUMMARY ---\n", res["ai_summary"])
        print("\n--- RAW TEXT (first 500 chars) ---\n", res["raw_text"][:500])
    else:
        print(f"⚠️  Test ke liye '{test_pdf}' file folder mein nahi hai.")
        print("Koi bhi resume PDF ko 'test_resume.pdf' naam se save karo aur phir se run karo!")