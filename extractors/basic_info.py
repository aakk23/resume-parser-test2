import re
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path):
    """Extract text from PDF with enhanced handling of text blocks"""
    text_blocks = []
    
    with fitz.open(file_path) as doc:
        for page in doc:
            # Get text with more layout preservation
            blocks = page.get_text("blocks")
            for block in blocks:
                # Each block is (x0, y0, x1, y1, "text", block_no, block_type)
                text_blocks.append(block[4])
    
    # Join all text blocks with space in between
    full_text = "\n".join(text_blocks)
    
    # Clean up multiple newlines and spaces
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    full_text = re.sub(r' {2,}', ' ', full_text)
    
    return full_text

def get_email_prefix(email):
    return email.split('@')[0]

def clean_and_tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

def generate_search_keys(email_prefix):
    search_keys = set()
    length = len(email_prefix)
    # Forward slices
    for i in range(2, length + 1):
        search_keys.add(email_prefix[:i])
    # Backward slices
    for i in range(length - 1, 0, -1):
        search_keys.add(email_prefix[i:])
    return list(search_keys)

def score_match(search_key, word):
    if word == search_key:
        return 100  # exact match
    elif word.startswith(search_key) or word.endswith(search_key):
        return 75  # prefix/suffix match
    elif search_key in word:
        return 50  # partial
    return 0

def clean_name_format(name):
    name = re.sub(r'[^a-zA-Z\s]', '', name)  # remove digits and symbols
    return ' '.join(word.capitalize() for word in name.split())

def email_proximity_search(text, email):
    # Remove the email itself from text before searching
    if email:
        text = text.replace(email, '')

    tokens = clean_and_tokenize(text)
    email_prefix = get_email_prefix(email)

    # Try full match first
    if email_prefix in tokens:
        return clean_name_format(email_prefix)

    # Scoring-based fallback
    search_keys = generate_search_keys(email_prefix)
    best_word, best_score = None, 0
    for word in tokens:
        for key in search_keys:
            score = score_match(key, word)
            if score > best_score:
                best_score = score
                best_word = word

    return clean_name_format(best_word) if best_word else None

def name_matches_email(name, email):
    if not name:
        return False
    email_prefix = get_email_prefix(email).lower()
    return any(part.lower() in email_prefix for part in name.split())

def extract_email(text):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None

def extract_phone(text):
    """Extract phone numbers from text with better handling of PDF formatting
    and standardize to 10 digits by removing country code if needed"""
    
    # Clean the text to handle potential PDF formatting issues
    cleaned_text = re.sub(r'\s+', ' ', text)
    
    # Try multiple patterns from specific to general
    patterns = [
        r'\+\d{1,3}[-\s]?\d{5,12}',              # International format: +91-7906862379
        r'\+?\d{1,3}[-\s]?\d{3,4}[-\s]?\d{3,4}', # Format with separators
        r'\d{10,12}',                            # Just digits (10-12 digits)
        r'\+?\d[\d\s\-()\n]{8,}\d'               # Flexible pattern as fallback
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, cleaned_text)
        if matches:
            # Clean the match to remove non-digits
            raw_phone = re.sub(r'\D', '', matches[0])
            
            # Standardize: if more than 10 digits, assume country code and remove it
            if len(raw_phone) > 10:
                # Keep only the last 10 digits
                return raw_phone[-10:]
            else:
                return raw_phone
    
    return None

def extract_name(text, email):
    lines = text.splitlines()
    first_15_lines = lines[:15]
    name_candidate = None

    # Logic 1: First 15 lines
    for line in first_15_lines:
        line = line.strip()
        if len(line.split()) in [2, 3] and not any(char.isdigit() for char in line):
            name_candidate = line
            if name_matches_email(name_candidate, email):
                return clean_name_format(name_candidate)
            break  # still try fallback if condition fails

    # Logic 2: Fallback to email proximity if Logic 1 fails or doesn't match
    fallback_name = email_proximity_search(text, email)
    return fallback_name

def parse_resume_details(file_path):
    text = extract_text_from_pdf(file_path)
    email = extract_email(text)
    phone = extract_phone(text)
    name = extract_name(text, email) if email else None

    return {
        "candidate_name": name,
        "emails": [email] if email else [],
        "phones": [phone] if phone else []
    }
