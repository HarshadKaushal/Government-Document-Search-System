#!/usr/bin/env python3
"""
Main entry point for downloading PDFs from government websites.

This script runs the scrapers for Income Tax, RBI, and CAQM to download
citizen-relevant PDF documents.

Usage:
    python src/download_pdfs.py                    # Run all scrapers
    python src/download_pdfs.py --source rbi       # Run only RBI scraper
    python src/download_pdfs.py --source all       # Run all scrapers
    python src/download_pdfs.py --source income_tax,caqm  # Run specific scrapers
"""

import argparse
import sys
import os
from datetime import datetime
import time

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import IncomeTaxScraper, RBIScraper, CAQMScraper

# Map source names to scraper classes
SCRAPER_MAP = {
    'income_tax': IncomeTaxScraper,
    'rbi': RBIScraper,
    'caqm': CAQMScraper,
    'all': None  # Special case for all scrapers
}

AVAILABLE_SOURCES = ['income_tax', 'rbi', 'caqm', 'all']


def run_scraper(scraper_class, source_name):
    """
    Run a single scraper and return results.
    
    Args:
        scraper_class: The scraper class to instantiate
        source_name: Name of the source (for logging)
    
    Returns:
        tuple: (success: bool, count: int, error_message: str or None)
    """
    print(f"\n{'='*80}")
    print(f"Starting {source_name.upper()} scraper...")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        scraper = scraper_class()
        documents = scraper.scrape()
        
        elapsed_time = time.time() - start_time
        
        if documents:
            print(f"\n[SUCCESS] {source_name.upper()} scraping completed successfully!")
            print(f"   - Downloaded/Processed: {len(documents)} documents")
            print(f"   - Time taken: {elapsed_time:.2f} seconds")
            return True, len(documents), None
        else:
            print(f"\n[WARNING] {source_name.upper()} scraping completed but found no new documents.")
            return True, 0, None
            
    except KeyboardInterrupt:
        print(f"\n[ERROR] {source_name.upper()} scraping interrupted by user.")
        return False, 0, "Interrupted by user"
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error during {source_name} scraping: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        print(f"   - Time taken: {elapsed_time:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False, 0, error_msg


def main():
    """Main function to run the scrapers."""
    parser = argparse.ArgumentParser(
        description='Download PDFs from government websites',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/download_pdfs.py                    # Run all scrapers
  python src/download_pdfs.py --source rbi       # Run only RBI scraper
  python src/download_pdfs.py --source income_tax,caqm  # Run specific scrapers
        """
    )
    
    parser.add_argument(
        '--source',
        type=str,
        default='all',
        help=f'Source to scrape: {", ".join(AVAILABLE_SOURCES)} or comma-separated list (default: all)'
    )
    
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip already downloaded files (default: enabled)'
    )
    
    args = parser.parse_args()
    
    # Parse source argument
    sources = [s.strip().lower() for s in args.source.split(',')]
    
    # Validate sources
    invalid_sources = [s for s in sources if s not in AVAILABLE_SOURCES and s not in SCRAPER_MAP]
    if invalid_sources:
        print(f"[ERROR] Invalid source(s): {', '.join(invalid_sources)}")
        print(f"   Available sources: {', '.join(AVAILABLE_SOURCES)}")
        sys.exit(1)
    
    # Handle 'all' source
    if 'all' in sources:
        sources = ['income_tax', 'rbi', 'caqm']
    
    # Remove duplicates while preserving order
    seen = set()
    sources = [s for s in sources if not (s in seen or seen.add(s))]
    
    # Print header
    print("\n" + "="*80)
    print("  Government Document Scraper")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sources to scrape: {', '.join(s.upper() for s in sources)}")
    print(f"Skip existing files: {'Yes' if args.skip_existing else 'No'}")
    print("="*80)
    
    # Run scrapers
    results = []
    total_start_time = time.time()
    
    for source_name in sources:
        if source_name not in SCRAPER_MAP:
            print(f"\n[WARNING] Skipping unknown source: {source_name}")
            continue
        
        scraper_class = SCRAPER_MAP[source_name]
        success, count, error = run_scraper(scraper_class, source_name)
        
        results.append({
            'source': source_name,
            'success': success,
            'count': count,
            'error': error
        })
        
        # Small delay between scrapers to be polite
        if source_name != sources[-1]:  # Don't delay after last scraper
            print("\nWaiting 2 seconds before next scraper...")
            time.sleep(2)
    
    # Print summary
    total_time = time.time() - total_start_time
    
    print("\n" + "="*80)
    print("  SCRAPING SUMMARY")
    print("="*80)
    
    total_documents = 0
    successful_scrapers = 0
    failed_scrapers = 0
    
    for result in results:
        status = "[SUCCESS]" if result['success'] else "[FAILED]"
        print(f"{result['source'].upper():15} {status:12} {result['count']:4} documents")
        if result['error']:
            print(f"  └─ Error: {result['error']}")
        
        total_documents += result['count']
        if result['success']:
            successful_scrapers += 1
        else:
            failed_scrapers += 1
    
    print("="*80)
    print(f"Total documents downloaded/processed: {total_documents}")
    print(f"Successful scrapers: {successful_scrapers}/{len(results)}")
    if failed_scrapers > 0:
        print(f"Failed scrapers: {failed_scrapers}/{len(results)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Exit with appropriate code
    if failed_scrapers > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()


