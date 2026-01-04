import os
import PyPDF2
import docx

# Check if running in production (no ollama available)
IS_PRODUCTION = os.environ.get('RENDER') or not os.system('which ollama > /dev/null 2>&1') == 0

if not IS_PRODUCTION:
    import ollama

# 1. Resume se text nikalne ke liye
def get_text_from_resume(file_path):
    text = ""
    try:
        print(f"Extracting text from: {file_path}")
        
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                print(f"PDF has {len(pdf.pages)} pages")
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        print(f"Page {i+1}: Extracted {len(page_text)} characters")
                
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            print(f"DOCX has {len(doc.paragraphs)} paragraphs")
            
            # Try multiple extraction methods
            all_text = []
            
            # Method 1: Paragraphs
            for i, para in enumerate(doc.paragraphs):
                if para.text.strip():
                    all_text.append(para.text.strip())
                    print(f"Paragraph {i+1}: {len(para.text)} characters")
            
            # Method 2: Tables (if any)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            all_text.append(cell.text.strip())
            
            # Method 3: Runs (text within paragraphs)
            if not all_text:
                for para in doc.paragraphs:
                    for run in para.runs:
                        if run.text.strip():
                            all_text.append(run.text.strip())
            
            text = "\n".join(all_text)
        
        print(f"Total extracted text length: {len(text)}")
        
        # Additional check for very short text
        if len(text.strip()) < 20:
            print("Text is very short, checking file existence...")
            import os
            if os.path.exists(file_path):
                print(f"File exists, size: {os.path.getsize(file_path)} bytes")
            else:
                print("File does not exist!")
            
        return text if text.strip() else None
        
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return None

# 2. Resume ki short summary banane ke liye
def create_resume_summary(text):
    if not text:
        return "No resume content found"
    
    text = text.strip()
    if len(text) < 20:
        return f"• Resume contains minimal content: {text}"
    
    # Clean text completely
    import re
    text = text.replace('\n', ' ').replace('\r', ' ')
    # Remove all extra spaces between letters
    text = re.sub(r'\s+', ' ', text)
    # Remove weird characters except basic ones
    text = re.sub(r'[^a-zA-Z0-9\s\-\.\,\@\/\#\%]', ' ', text)
    # Clean up multiple spaces again
    text = re.sub(r'\s+', ' ', text)
    
    # Split into sentences
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    bullet_points = []
    
    # Look for meaningful sentences with keywords
    keywords = ['experience', 'skilled', 'proficient', 'expert', 'knowledge', 'worked', 'developed', 'managed', 'led', 'created', 'years', 'professional', 'engineer', 'developer', 'designer', 'analyst', 'python', 'java', 'javascript', 'software', 'web', 'data', 'system', 'project', 'domain', 'cloud', 'aws', 'docker', 'git', 'api', 'database', 'sql', 'nosql', 'react', 'node', 'angular', 'vue', 'flask', 'django', 'machine', 'learning', 'ai', 'devops', 'agile', 'scrum', 'testing', 'unit', 'integration']
    
    for sentence in sentences[:8]:
        if len(sentence) > 20 and len(sentence) < 200:
            # Check for keywords
            if any(keyword in sentence.lower() for keyword in keywords):
                clean_sentence = sentence.capitalize()
                # Remove weird characters and extra spaces
                clean_sentence = re.sub(r'[^a-zA-Z0-9\s\-\.\,\@\/\#\%]', '', clean_sentence)
                clean_sentence = ' '.join(clean_sentence.split())  # Clean spaces
                
                if len(clean_sentence) > 20:
                    if not clean_sentence.endswith('.'):
                        clean_sentence += '.'
                    bullet_points.append(clean_sentence)
                if len(bullet_points) >= 4:
                    break
    
    # If no good sentences found, create general ones
    if len(bullet_points) < 2:
        # Extract key information manually
        if 'python' in text.lower():
            bullet_points.append("Experienced Python developer with strong programming skills.")
        if 'developer' in text.lower():
            bullet_points.append("Professional software developer with technical expertise.")
        if 'experience' in text.lower():
            bullet_points.append("Proven work experience in relevant field.")
        if 'project' in text.lower():
            bullet_points.append("Successfully delivered multiple projects with quality results.")
        if 'cloud' in text.lower():
            bullet_points.append("Experience with cloud technologies and deployment.")
        if 'database' in text.lower():
            bullet_points.append("Strong database management and optimization skills.")
        
        # Add a general point if still less than 2
        if len(bullet_points) < 2:
            bullet_points.append("Skilled professional with strong technical background.")
    
    # Format final bullet points
    if bullet_points:
        summary = "• " + "\n• ".join(bullet_points[:4])  # Max 4 bullet points
        return summary[:400] + ("..." if len(summary) > 400 else "")
    else:
        # Simple fallback
        return f"• Professional with relevant experience and skills."

# 3. YEH FUNCTION MISSING THA - Isse add karein
def match_resume_with_job(resume_summary, job_title, job_description):
    """
    Candidate ki summary ko Job Description se match karta hai.
    Specially checking for BSc/MSc and Agile skills.
    """
    # Simple keyword-based matching for production
    if IS_PRODUCTION:
        # Extract keywords from job description
        job_text = f"{job_title} {job_description}".lower()
        resume_text = resume_summary.lower()
        
        # Common tech and education keywords
        tech_keywords = ['python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker', 'git', 'agile', 'scrum']
        education_keywords = ['bsc', 'msc', 'bachelor', 'master', 'degree', 'engineering']
        
        matched_skills = []
        for keyword in tech_keywords + education_keywords:
            if keyword in job_text and keyword in resume_text:
                matched_skills.append(keyword)
        
        # Calculate match percentage
        total_keywords = len([k for k in tech_keywords + education_keywords if k in job_text])
        match_percent = int((len(matched_skills) / max(total_keywords, 1)) * 100)
        
        return f"Match: {match_percent}% - Skills: {', '.join(matched_skills)}"
    
    # Original AI matching for local development
    prompt = f"""
    You are an expert HR Recruiter. 
    Analyze the match between this Candidate and the Job.

    JOB TITLE: {job_title}
    JOB DESCRIPTION: {job_description}
    CANDIDATE SUMMARY: {resume_summary}

    Please provide:
    1. Match Percentage (0-100%)
    2. Key Reasons (Point out if BSc/MSc or specific skills like Agile match)
    3. Final Verdict (Highly Recommended / Potential / Not Suitable)
    
    Keep the analysis concise and professional.
    """
    try:
        response = ollama.generate(model='llama3', prompt=prompt)
        return response['response']
    except Exception as e:
        return f"AI Matching Error: {e}"