"""
Resume utilities for text extraction and processing.
Supports PDF and DOCX file formats.
"""
import re
import sys
import subprocess
from typing import Dict

try:
    import spacy
except ImportError:
    spacy = None

nlp_model = None

def get_nlp_model():
    global nlp_model
    if nlp_model is None and spacy is not None:
        try:
            nlp_model = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy en_core_web_sm model...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            nlp_model = spacy.load("en_core_web_sm")
    return nlp_model

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


RESUME_ANALYSIS_PROMPT = """
Analyze the resume and provide feedback in EXACTLY this JSON format:
{resume_text}
{{
  "strengths": ["s1", "s2"],
  "weaknesses": ["w1", "w2"],
  "missing_keywords": ["k1", "k2"],
  "formatting_feedback": "Brief structural feedback",
  "action_items": [
    {{"priority": "high", "item": "specific action"}},
    {{"priority": "low", "item": "specific action"}}
  ],
  "overall_impression": "Brief assessment",
  "ai_comparison": {{
    "ats_score": 85,
    "skills_match": "High/Medium/Low - Brief",
    "keyword_match": "High/Medium/Low - Brief",
    "final_recommendation": "Brief recommendation",
    "reasoning": "Brief explanation"
  }}
}}
"""


def extract_text_from_pdf(file_stream) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_stream: File-like object containing PDF data
        
    Returns:
        Extracted text as string
    """
    if PdfReader is None:
        raise ImportError("PyPDF2 is not installed. Install it with: pip install PyPDF2")
    
    try:
        pdf_reader = PdfReader(file_stream)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_docx(file_stream) -> str:
    """
    Extract text from a DOCX file.
    
    Args:
        file_stream: File-like object containing DOCX data
        
    Returns:
        Extracted text as string
    """
    if Document is None:
        raise ImportError("python-docx is not installed. Install it with: pip install python-docx")
    
    try:
        doc = Document(file_stream)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")


def extract_resume_text(file_stream, filename: str) -> str:
    """
    Extract text from resume file (PDF or DOCX).
    
    Args:
        file_stream: File-like object containing resume data
        filename: Name of the file to determine type
        
    Returns:
        Extracted text as string
    """
    file_ext = filename.lower().split('.')[-1]
    
    if file_ext == 'pdf':
        return extract_text_from_pdf(file_stream)
    elif file_ext in ['docx', 'doc']:
        return extract_text_from_docx(file_stream)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Only PDF and DOCX are supported.")


def preprocess_resume_text(text: str) -> str:
    """
    Clean and preprocess resume text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace (multiple spaces to single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation necessary for sentence structure
    # Keeps: alphanumerics, spaces, ., ;, :, (), -, @, +, #
    text = re.sub(r'[^\w\s.,;:()\-@+#]', '', text)
    
    return text.strip()


def analyze_resume_keywords(text: str) -> Dict[str, list]:
    """
    Analyze resume for common keywords and categories using NLP.
    
    Args:
        text: Resume text
        
    Returns:
        Dictionary with keyword categories and NLP entities
    """
    text_lower = text.lower()
    nlp = get_nlp_model()
    
    # Process text with spaCy if available
    doc = nlp(text) if nlp else None
    
    technical_skills = [
        'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
        'kubernetes', 'git', 'machine learning', 'ai', 'data science', 'tensorflow',
        'pytorch', 'html', 'css', 'angular', 'vue', 'mongodb', 'postgresql'
    ]
    
    soft_skills = [
        'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
        'creative', 'adaptable', 'organized', 'detail-oriented', 'collaborative'
    ]
    
    action_verbs = [
        'develop', 'create', 'design', 'implement', 'manage', 'lead',
        'improve', 'optimize', 'achieve', 'deliver', 'build', 'launch'
    ]
    
    found_tech_skills = [skill for skill in technical_skills if skill in text_lower]
    found_soft_skills = [skill for skill in soft_skills if skill in text_lower]
    
    if doc:
        # Use NLP for action verbs: match on lemmas
        doc_lemmas = [token.lemma_.lower() for token in doc if token.pos_ == 'VERB']
        found_action_verbs = list(set([verb for verb in action_verbs if verb in doc_lemmas]))
        
        # Extract entities
        organizations = list(set([ent.text for ent in doc.ents if ent.label_ == 'ORG']))
        locations = list(set([ent.text for ent in doc.ents if ent.label_ == 'GPE']))
        dates = list(set([ent.text for ent in doc.ents if ent.label_ == 'DATE']))
        
        found_keywords = {
            'technical_skills': found_tech_skills,
            'soft_skills': found_soft_skills,
            'action_verbs': found_action_verbs,
            'organizations': organizations[:10], # Limit to avoid bloat
            'locations': locations[:10],
            'dates': dates[:10]
        }
    else:
        # Fallback to simple matching if spaCy is unavailable
        action_verbs_simple = [v + 'ed' for v in action_verbs] + action_verbs
        found_keywords = {
            'technical_skills': found_tech_skills,
            'soft_skills': found_soft_skills,
            'action_verbs': [verb for verb in action_verbs_simple if verb in text_lower],
            'organizations': [],
            'locations': [],
            'dates': []
        }
        
    return found_keywords


def calculate_ats_score(text: str, keywords: Dict[str, list]) -> Dict[str, any]:
    """
    Calculate ATS (Applicant Tracking System) compatibility score.
    Returns:
        Dict with total_score between 0-100 and a breakdown of components
    """
    breakdown = {
        "Skills Match Score": 0,
        "Keyword Match Score": 0,
        "Experience Score": 0,
        "Education Score": 0,
        "Formatting Score": 0
    }
    
    # 1. Contact Info & Sections (Formatting Score max 20)
    fmt_score = 0
    # Check for contact information (email, phone)
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
        fmt_score += 10
    if re.search(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
        fmt_score += 5
    
    # Check for section headers
    common_sections = ['experience', 'education', 'skills', 'projects']
    for section in common_sections:
        if section in text.lower():
            fmt_score += 1.25
    breakdown["Formatting Score"] = min(int(fmt_score), 20)
    
    # 2. Skills Match Score (max 25)
    skill_score = 0
    tech_count = len(keywords.get('technical_skills', []))
    soft_count = len(keywords.get('soft_skills', []))
    
    if tech_count + soft_count >= 10:
        skill_score += 25
    elif tech_count + soft_count >= 5:
        skill_score += 15
    else:
        skill_score += 5
    breakdown["Skills Match Score"] = skill_score
        
    # 3. Keyword Match (Entities / Action Verbs) Score (max 25)
    kw_score = 0
    org_count = len(keywords.get('organizations', []))
    
    if org_count >= 2:
        kw_score += 10
    
    verb_count = len(keywords.get('action_verbs', []))
    if verb_count >= 5:
        kw_score += 15
    elif verb_count >= 3:
        kw_score += 8
    breakdown["Keyword Match Score"] = kw_score
    
    # 4. Experience & Impact Score (max 20)
    exp_score = 0
    date_count = len(keywords.get('dates', []))
    if date_count >= 3:
        exp_score += 10  # Specifying precise timelines is a strong ATS signal
    
    numbers = re.findall(r'\b\d+%|\b\d+\+|\b\d+x\b', text)
    if len(numbers) >= 3:
        exp_score += 10
    elif len(numbers) >= 1:
        exp_score += 5
    breakdown["Experience Score"] = min(exp_score, 20)

    # 5. Education Score (max 10)
    edu_score = 0
    education_keywords = ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'bsc', 'msc', 'diploma', 'certificate', 'certification', 'high school', 'degree', 'university', 'college']
    edu_count = sum(1 for edu in education_keywords if edu in text.lower())
    if edu_count >= 2:
        edu_score = 10
    elif edu_count >= 1:
        edu_score = 5
    breakdown["Education Score"] = edu_score

    # Calculate total and map breakdown dict
    total_score = min(sum(breakdown.values()), 100)
    
    percentages = {
        "Skills Match": {"score": breakdown["Skills Match Score"], "max": 25},
        "Keyword Match": {"score": breakdown["Keyword Match Score"], "max": 25},
        "Experience": {"score": breakdown["Experience Score"], "max": 20},
        "Formatting": {"score": breakdown["Formatting Score"], "max": 20},
        "Education": {"score": breakdown["Education Score"], "max": 10}
    }
    
    return {
        "total": total_score,
        "breakdown": percentages
    }


def extract_nlp_analysis(text: str) -> Dict[str, any]:
    """
    Extracts NLP-driven insights: skills, experience level, education, keywords.
    """
    text_lower = text.lower()
    nlp = get_nlp_model()
    
    # Process text with spaCy if available
    doc = nlp(text) if nlp else None

    # Extracted skills (technical + tools)
    technical_skills = [
        'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
        'kubernetes', 'git', 'machine learning', 'ai', 'data science', 'tensorflow',
        'pytorch', 'html', 'css', 'angular', 'vue', 'mongodb', 'postgresql', 'c++', 'c#',
        'fastapi', 'flask', 'django', 'spring', 'go', 'rust', 'azure', 'gcp'
    ]
    skills_detected = [skill for skill in technical_skills if skill in text_lower]

    # Education
    education_keywords = ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'bsc', 'msc', 'diploma', 'certificate', 'certification', 'high school', 'degree']
    education_detected = list(set([edu for edu in education_keywords if edu in text_lower]))

    # Experience level classification
    if any(word in text_lower for word in ['senior', 'lead', 'manager', 'director', 'principal', 'head']) or re.search(r'\b(1[0-9]|20)\+?\s*years?\b', text_lower):
        experience_level = "Advanced"
    elif any(word in text_lower for word in ['intermediate', 'mid-level']) or re.search(r'\b[3-9]\+?\s*years?\b', text_lower):
        experience_level = "Intermediate"
    elif any(word in text_lower for word in ['intern', 'junior', 'fresher', 'entry-level', 'beginner']) or re.search(r'\b[0-2]\s*years?\b', text_lower):
        experience_level = "Beginner"
    else:
        experience_level = "Intermediate" if len(skills_detected) > 5 else "Beginner"

    # Important keywords (Domain related nouns)
    important_keywords = []
    if doc:
        from collections import Counter
        # Extract Nouns and Proper Nouns, ignoring short words and stop words
        nouns = [token.text.lower() for token in doc if token.pos_ in ['NOUN'] and len(token.text) > 3 and not token.is_stop]
        
        # Don't include words that are already in skills or education
        filtered_nouns = [n for n in nouns if n not in technical_skills and n not in education_keywords]
        
        top_nouns = [word for word, count in Counter(filtered_nouns).most_common(8)]
        important_keywords = top_nouns
    else:
        # Fallback if no spaCy
        important_keywords = list(set([word for word in text_lower.split() if len(word) > 5]))[:8]

    return {
        "skills": skills_detected,
        "experience_level": experience_level,
        "education": education_detected,
        "domain_keywords": important_keywords
    }
