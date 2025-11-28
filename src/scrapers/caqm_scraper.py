from .base_scraper import BaseScraper
from .metadata_utils import extract_date, clean_title, determine_section, build_filename, extract_release_date_from_pdf
import requests
from bs4 import BeautifulSoup
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import pdfplumber
import re
from datetime import datetime

def extract_release_date_from_pdf(pdf_path):
    date_patterns = [
        r'(?i)(date[:\\s]*)(\\d{2}[/-]\\d{2}[/-]\\d{4})',
        r'(?i)(issued on[:\\s]*)(\\d{2}[/-]\\d{2}[/-]\\d{4})',
        r'(\\d{2})[/-](\\d{2})[/-](\\d{4})',
        r'(\\d{4})[/-](\\d{2})[/-](\\d{2})',
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},?\\s+\\d{4}',
        r'\\d{1,2}\\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{4}',
    ]
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            if text:
                # 1. Look for date near keywords
                for pattern in date_patterns[:2]:
                    match = re.search(pattern, text)
                    if match:
                        return match.group(2)
                # 2. Fallback: first date found
                for pattern in date_patterns[2:]:
                    match = re.search(pattern, text)
                    if match:
                        return match.group(0)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return None

class CAQMScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://caqm.nic.in"
        self.urls = {
            'main': f"{self.base_url}/index1.aspx?lsid=1070&lev=2&lid=1073&langid=1",
            'orders': f"{self.base_url}/orders",
            'reports': f"{self.base_url}/reports",
            'notifications': f"{self.base_url}/notifications"
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.citizen_relevant_keywords.extend([
            'air quality', 'pollution', 'environment',
            'health', 'public', 'notification', 'order',
            'guideline', 'advisory', 'report', 'action plan'
        ])
        self.technical_patterns.extend([
            'monitoring protocol', 'measurement methodology',
            'calibration', 'technical specification'
        ])

    def scrape(self, start_date=None, end_date=None):
        try:
            print("Starting CAQM PDF count...")
            print(f"Accessing page: {self.urls['main']}")
            response = self.session.get(
                self.urls['main'],
                headers=self.headers,
                verify=False
            )
            if response.status_code != 200:   
                print(f"Failed to access page. Status code: {response.status_code}")
                return []
            soup = BeautifulSoup(response.text, 'html.parser')
            pdf_links = []
            seen_urls = set()
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                try:
                    href = link['href'].lower()
                    if href.endswith('.pdf') or 'writereaddata' in href:
                        if href.startswith('http'):
                            download_link = href
                        else:
                            href = href.replace('..', '')
                            download_link = f"{self.base_url}/{href.lstrip('/')}"
                        if download_link in seen_urls:
                            continue
                        seen_urls.add(download_link)
                        title = clean_title(link.text)
                        if not title:
                            continue
                        parent = link.find_parent(['td', 'p', 'div'])
                        date = extract_date(parent.text) if parent else extract_date(title)
                        section = determine_section(title, link)
                        doc = {
                            'date': date,
                            'title': title,
                            'download_link': download_link,
                            'section': section
                        }
                        pdf_links.append(doc)
                except Exception as e:
                    print(f"Error processing link: {str(e)}")
                    continue
            citizen_documents, technical_documents = self.filter_documents(pdf_links)
            print(f"\nFound {len(citizen_documents)} citizen-relevant documents:")
            print("-" * 80)
            for i, doc in enumerate(citizen_documents, 1):
                print(f"{i}. {doc['title']}")
                print(f"   Date: {doc['date']}")
                print(f"   Section: {doc['section']}")
                print(f"   Download Link: {doc['download_link']}")
                print("-" * 80)
            print(f"\nSkipping {len(technical_documents)} technical documents:")
            for doc in citizen_documents:
                try:
                    download_dir = os.path.join('downloads', self.__class__.__name__.lower().replace('scraper', ''), 'citizen_docs')
                    os.makedirs(download_dir, exist_ok=True)
                    filename = build_filename(doc['title'], doc['date'], doc['section'])
                    filepath = os.path.join(download_dir, filename)
                    if os.path.exists(filepath):
                        print(f"Skipping existing file: {filename}")
                        continue
                    print(f"Downloading citizen-relevant document: {filename}")
                    if self.download_with_retry(doc['download_link'], filepath):
                        # Try to extract date from PDF after download
                        pdf_date = extract_release_date_from_pdf(filepath)
                        if pdf_date:
                            print(f"[PDF Date Extracted] {filename}: {pdf_date}")
                            doc['date'] = pdf_date
                        print(f"Successfully downloaded: {filepath}")
                    else:
                        print(f"Failed to download: {filename}")
                except Exception as e:
                    print(f"Error processing document: {str(e)}")
                    continue
            return citizen_documents
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
