import os
import json
import sys
import logging  # Add logging import
from pdfminer.high_level import extract_text
from extractors.basic_info import parse_resume_details  # Updated function name
from extractors.links import extract_social_links
from extractors.skills import extract_skills
from extractors.education import extract_education
from extractors.experience import extract_experience

# Suppress pdfminer warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def parse_resume(filepath):
    """Parse PDF resume and extract structured information"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if not filepath.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported")
    
    # For PDFs, use parse_resume_details for basic info
    basic_info = parse_resume_details(filepath)
    
    # Extract text for other processing
    text = extract_text(filepath)
    
    skills = extract_skills(text)
    social_links = extract_social_links(text, filepath)
    education = extract_education(text)
    experience = extract_experience(text)
    
    # Combine all data
    resume_data = {
        "name": basic_info.get("candidate_name"),  # Updated key to match new structure
        "emails": basic_info.get("emails", []),
        "phones": basic_info.get("phones", []),
        "Social Links": social_links,
        "Skills": skills,
        "Education": education,
        "Experience": experience
    }
    
    return resume_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_resume.pdf>")
        sys.exit(1)
    
    try:
        resume_data = parse_resume(sys.argv[1])
        print(json.dumps(resume_data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)