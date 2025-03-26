from .base_scraper import BaseScraper
import requests
from bs4 import BeautifulSoup
import os
import logging
from datetime import datetime
import re

class IncomeTaxScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.incometax.gov.in/iec/foportal/"
        self.urls = {
            "main": "https://www.incometax.gov.in/iec/foportal/",
            "downloads": "https://www.incometax.gov.in/iec/foportal/downloads"
        }
        self.seen_filenames = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.incometax.gov.in/"
        }

    def scrape(self):
        """Main scraping method required by BaseScraper"""
        try:
            # Get all PDF links
            documents = self.find_pdf_links()
            
            # Filter documents into citizen-relevant and technical categories
            citizen_documents, technical_documents = self.filter_documents(documents)
            
            # Print summary
            print(f"\nFound {len(citizen_documents)} citizen-relevant documents:")
            print("-" * 80)
            
            for i, doc in enumerate(citizen_documents, 1):
                print(f"{i}. {doc['title']}")
                print(f"   Date: {doc['date']}")
                print(f"   Section: {doc['section']}")
                print(f"   URL: {doc['url']}")
                print("-" * 80)
            
            print(f"\nSkipping {len(technical_documents)} technical documents")
            
            # Download only citizen-relevant documents
            download_dir = os.path.join('downloads', 'income_tax', 'citizen_docs')
            os.makedirs(download_dir, exist_ok=True)
            
            for doc in citizen_documents:
                filename = self.get_unique_filename(
                    os.path.basename(doc['url']),
                    title=doc['title'],
                    section=doc['section']
                )
                filepath = os.path.join(download_dir, filename)
                
                if os.path.exists(filepath):
                    print(f"Skipping existing file: {filename}")
                    continue
                
                print(f"Downloading: {filename}")
                if self.download_with_retry(doc['url'], filepath):
                    print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download: {filename}")
            
            return citizen_documents
            
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
            return []

    def extract_date(self, text):
        try:
            # Try to find a date in the text
            date_patterns = [
                r'(\d{2})[/-](\d{2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
                r'(\d{4})[/-](\d{2})[/-](\d{2})',  # YYYY/MM/DD or YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY-MM-DD format
                        date_obj = datetime.strptime(f"{groups[0]}-{groups[1]}-{groups[2]}", "%Y-%m-%d")
                    else:  # DD-MM-YYYY format
                        date_obj = datetime.strptime(f"{groups[2]}-{groups[1]}-{groups[0]}", "%Y-%m-%d")
                    return date_obj.strftime("%Y-%m-%d")
            
            return datetime.now().strftime("%Y-%m-%d")
        except Exception as e:
            logging.warning(f"Error extracting date: {e}")
            return datetime.now().strftime("%Y-%m-%d")

    def get_unique_filename(self, original_filename, title="", section=""):
        """Generate a unique filename based on document metadata."""
        base, ext = os.path.splitext(original_filename)
        
        # Clean the base filename
        base = re.sub(r'[^\w\s-]', '', base)
        base = base.strip().replace(' ', '_')
        
        # Add section prefix if available
        if section:
            section = re.sub(r'[^\w\s-]', '', section)
            section = section.strip().replace(' ', '_')
            base = f"{section}_{base}"
        
        # Handle special cases
        if "schema" in base.lower():
            base = f"Schema_{base}"
        elif "validation" in base.lower():
            base = f"Validation_{base}"
        
        # Add date if found in title
        date_match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', title)
        if date_match:
            date_str = date_match.group().replace('/', '-')
            base = f"{base}_{date_str}"
        
        filename = f"{base}{ext}"
        counter = 1
        
        while filename.lower() in self.seen_filenames:
            filename = f"{base}_{counter}{ext}"
            counter += 1
        
        self.seen_filenames.add(filename.lower())
        return filename

    def find_pdf_links(self):
        documents = []
        session = requests.Session()
        session.headers.update(self.headers)

        for url_name, url in self.urls.items():
            try:
                response = session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    if href.lower().endswith('.pdf'):
                        title = link.get_text().strip()
                        if not title:
                            title = os.path.basename(href)

                        # Make the URL absolute if it's relative
                        if not href.startswith(('http://', 'https://')):
                            href = requests.compat.urljoin(self.base_url, href)
                        
                        # Determine section based on URL and context
                        section = url_name.capitalize()
                        if "schema" in href.lower() or "schema" in title.lower():
                            section = "Schema"
                        elif "validation" in href.lower() or "validation" in title.lower():
                            section = "Validation"
                        
                        document = {
                            'title': title,
                            'date': self.extract_date(title),
                            'url': href,
                            'section': section
                        }
                        documents.append(document)

            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching {url}: {e}")
                continue

        return documents

    def download_with_retry(self, url, filename, max_retries=3):
        """Download a file with retry logic."""
        session = requests.Session()
        session.headers.update(self.headers)
        
        for attempt in range(max_retries):
            try:
                response = session.get(url, stream=True)
                response.raise_for_status()
                
                # Verify it's a PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type:
                    logging.warning(f"Skipping non-PDF URL: {url} (Content-Type: {content_type})")
                    return False
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to download {url} after {max_retries} attempts: {e}")
                    return False
                logging.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                continue
            
        return False