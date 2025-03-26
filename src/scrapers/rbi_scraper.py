from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import re

class RBIScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.rbi.org.in"
        self.urls = {
            'press_releases': f"{self.base_url}/Scripts/BS_PressReleaseDisplay.aspx",
            'notifications': f"{self.base_url}/Scripts/NotificationUser.aspx",
            'circulars': f"{self.base_url}/Scripts/BS_CircularIndexDisplay.aspx",
            'speeches': f"{self.base_url}/Scripts/BS_SpeechesView.aspx"
        }
        
        # Add RBI specific keywords
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

    def extract_date(self, text):
        """Extract date from text using various formats"""
        # Common date patterns in RBI releases
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def determine_section(self, link):
        """Determine the section based on the link context"""
        href = link.get('href', '').lower()
        if 'notification' in href:
            return 'Notifications'
        elif 'circular' in href:
            return 'Circulars'
        elif 'pressrelease' in href:
            return 'Press Releases'
        elif 'speech' in href:
            return 'Speeches'
        return 'Other'

    def find_pdf_links(self, soup):
        documents = []
        
        # Look for links in various containers
        for link in soup.find_all(['a', 'link'], href=True):
            try:
                href = link['href']
                title = self._clean_text(link.text)
                
                if not title:
                    # Try to get title from parent elements
                    parent = link.find_parent(['td', 'tr', 'div'])
                    if parent:
                        title = self._clean_text(parent.get_text())
                
                if not title:
                    continue
                
                # Build full URL if needed
                full_url = (href if href.startswith('http') 
                          else f"{self.base_url}/{href.lstrip('/')}")
                
                # Extract date
                date = "No date"
                parent = link.find_parent(['td', 'tr', 'div'])
                if parent:
                    date = self.extract_date(parent.get_text()) or "No date"
                
                if (href.endswith('.pdf') or 
                    'notification' in href.lower() or
                    'circular' in href.lower() or
                    'pressrelease' in href.lower()):
                    
                    section = self.determine_section(link)
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

    def scrape(self, start_date=None, end_date=None):
        try:
            print("Starting RBI documents scrape...")
            all_documents = []
            
            # Scrape each URL
            for page_name, url in self.urls.items():
                print(f"Accessing {page_name} page: {url}")
                response = self.session.get(
                    url,
                    headers=self.headers,
                    verify=False
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    documents = self.find_pdf_links(soup)
                    all_documents.extend(documents)
            
            # Filter documents
            citizen_documents, technical_documents = self.filter_documents(all_documents)
            
            # Print summary
            print(f"\nFound {len(citizen_documents)} citizen-relevant documents:")
            print("-" * 80)
            
            for i, doc in enumerate(citizen_documents, 1):
                print(f"{i}. {doc['title']}")
                print(f"   Date: {doc['date']}")
                print(f"   Section: {doc['section']}")
                print(f"   Download Link: {doc['download_link']}")
                print("-" * 80)

            return citizen_documents

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []