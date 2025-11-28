from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from .metadata_utils import extract_date, clean_title, determine_section, build_filename, extract_release_date_from_pdf
import os
import requests
import time
import urllib3

# Disable SSL warnings for government websites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RBIScraper(BaseScraper):
    def __init__(self, download_dir=None):
        super().__init__()
        # Use a relative path for downloads
        if download_dir is None:
            download_dir = os.path.join('downloads', 'rbi', 'citizen_docs')
        self.download_dir = download_dir
        self.session = requests.Session()
        self.urls = {
            'press_releases': 'https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx'
        }
        self.citizen_relevant_keywords.extend([
            'bank', 'customer', 'deposit', 'loan',
            'interest rate', 'kyc', 'banking',
            'savings', 'credit', 'debit', 'upi',
            'payment', 'mobile banking', 'protection'
        ])
        self.technical_patterns.extend([
            'basel', 'regulatory reporting',
            'payment system', 'settlement system'
        ])
        os.makedirs(self.download_dir, exist_ok=True)

    def _get_full_url(self, url):
        if url.startswith('http'):
            return url
        elif url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"https://rbidocs.rbi.org.in{url}"
        else:
            return f"https://rbidocs.rbi.org.in/{url}"

    def find_pdf_links(self, soup):
        documents = []
        for link in soup.find_all(['a', 'link'], href=True):
            try:
                href = link['href']
                title = clean_title(link.text)
                if not title:
                    parent = link.find_parent(['td', 'tr', 'div'])
                    if parent:
                        title = clean_title(parent.get_text())
                if not title:
                    continue
                full_url = self._get_full_url(href)
                parent = link.find_parent(['td', 'tr', 'div'])
                date = extract_date(parent.get_text()) if parent else extract_date(title)
                section = determine_section(title, link)
                if (href.endswith('.pdf') or 
                    'notification' in href.lower() or
                    'circular' in href.lower() or
                    'pressrelease' in href.lower()):
                    doc = {
                        'title': title,
                        'download_link': full_url,
                        'date': date,
                        'section': section
                    }
                    documents.append(doc)
            except Exception as e:
                print(f"Error processing link: {str(e)}")
                continue
        return documents

    def download_document(self, doc):
        url = doc['download_link']
        if not url.startswith('http'):
            url = f"https://rbidocs.rbi.org.in{url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        try:
            response = self.session.get(url, headers=headers, verify=False, timeout=30)
            if response.status_code == 200:
                filename = build_filename(doc['title'], doc['date'], doc['section'])
                filepath = os.path.join(self.download_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                # Try to extract date from PDF after download
                pdf_date = extract_release_date_from_pdf(filepath)
                if pdf_date:
                    print(f"[PDF Date Extracted] {filename}: {pdf_date}")
                    doc['date'] = pdf_date
                print(f"Successfully downloaded: {filepath} (size: {os.path.getsize(filepath)} bytes)")
                return True
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
        return False

    def scrape(self, start_date=None, end_date=None):
        url = self.urls['press_releases']
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.session.headers.update(headers)
        response = self.session.get(url, verify=False)
        all_documents = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            documents = self.find_pdf_links(soup)
            citizen_documents, technical_documents = self.filter_documents(documents)
            print(f"\nFound {len(citizen_documents)} citizen-relevant documents:")
            print("-" * 80)
            for i, doc in enumerate(citizen_documents, 1):
                print(f"{i}. {doc['title']}")
                print(f"   Date: {doc['date']}")
                print(f"   Section: {doc['section']}")
                print(f"   Download Link: {doc['download_link']}")
                print("-" * 80)
            print(f"\nSkipping {len(technical_documents)} technical documents")
            for doc in citizen_documents:
                self.download_document(doc)
            all_documents = citizen_documents
        return all_documents

    def filter_documents(self, documents):
        return super().filter_documents(documents)


def scrape_rbi():
    """Standalone function to run RBI scraper"""
    scraper = RBIScraper()
    documents = scraper.scrape()
    print(f"\n✅ RBI Scraping completed. Downloaded {len(documents)} documents.")
    return documents


if __name__ == "__main__":
    scrape_rbi()