import sys
import os
import logging
from datetime import datetime, timedelta
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Force output buffering
sys.stdout.reconfigure(line_buffering=True)

# Configure logging to show everything
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

# Create a console handler with higher verbosity
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

def main():
    print("Starting the scraper script...")
    print("Initializing scraper...")
    
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    start_date_str = start_date.strftime("%d-%m-%Y")
    end_date_str = end_date.strftime("%d-%m-%Y")
    
    print(f"Searching for documents between {start_date_str} and {end_date_str}")
    
    # Test connection first
    print("Making request to CAQM...")
    try:
        test_response = requests.get("https://caqm.nic.in", verify=False)
        print(f"Connection test status code: {test_response.status_code}")
    except Exception as e:
        print(f"Error in test connection: {str(e)}")
        return

    # Initialize and run scraper
    scraper = CAQMScraper()
    results = scraper.scrape(start_date_str, end_date_str)
    
    # Print results
    if results:
        print("\nFound documents:")
        for idx, doc in enumerate(results, 1):
            print(f"\nDocument {idx}:")
            print(f"Date: {doc['date']}")
            print(f"Title: {doc['title']}")
            print(f"Download Link: {doc['download_link']}")
            print("-" * 80)
    else:
        print("No documents found")

if __name__ == "__main__":
    # Make sure the imports are working
    try:
        from scrapers.caqm_scraper import CAQMScraper
        print("Successfully imported CAQMScraper")
        main()
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Current directory:", os.getcwd())
        print("Python path:", sys.path)