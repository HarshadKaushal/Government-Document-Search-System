import re
from datetime import datetime
from bs4 import BeautifulSoup
import pdfplumber

def extract_date(text):
    """
    Extract a date from text using common patterns. Returns date as YYYY-MM-DD or None.
    """
    date_patterns = [
        r'(\d{2})[/-](\d{2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{2})[/-](\d{2})',  # YYYY/MM/DD or YYYY-MM-DD
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        r'\d{2}/\d{2}/\d{4}',
        r'\d{2}-\d{2}-\d{4}'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        return datetime.strptime(f"{groups[0]}-{groups[1]}-{groups[2]}", "%Y-%m-%d").strftime("%Y-%m-%d")
                    else:  # DD-MM-YYYY
                        return datetime.strptime(f"{groups[2]}-{groups[1]}-{groups[0]}", "%Y-%m-%d").strftime("%Y-%m-%d")
                else:
                    # For month name formats
                    try:
                        return datetime.strptime(match.group(0), "%B %d, %Y").strftime("%Y-%m-%d")
                    except:
                        try:
                            return datetime.strptime(match.group(0), "%d %B %Y").strftime("%Y-%m-%d")
                        except:
                            pass
            except Exception:
                continue
    return None

def clean_title(text):
    """Clean and normalize document title."""
    if text:
        return ' '.join(text.strip().split())
    return ''

def determine_section(text, element=None):
    """
    Determine section from text or BeautifulSoup element context.
    """
    text = text.lower() if text else ''
    if 'notification' in text:
        return 'Notifications'
    if 'circular' in text:
        return 'Circulars'
    if 'order' in text:
        return 'Orders'
    if 'pressrelease' in text or 'press release' in text:
        return 'Press Releases'
    if 'speech' in text:
        return 'Speeches'
    # Try parent context if element is provided
    if element:
        for parent in [element] + list(element.parents):
            parent_text = parent.get_text().lower()
            if 'notification' in parent_text:
                return 'Notifications'
            if 'circular' in parent_text:
                return 'Circulars'
            if 'order' in parent_text:
                return 'Orders'
    return 'Other'

def build_filename(title, date=None, section=None, ext='.pdf'):
    """Standardize filename construction."""
    base = re.sub(r'[^\w\s-]', '', title)[:50].strip().replace(' ', '_')
    section = section or 'Document'
    date = date or 'NODATE'
    filename = f"{section}_{base}_{date}{ext}"
    return filename

def extract_release_date_from_pdf(pdf_path):
    """
    Extract the most likely release date from the first page of a PDF using keyword proximity.
    Returns the date string if found, else None.
    """
    date_patterns = [
        r'(\d{2})[/-](\d{2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{2})[/-](\d{2})',  # YYYY/MM/DD or YYYY-MM-DD
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
    ]
    keywords = ["date", "issued", "notification", "order", "published", "release"]
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            if not text:
                return None
            lines = text.split('\n')
            # 1. Search for date near keywords
            for line in lines:
                lower_line = line.lower()
                if any(kw in lower_line for kw in keywords):
                    for pattern in date_patterns:
                        match = re.search(pattern, line)
                        if match:
                            return match.group(0)
            # 2. Fallback: first date found on the page
            for line in lines:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(0)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return None 