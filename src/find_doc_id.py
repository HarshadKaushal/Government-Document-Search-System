#!/usr/bin/env python3
"""
Utility script to find doc_id for a given filename or search for documents.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Python < 3.7 or reconfigure failed
        pass

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search.es_setup import ElasticsearchSetup
from processors.pdf_processor import PDFProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def find_doc_id_by_filename(filename: str, es_setup: ElasticsearchSetup, index_name: str = "government_documents"):
    """Find doc_id by searching Elasticsearch for the filename."""
    try:
        es_client = es_setup.get_client()
        
        # Search for documents with matching filename
        query = {
            "bool": {
                "must": [
                    {"wildcard": {"filename": f"*{filename}*"}}
                ]
            }
        }
        
        response = es_client.search(
            index=index_name,
            query=query,
            size=10
        )
        
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            results.append({
                'doc_id': source.get('doc_id', ''),
                'filename': source.get('filename', ''),
                'title': source.get('title', ''),
                'source': source.get('source', ''),
                'filepath': source.get('filepath', '')
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching Elasticsearch: {e}")
        return []


def generate_doc_id_from_filepath(filepath: str):
    """Generate doc_id for a filepath (same method as PDFProcessor)."""
    processor = PDFProcessor()
    if os.path.exists(filepath):
        return processor.generate_doc_id(filepath)
    else:
        logger.warning(f"File not found: {filepath}")
        return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Find doc_id for a document')
    parser.add_argument('filename', type=str, nargs='?',
                       help='Filename to search for (e.g., "Circulars_Tax_Payer_Charter_NODATE.pdf")')
    parser.add_argument('--filepath', type=str,
                       help='Full filepath to generate doc_id from')
    parser.add_argument('--search', type=str,
                       help='Search query to find documents')
    parser.add_argument('--es-host', type=str, default='localhost',
                       help='Elasticsearch host')
    parser.add_argument('--es-port', type=int, default=9200,
                       help='Elasticsearch port')
    parser.add_argument('--es-username', type=str, default='elastic',
                       help='Elasticsearch username')
    parser.add_argument('--es-password', type=str, default=None,
                       help='Elasticsearch password')
    parser.add_argument('--index-name', type=str, default='government_documents',
                       help='Elasticsearch index name')
    
    args = parser.parse_args()
    
    # Initialize Elasticsearch
    try:
        es_setup = ElasticsearchSetup(
            host=args.es_host,
            port=args.es_port,
            username=args.es_username,
            password=args.es_password
        )
        logger.info("✓ Connected to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        logger.error("Make sure Elasticsearch is running")
        return
    
    # Search by filename
    if args.filename:
        logger.info(f"\nSearching for filename: {args.filename}")
        results = find_doc_id_by_filename(args.filename, es_setup, args.index_name)
        
        if results:
            print(f"\n{'='*80}")
            print(f"Found {len(results)} matching document(s):")
            print(f"{'='*80}\n")
            
            for i, result in enumerate(results, 1):
                print(f"[{i}]")
                print(f"  Doc ID:    {result['doc_id']}")
                print(f"  Filename:  {result['filename']}")
                print(f"  Title:     {result['title']}")
                print(f"  Source:    {result['source']}")
                print(f"  Filepath:  {result['filepath']}")
                print()
        else:
            print(f"\n[!] No documents found matching: {args.filename}")
            print("\nTip: Try using --search to find documents by content")
    
    # Generate doc_id from filepath
    elif args.filepath:
        logger.info(f"\nGenerating doc_id for filepath: {args.filepath}")
        doc_id = generate_doc_id_from_filepath(args.filepath)
        
        if doc_id:
            print(f"\n{'='*80}")
            print(f"Doc ID: {doc_id}")
            print(f"Filepath: {args.filepath}")
            print(f"{'='*80}\n")
        else:
            print(f"\n[!] Could not generate doc_id")
    
    # Search by query
    elif args.search:
        logger.info(f"\nSearching for: {args.search}")
        try:
            from search.search_service import SearchService
            from embeddings.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            search_service = SearchService(
                es_setup=es_setup,
                embedding_service=embedding_service,
                index_name=args.index_name
            )
            
            results = search_service.search(args.search, size=10)
            
            if results:
                print(f"\n{'='*80}")
                print(f"Found {len(results)} result(s):")
                print(f"{'='*80}\n")
                
                for i, result in enumerate(results, 1):
                    print(f"[{i}]")
                    print(f"  Doc ID:    {result.get('doc_id', 'N/A')}")
                    print(f"  Title:     {result.get('title', 'N/A')}")
                    print(f"  Filename:  {result.get('filename', 'N/A')}")
                    print(f"  Source:    {result.get('source', 'N/A')}")
                    print(f"  Score:     {result.get('score', 0):.4f}")
                    print()
            else:
                print(f"\n[!] No results found")
        except Exception as e:
            logger.error(f"Error searching: {e}")
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  # Find doc_id by filename")
        print("  python src/find_doc_id.py Circulars_Tax_Payer_Charter_NODATE.pdf")
        print("\n  # Generate doc_id from filepath")
        print("  python src/find_doc_id.py --filepath downloads/income_tax/Circulars_Tax_Payer_Charter_NODATE.pdf")
        print("\n  # Search for documents")
        print("  python src/find_doc_id.py --search 'tax payer charter'")


if __name__ == '__main__':
    main()

