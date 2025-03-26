import requests
from bs4 import BeautifulSoup
import re
import os
import time
from datetime import datetime

class BaseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Common citizen-relevant keywords
        self.citizen_relevant_keywords = [
            'public', 'citizen', 'notification', 'circular',
            'guide', 'manual', 'form', 'instruction',
            'advisory', 'notice', 'guidelines', 'regulation'
        ]
        
        # Common technical patterns
        self.technical_patterns = [
            r'internal\s+memo',
            r'technical\s+specification',
            r'maintenance',
            r'system\s+update'
        ]

    def is_citizen_relevant(self, doc):
        """Check if a document is relevant for citizens"""
        title = doc.get('title', '').lower()
        download_link = doc.get('download_link', '').lower()
        section = doc.get('section', '').lower()
        
        # Check for technical patterns first
        for pattern in self.technical_patterns:
            if re.search(pattern, title) or re.search(pattern, section):
                return False
        
        # Check for citizen-relevant keywords
        for keyword in self.citizen_relevant_keywords:
            if keyword in title or keyword in download_link or keyword in section:
                return True
                
        return False

    def download_with_retry(self, url, filename, max_retries=3):
        """Download a file with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    headers=self.headers,
                    verify=False,
                    stream=True,
                    timeout=30
                )
                
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(filename), exist_ok=True)
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return True
                else:
                    print(f"Failed to download {filename}: HTTP {response.status_code}")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to download {filename} after {max_retries} attempts: {str(e)}")
                    return False
        
        return False

    def filter_documents(self, documents):
        """
        Filter documents into citizen-relevant and technical categories
        """
        citizen_docs = []
        technical_docs = []

        for doc in documents:
            if self.is_citizen_relevant(doc):
                citizen_docs.append(doc)
            else:
                technical_docs.append(doc)

        return citizen_docs, technical_docs

    def make_request(self, url, method='GET', **kwargs):
        """
        Make HTTP request with error handling
        """
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to {url}: {str(e)}")
            return None

    def parse_html(self, html_content):
        """
        Parse HTML content using BeautifulSoup
        """
        return BeautifulSoup(html_content, 'html.parser')

    def clean_text(self, text):
        """
        Clean extracted text
        """
        if text:
            return ' '.join(text.split())
        return ''

    def scrape(self, start_date=None, end_date=None):
        """Base scrape method to be implemented by child classes"""
        raise NotImplementedError("Subclasses must implement scrape()")

    def _clean_text(self, text):
        """Clean up text by removing extra whitespace and newlines"""
        if text:
            return ' '.join(text.strip().split())
        return ''

    def get_unique_filename(self, original_filename, title="", section=""):
        """Generate a shorter, unique filename"""
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        
        # Create a shorter name using key information
        # Example: "CAQM_Direction84_20241010.pdf" instead of long name
        if "direction" in title.lower():
            doc_type = "DIR"
        elif "notification" in title.lower():
            doc_type = "NOT"
        else:
            doc_type = "DOC"
        
        # Extract date if present
        date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', title)
        date_str = f"{date_match.group(3)}{date_match.group(2)}{date_match.group(1)}" if date_match else "NODATE"
        
        # Extract document number if present
        num_match = re.search(r'No\.\s*-?\s*(\d+)', title)
        doc_num = num_match.group(1) if num_match else "XX"
        
        # Create shorter filename
        short_name = f"{self.source}_{doc_type}{doc_num}_{date_str}{ext}"
        
        return short_name