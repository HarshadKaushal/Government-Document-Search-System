#!/usr/bin/env python3
"""
Batch process all downloaded PDFs.
Extracts text, splits into chunks, and saves processed documents.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processors import PDFProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_pdf_files(download_dir: str) -> List[str]:
    """Find all PDF files in the download directory."""
    pdf_files = []
    download_path = Path(download_dir)
    
    if not download_path.exists():
        logger.error(f"Download directory does not exist: {download_dir}")
        return pdf_files
    
    for pdf_file in download_path.rglob("*.pdf"):
        pdf_files.append(str(pdf_file))
    
    return sorted(pdf_files)


def process_all_pdfs(download_dir: str = "downloads", 
                     output_dir: str = "data/processed",
                     chunk_size: int = 500,
                     chunk_overlap: int = 100,
                     skip_existing: bool = True):
    """
    Process all PDFs in the download directory.
    
    Args:
        download_dir: Directory containing downloaded PDFs
        output_dir: Directory to save processed JSON files
        chunk_size: Number of words per chunk
        chunk_overlap: Number of words to overlap between chunks
        skip_existing: Skip already processed files
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize processor
    processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    # Find all PDF files
    pdf_files = find_pdf_files(download_dir)
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {download_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_file = Path(pdf_path)
        
        # Generate output filename
        output_filename = pdf_file.stem + ".json"
        output_filepath = output_path / output_filename
        
        # Skip if already processed
        if skip_existing and output_filepath.exists():
            skipped_count += 1
            continue
        
        try:
            # Process PDF
            doc = processor.process_pdf(pdf_path)
            
            if doc:
                # Save processed document
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump(doc, f, indent=2, ensure_ascii=False)
                processed_count += 1
            else:
                logger.warning(f"Failed to process: {pdf_path}")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}", exc_info=True)
            failed_count += 1
    
    # Print summary
    logger.info("="*80)
    logger.info("PROCESSING SUMMARY")
    logger.info("="*80)
    logger.info(f"Total PDFs: {len(pdf_files)}")
    logger.info(f"Processed: {processed_count}")
    logger.info(f"Skipped (already processed): {skipped_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process all downloaded PDFs and extract text',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--download-dir',
        type=str,
        default='downloads',
        help='Directory containing downloaded PDFs (default: downloads)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed',
        help='Directory to save processed JSON files (default: data/processed)'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=500,
        help='Number of words per chunk (default: 500)'
    )
    
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=100,
        help='Number of words to overlap between chunks (default: 100)'
    )
    
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Re-process already processed files'
    )
    
    args = parser.parse_args()
    
    process_all_pdfs(
        download_dir=args.download_dir,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        skip_existing=not args.no_skip_existing
    )


if __name__ == "__main__":
    main()


