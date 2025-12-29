import ollama
import PyPDF2
import docx

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
        return f"Resume contains minimal content: {text}"
    
    # Clean and format text
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Extract key information
    lines = text.split('.')
    summary_parts = []
    
    for line in lines[:5]:  # First 5 sentences
        line = line.strip()
        if len(line) > 10:  # Only meaningful sentences
            summary_parts.append(line)
            if len(' '.join(summary_parts)) > 250:
                break
    
    if summary_parts:
        summary = '. '.join(summary_parts)
        if not summary.endswith('.'):
            summary += '.'
        return summary[:400] + ('...' if len(summary) > 400 else '')
    else:
        # If no sentences found, return first 200 characters
        return text[:200] + ('...' if len(text) > 200 else '')

# 3. YEH FUNCTION MISSING THA - Isse add karein
def match_resume_with_job(resume_summary, job_title, job_description):
    """
    Candidate ki summary ko Job Description se match karta hai.
    Specially checking for BSc/MSc and Agile skills.
    """
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