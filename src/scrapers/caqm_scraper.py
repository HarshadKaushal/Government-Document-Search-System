from .base_scraper import BaseScraper
import requests
from bs4 import BeautifulSoup
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        # Add CAQM specific keywords
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
            
            # Find all links that end with .pdf
            pdf_links = []
            seen_urls = set()
            
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                try:
                    href = link['href'].lower()
                    if href.endswith('.pdf') or 'writereaddata' in href:
                        # Build the full URL
                        if href.startswith('http'):
                            download_link = href
                        else:
                            href = href.replace('..', '')
                            download_link = f"{self.base_url}/{href.lstrip('/')}"
                        
                        # Skip if we've seen this URL
                        if download_link in seen_urls:
                            continue
                        seen_urls.add(download_link)
                        
                        # Get the title
                        title = self._clean_text(link.text)
                        if not title:
                            continue
                        
                        # Look for date in parent elements
                        date = "No date"
                        parent = link.find_parent(['td', 'p', 'div'])
                        if parent:
                            date_text = self._clean_text(parent.text)
                            import re
                            date_match = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', date_text)
                            if date_match:
                                date = date_match.group(0)
                        
                        # Create document with standardized keys
                        doc = {
                            'date': date,
                            'title': title,
                            'download_link': download_link,
                            'section': self.determine_section(link)
                        }
                        pdf_links.append(doc)

                except Exception as e:
                    print(f"Error processing link: {str(e)}")
                    continue

            # Filter documents
            citizen_documents, technical_documents = self.filter_documents(pdf_links)

            # Print summary
            print(f"\nFound {len(citizen_documents)} citizen-relevant documents:")
            print("-" * 80)
            
            for i, doc in enumerate(citizen_documents, 1):
                print(f"{i}. {doc['title']}")
                print(f"   Date: {doc['date']}")
                print(f"   Section: {doc['section']}")
                print(f"   Download Link: {doc['download_link']}")
                print("-" * 80)

            print(f"\nSkipping {len(technical_documents)} technical documents:")
            for doc in technical_documents:
                print(f"Skipping technical document: {doc['title']}")

            # Download only citizen-relevant documents
            for doc in citizen_documents:
                try:
                    # Create appropriate subdirectory
                    download_dir = os.path.join('downloads', self.__class__.__name__.lower().replace('scraper', ''), 'citizen_docs')
                    os.makedirs(download_dir, exist_ok=True)
                    
                    filename = self.get_unique_filename(doc['title'], doc['download_link'], doc['date'])
                    filepath = os.path.join(download_dir, filename)
                    
                    if os.path.exists(filepath):
                        print(f"Skipping existing file: {filename}")
                        continue
                    
                    print(f"Downloading citizen-relevant document: {filename}")
                    if self.download_with_retry(doc['download_link'], filepath):
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

    def _clean_text(self, text):
        """Clean up text by removing extra whitespace and newlines"""
        if text:
            return ' '.join(text.strip().split())
        return ''

    def find_pdf_links(self, soup):
        documents = []
        
        # Look for links in various containers
        for link in soup.find_all('a', href=True):
            try:
                href = link['href']
                title = self._clean_text(link.text)
                
                if not title or not href:
                    continue
                
                # Build full URL if needed
                full_url = (href if href.startswith('http') 
                          else f"{self.base_url}/{href.lstrip('/')}")
                
                if href.endswith('.pdf'):
                    section = self.determine_section(link)
                    doc = {
                        'title': title,
                        'download_link': full_url,
                        'date': self.extract_date(title) or "No date",
                        'section': section
                    }
                    documents.append(doc)
                
            except Exception as e:
                print(f"Error processing link: {str(e)}")
                continue
                
        return documents

    def determine_section(self, element):
        """Determine which section a document belongs to"""
        try:
            # Check element and its parents for section indicators
            for parent in [element] + list(element.parents):
                if 'notification' in parent.get_text().lower():
                    return 'Notifications'
                elif 'circular' in parent.get_text().lower():
                    return 'Circulars'
                elif 'order' in parent.get_text().lower():
                    return 'Orders'
            return 'Other'
        except:
            return 'Other'
