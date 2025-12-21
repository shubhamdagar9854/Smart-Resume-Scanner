import requests

# -----------------------------
# Ollama AI settings
# -----------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


# -----------------------------
# Resume se text nikalna
# -----------------------------
def get_text_from_resume(file_path):
    text = ""

    try:
        # PDF file
        if file_path.endswith(".pdf"):
            import PyPDF2
            pdf = PyPDF2.PdfReader(open(file_path, "rb"))
            for page in pdf.pages:
                text += page.extract_text()

        # DOCX file
        elif file_path.endswith(".docx"):
            from docx import Document
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"

        else:
            return "Only PDF or DOCX files are supported."

    except:
        return "Error while reading resume file."

    return text


# -----------------------------
# Resume summary banana (AI)
# -----------------------------
def create_resume_summary(resume_text):
    if resume_text.strip() == "":
        return "Resume text not found."

    prompt = (
        "Summarize this resume in simple words. "
        "Mention skills, experience and education.\n\n"
        + resume_text[:2000]
    )

    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )

        return res.json()["response"]

    except:
        return "Ollama AI is not running."


# -----------------------------
# Resume & Job match check
# -----------------------------
def match_resume_with_job(summary, job_text):
    prompt = (
        "Check if this resume matches the job.\n\n"
        "Resume:\n" + summary +
        "\n\nJob:\n" + job_text +
        "\n\nAnswer only YES or NO with reason."
    )

    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )

        return res.json()["response"]

    except:
        return "AI match check failed."
