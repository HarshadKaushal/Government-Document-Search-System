from scrapers.income_tax_scraper import IncomeTaxScraper
from scrapers.caqm_scraper import CAQMScraper
from scrapers.rbi_scraper import RBIScraper
import os
import requests
import urllib3
import re
from datetime import datetime
import logging
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def sanitize_filename(filename):
    """Clean filename by removing invalid characters and limiting length"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Limit length (Windows has 260 char limit, using 240 to be safe)
    if len(filename) > 240:
        name, ext = os.path.splitext(filename)
        filename = name[:236] + ext
    return filename.strip()

def format_date(date_str):
    """Convert various date formats to YYYY-MM-DD"""
    if not date_str or date_str == 'No date':
        return ''
    
    try:
        # Try different date formats
        for fmt in ['%B %d, %Y', '%d %B %Y', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
    except Exception:
        return date_str
    return date_str

def download_pdfs():
    # Create downloads directory if it doesn't exist
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    # Initialize scrapers
    caqm_scraper = CAQMScraper()
    rbi_scraper = RBIScraper()
    income_tax_scraper = IncomeTaxScraper()
    
    # Get documents from each scraper
    scrapers = {
        'caqm': caqm_scraper,
        'rbi': rbi_scraper,
        'income_tax': income_tax_scraper
    }
    
    for source, scraper in scrapers.items():
        print(f"\nProcessing {source.upper()} documents...")
        documents = scraper.scrape()
        
        # Create source-specific directory
        source_dir = os.path.join('downloads', source)
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)
        
        # Download PDFs
        for doc in documents:
            try:
                url = doc['download_link']
                title = doc['title']
                date = format_date(doc.get('date', ''))
                
                # Create filename with date prefix if available
                if date:
                    base_filename = f"{date}_{title}"
                else:
                    base_filename = title
                
                # Add .pdf extension if not present
                if not base_filename.lower().endswith('.pdf'):
                    base_filename += '.pdf'
                
                # Sanitize filename
                filename = sanitize_filename(base_filename)
                filepath = os.path.join(source_dir, filename)
                
                # Skip if file already exists
                if os.path.exists(filepath):
                    print(f"Skipping existing file: {filename}")
                    continue
                
                print(f"Downloading: {filename}")
                response = requests.get(url, verify=False)
                
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download {filename}. Status code: {response.status_code}")
                    
            except Exception as e:
                print(f"Error downloading document: {str(e)}")
                continue

def main():
    # Create scrapers
    income_tax = IncomeTaxScraper()
    caqm = CAQMScraper()
    rbi = RBIScraper()
    
    # Run scrapers
    print("Processing Income Tax documents...")
    income_tax.scrape()
    
    print("\nProcessing CAQM documents...")
    caqm.scrape()
    
    print("\nProcessing RBI documents...")
    rbi.scrape()

if __name__ == "__main__":
    main()