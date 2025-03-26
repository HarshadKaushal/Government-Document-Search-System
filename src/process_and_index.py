import os
from process_documents import DocumentProcessor
from scrapers.income_tax_scraper import IncomeTaxScraper
from scrapers.rbi_scraper import RBIScraper
from scrapers.caqm_scraper import CAQMScraper
import urllib3
import logging
import argparse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process and index government documents')
    parser.add_argument('--es-password', required=True, help='Elasticsearch password')
    args = parser.parse_args()

    # Setup detailed logging
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Initialize processor
    processor = DocumentProcessor(es_password=args.es_password)
    
    # Process documents from downloads directory
    downloads_dir = 'downloads'
    
    if not os.path.exists(downloads_dir):
        logger.error(f"Downloads directory {downloads_dir} does not exist!")
        return

    # Process each subdirectory
    for source in ['income_tax', 'rbi', 'caqm']:
        source_dir = os.path.join(downloads_dir, source)
        if not os.path.exists(source_dir):
            logger.warning(f"Source directory {source_dir} does not exist, skipping...")
            continue

        logger.info(f"\nProcessing documents from {source}...")
        
        # Walk through the directory
        for root, _, files in os.walk(source_dir):
            for filename in files:
                if filename.endswith('.pdf'):
                    pdf_path = os.path.join(root, filename)
                    logger.info(f"Processing: {pdf_path}")
                    
                    try:
                        # Create document metadata
                        doc = {
                            'title': os.path.splitext(filename)[0],
                            'source': source,
                            'date': 'No date',  # You might want to extract this from filename or content
                            'section': os.path.basename(root)
                        }
                        
                        # Index the document
                        success = processor.index_document(doc, pdf_path)
                        if success:
                            logger.info(f"Successfully indexed: {filename}")
                        else:
                            logger.error(f"Failed to index: {filename}")
                            
                    except Exception as e:
                        logger.error(f"Error processing {filename}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 