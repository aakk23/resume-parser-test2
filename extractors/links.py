# extractors/links.py
import re
from urllib.parse import urlparse
import validators
import pdfplumber

def categorize_social_link(url):
    """Categorize social media links by platform"""
    # Extract domain from URL
    domain = urlparse(url).netloc.lower()
    
    platforms = {
        'www.linkedin.com': 'LinkedIn',
        'linkedin.com': 'LinkedIn',
        'www.github.com': 'GitHub',
        'github.com': 'GitHub',
        'www.twitter.com': 'Twitter',
        'twitter.com': 'Twitter',
        'x.com': 'Twitter',
        'www.facebook.com': 'Facebook',
        'facebook.com': 'Facebook',
        'www.instagram.com': 'Instagram',
        'instagram.com': 'Instagram',
        'www.medium.com': 'Medium',
        'medium.com': 'Medium',
        'www.stackoverflow.com': 'Stack Overflow',
        'stackoverflow.com': 'Stack Overflow',
        'www.hackerrank.com': 'HackerRank',
        'hackerrank.com': 'HackerRank',
        'www.leetcode.com': 'LeetCode',
        'leetcode.com': 'LeetCode'
    }
    
    # Check if any platform key is in the domain (partial match)
    for platform_domain, platform_name in platforms.items():
        if platform_domain in domain:
            return platform_name
    
    return "Other"

def extract_pdf_hyperlinks(pdf_path):
    """Extract hyperlinks from PDF using pdfplumber"""
    try:
        links = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                annotations = page.annots
                if annotations:
                    for annotation in annotations:
                        if annotation.get("uri"):
                            links.append(annotation["uri"])
        return links
    except Exception:
        return []

def extract_social_links(text, filepath=None):
    """Extract and categorize social media links"""
    url_matches = re.findall(r'(https?://[^\s]+)', text)
    
    social_patterns = {
        'linkedin': r'linkedin\.com/in/[\w-]+',
        'github': r'github\.com/[\w-]+',
        'twitter': r'twitter\.com/[\w-]+',
        'medium': r'medium\.com/@?[\w-]+'
    }
    
    embedded_links = []
    if filepath and filepath.lower().endswith('.pdf'):
        embedded_links = extract_pdf_hyperlinks(filepath)
    
    all_links = set(url_matches + embedded_links)
    
    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, text, re.I)
        all_links.update(f"https://{match}" for match in matches)
    
    categorized = {}
    for link in all_links:
        clean_link = re.sub(r'[,.)\]>"]$', '', link)  # Remove trailing punctuation
        
        if validators.url(clean_link):  # Ensure the link is valid
            category = categorize_social_link(clean_link)
            
            if category not in categorized:
                categorized[category] = []
            if clean_link not in categorized[category]:
                categorized[category].append(clean_link)
    
    return categorized