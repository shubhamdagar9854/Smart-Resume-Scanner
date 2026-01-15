import os
import re
import PyPDF2
import docx

# Import RAG processor
from rag_summary import create_rag_summary

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
# RESUME SUMMARY (DIRECT EXTRACTION)
# =====================================================
def extract_summary_from_text(text):
    """Extract summary section directly from resume text"""
    if not text:
        return None
    
    print("=== DEBUG: Raw Resume Text ===")
    print(text[:500] + "..." if len(text) > 500 else text)
    print("\n=== DEBUG: Looking for Summary Section ===")
    
    # Look for summary section patterns - more comprehensive
    summary_patterns = [
        # Pattern 1: Summary heading followed by content until next heading
        r'(?:summary|professional summary|profile|about|overview)[:\-]?\s*\n?\s*(.*?)(?=\n\s*[A-Z][a-zA-Z\s]*:|\n\s*[A-Z][a-zA-Z\s]+\n|\n\s*[A-Z][a-zA-Z\s]*$|\Z)',
        # Pattern 2: Summary heading with colon
        r'(?:summary|professional summary|profile|about|overview)[:\-]?\s*\n?\s*:\s*(.*?)(?=\n\s*[A-Z][a-zA-Z\s]*:|\n\s*[A-Z][a-zA-Z\s]+\n|\n\s*[A-Z][a-zA-Z\s]*$|\Z)',
        # Pattern 3: Simple summary section
        r'(?:summary|professional summary|profile|about|overview)[:\-]?\s*\n?\s*(.*?)(?:\n\n|\n[A-Z]|\Z)',
    ]
    
    for i, pattern in enumerate(summary_patterns):
        print(f"=== DEBUG: Trying Pattern {i+1} ===")
        print(f"Pattern: {pattern}")
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            summary_text = match.group(1).strip()
            # Clean up but preserve ALL formatting
            summary_text = re.sub(r'\n+', '\n', summary_text)
            # Remove trailing whitespace
            summary_text = summary_text.rstrip()
            print(f"=== DEBUG: Pattern {i+1} MATCHED! ===")
            print(f"Extracted Summary: '{summary_text}'")
            return summary_text
        else:
            print(f"=== DEBUG: Pattern {i+1} NO MATCH ===")
    
    print("=== DEBUG: No Summary Section Found - Trying Smart Fallback ===")
    
    # Smart fallback - look for multi-line summary paragraph
    lines = text.split('\n')
    summary_lines = []
    found_start = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        print(f"=== DEBUG: Line {i+1}: '{line}' (Length: {len(line)}) ===")
        
        # Skip first 6 lines (name, title, contact info)
        if i < 6:
            continue
        
        # Found first long line (40+ chars) - start collecting
        if not found_start and len(line) >= 40:
            found_start = True
            summary_lines.append(line)
            
            # Capture next 4-5 lines (complete paragraph)
            for j in range(i+1, min(i+6, len(lines))):
                next_line = lines[j].strip()
                
                # Stop conditions
                if len(next_line) < 15:  # Empty or too short
                    break
                if next_line.strip() in ['Senior Technical Lead', 'Work History', 'Experience', 'Education', 'Skills', 'Projects', 'Certifications', 'Employment', 'Objective', 'Profile', 'About']:  # Section headings
                    break
                if next_line.endswith(':'):  # Section heading with colon
                    break
                
                # Valid continuation line - add it
                summary_lines.append(next_line)
            
            # Return combined paragraph
            if summary_lines:
                complete_summary = ' '.join(summary_lines)
                print(f"=== DEBUG: Multi-line Summary Found ===")
                print(f"Complete Summary: '{complete_summary}'")
                return complete_summary
            break
    
    print("=== DEBUG: No Summary Found ===")
    return None

