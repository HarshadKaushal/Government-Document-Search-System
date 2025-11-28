from .base_scraper import BaseScraper
from .metadata_utils import extract_date, clean_title, determine_section, build_filename, extract_release_date_from_pdf
import requests
from bs4 import BeautifulSoup
import os
import logging

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
        try:
            documents = self.find_pdf_links()
            citizen_documents, technical_documents = self.filter_documents(documents)
            print(f"\nFound {len(citizen_documents)} citizen-relevant documents:")
            print("-" * 80)
            for i, doc in enumerate(citizen_documents, 1):
                print(f"{i}. {doc['title']}")
                print(f"   Date: {doc['date']}")
                print(f"   Section: {doc['section']}")
                print(f"   URL: {doc['url']}")
                print("-" * 80)
            print(f"\nSkipping {len(technical_documents)} technical documents")
            download_dir = os.path.join('downloads', 'income_tax', 'citizen_docs')
            os.makedirs(download_dir, exist_ok=True)
            for doc in citizen_documents:
                filename = build_filename(doc['title'], doc['date'], doc['section'])
                filepath = os.path.join(download_dir, filename)
                if os.path.exists(filepath):
                    print(f"Skipping existing file: {filename}")
                    continue
                print(f"Downloading: {filename}")
                if self.download_with_retry(doc['url'], filepath):
                    # Try to extract date from PDF after download
                    pdf_date = extract_release_date_from_pdf(filepath)
                    if pdf_date:
                        print(f"[PDF Date Extracted] {filename}: {pdf_date}")
                        doc['date'] = pdf_date
                    print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download: {filename}")
            return citizen_documents
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
            return []

    def find_pdf_links(self):
        documents = []
        session = requests.Session()
        session.headers.update(self.headers)
        for url_name, url in self.urls.items():
            try:
                response = session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if href.lower().endswith('.pdf'):
                        title = clean_title(link.get_text())
                        if not title:
                            title = os.path.basename(href)
                        if not href.startswith(('http://', 'https://')):
                            href = requests.compat.urljoin(self.base_url, href)
                        section = determine_section(title, link)
                        date = extract_date(title) or extract_date(link.get_text())
                        if not date:
                            date = None
                        document = {
                            'title': title,
                            'date': date,
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