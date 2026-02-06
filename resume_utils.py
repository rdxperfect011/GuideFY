"""
Resume utilities for text extraction and processing.
Supports PDF and DOCX file formats.
"""


import re
from typing import Dict

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


RESUME_ANALYSIS_PROMPT = """
You are an expert resume reviewer and career coach.
Analyze the following resume and provide detailed feedback in JSON format.

Resume Content:
{resume_text}

Provide analysis in this EXACT JSON format:
{{
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "missing_keywords": ["keyword 1", "keyword 2", "keyword 3"],
  "formatting_feedback": "Brief feedback on structure and formatting",
  "action_items": [
    {{"priority": "high", "item": "specific action"}},
    {{"priority": "medium", "item": "specific action"}},
    {{"priority": "low", "item": "specific action"}}
  ],
  "overall_impression": "Brief overall assessment"
}}

Be specific, actionable, and constructive.
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
    Analyze resume for common keywords and categories.
    
    Args:
        text: Resume text
        
    Returns:
        Dictionary with keyword categories
    """
    text_lower = text.lower()
    
    # Common keyword categories
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
        'developed', 'created', 'designed', 'implemented', 'managed', 'led',
        'improved', 'optimized', 'achieved', 'delivered', 'built', 'launched'
    ]
    
    found_keywords = {
        'technical_skills': [skill for skill in technical_skills if skill in text_lower],
        'soft_skills': [skill for skill in soft_skills if skill in text_lower],
        'action_verbs': [verb for verb in action_verbs if verb in text_lower]
    }
    
    return found_keywords


def calculate_ats_score(text: str, keywords: Dict[str, list]) -> int:
    """
    Calculate ATS (Applicant Tracking System) compatibility score.
    
    Args:
        text: Resume text
        keywords: Found keywords dictionary
        
    Returns:
        Score between 0-100
    """
    score = 0
    
    # Check for contact information (email, phone)
    # Email pattern: standard user@domain.com format
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
        score += 10
    # Phone pattern: 10 digits or standard xxx-xxx-xxxx formats
    if re.search(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
        score += 10
    
    # Check for section headers
    common_sections = ['experience', 'education', 'skills', 'projects']
    for section in common_sections:
        if section in text.lower():
            score += 5
    
    # Check for keywords
    # Awards points based on the density of relevant keywords found
    total_keywords = sum(len(v) for v in keywords.values())
    if total_keywords >= 10:
        score += 30
    elif total_keywords >= 5:
        score += 20
    else:
        score += 10
    
    # Check for action verbs
    # Strong resumes use action verbs (e.g., "developed", "led")
    if len(keywords.get('action_verbs', [])) >= 5:
        score += 15
    elif len(keywords.get('action_verbs', [])) >= 3:
        score += 10
    else:
        score += 5
    
    # Check for quantifiable achievements (numbers)
    # Looks for percentages, "X+", or "Xx" (e.g., "10x growth") to indicate measurable impact
    numbers = re.findall(r'\b\d+%|\b\d+\+|\b\d+x\b', text)
    if len(numbers) >= 3:
        score += 10
    elif len(numbers) >= 1:
        score += 5
    
    return min(score, 100)