def create_resume_summary(text):
    import ollama
    prompt = f'''
You are a professional resume writer.

Your task is to GENERATE a new professional resume summary from the given resume text.

IMPORTANT:
- Do NOT extract or reuse the existing summary sentences from the resume.
- Rewrite everything in your own professional language.
- Do NOT output a paragraph.

STRICT FORMAT RULES:
- Use bullet points (•) only.
- Maximum 5 bullet points.
- Professional, recruiter-ready tone.
- Avoid generic phrases like "self-directed", "motivated", "results-oriented".

CONTENT RULES:
- Use ONLY information present in the resume text.
- If years of experience are mentioned, format as "X+ years".
- If a domain/industry is mentioned (Healthcare, Enterprise, FinTech, etc.), include it naturally.
- If skills are mentioned, group them under a line starting exactly with:
  Technical Expertise:
- If skill ratings exist (⭐ ★ ☆ ● ○ %), preserve them exactly.
- Do NOT invent skills, ratings, or domains.

MANDATORY OUTPUT STRUCTURE:

• Experienced software engineer with X+ years of hands-on experience in end-to-end product development.
• Strong background in <domain if mentioned>.
• Technical Expertise:
  Skill1 ⭐⭐⭐⭐⭐ | Skill2 ⭐⭐⭐⭐☆ | Skill3 ⭐⭐⭐⭐☆
• Experienced in backend development, API design, system integration, and performance optimization.
• Comfortable working in Agile teams and mentoring junior engineers.

OUTPUT RULES:
- Output ONLY the bullet-point summary.
- Do NOT include headings, explanations, or emojis.

RESUME TEXT:
{text[:1200]}
'''
    try:
        response = ollama.generate(model='llama3.2:1b', prompt=prompt, options={"num_predict": 200, "temperature": 0.2})
        return response['response'].strip()
    except:
        return "• Error generating summary."

def create_clean_ai_summary(text):
    """Generate new professional resume summary"""
    # Professional resume writer prompt with generation instructions
    ai_prompt = f"""You are a professional resume writer.

Your task is to GENERATE a new professional resume summary from the given resume text.

IMPORTANT:
- Do NOT extract or reuse existing summary sentences from the resume.
- Rewrite everything in your own professional language.
- Do NOT output a paragraph.

STRICT FORMAT RULES:
- Use bullet points (•) only.
- Maximum 5 bullet points.
- Professional, recruiter-ready tone.
- Avoid generic phrases like "self-directed", "motivated", "results-oriented".

CONTENT RULES:
- Use ONLY information present in the resume text.
- If years of experience are mentioned, format as "X+ years".
- If a domain/industry is mentioned (Healthcare, Enterprise, FinTech, etc.), include it naturally.
- If skills are mentioned, group them under a line starting exactly with:
  Technical Expertise:
- If skill ratings exist (⭐ ★ ☆ ● ○ %), preserve them exactly.

MANDATORY OUTPUT STRUCTURE:

• Experienced software engineer with X+ years of hands-on experience in end-to-end product development.
• Strong background in <domain if mentioned>.
• Technical Expertise:
  Skill1 ⭐⭐⭐⭐ | Skill2 ⭐⭐⭐⭐☆ | Skill3 ⭐⭐⭐⭐☆
• Experienced in backend development, API design, system integration, and performance optimization.
• Comfortable working in Agile teams and mentoring junior engineers.

OUTPUT RULES:
- Output ONLY the bullet-point summary.
- Do NOT include headings, explanations, or emojis.
- Do NOT invent skills, ratings, or domains.

Resume Text:
{text}"""

    try:
        # Call AI model with generation instructions
        response = ollama.generate(
            model='llama3.1:8b',
            prompt=ai_prompt,
            options={
                'temperature': 0.3,  # Slight creativity for professional writing
                'top_p': 0.9,
                'max_tokens': 250
            }
        )
        
        if response and 'response' in response:
            ai_summary = response['response'].strip()
            # Ensure bullet point format
            if not ai_summary.startswith('•'):
                # Force bullet point format
                lines = ai_summary.split('\n')
                formatted_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('•'):
                        line = f"• {line}"
                    formatted_lines.append(line)
                ai_summary = '\n'.join(formatted_lines)
            
            # Clean up any conversational text
            ai_summary = re.sub(r'^(Here is|This is|The following|Your summary).*?:', '', ai_summary, flags=re.IGNORECASE).strip()
            return ai_summary
        else:
            return "• Experienced software engineer with relevant skills and experience."
            
    except Exception as e:
        print(f"AI summary generation failed: {e}")
        return "• Experienced software engineer with relevant skills and experience."


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
