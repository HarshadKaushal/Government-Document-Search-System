#!/usr/bin/env python3
"""
Command-line interface for searching government documents.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from collections import defaultdict

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
from search.search_service import SearchService
from embeddings.embedding_service import EmbeddingService

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise for CLI
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def format_result(result: dict, index: int) -> str:
    """Format a single search result for display."""
    title = result.get('title', 'Unknown Title')
    source = result.get('source', 'unknown').upper()
    score = result.get('score', 0)
    date = result.get('date', 'N/A')
    section = result.get('section', 'Document')
    chunk_text = result.get('text_chunk', '')
    page = result.get('page', '?')
    filename = result.get('filename', '')
    
    # Format score as percentage
    score_pct = min(score * 100, 100) if score > 0 else 0
    
    # Clean and truncate chunk text for preview
    preview = chunk_text.replace('\n', ' ').strip()
    if len(preview) > 200:
        preview = preview[:200] + "..."
    
    # Build formatted output
    output = []
    output.append(f"\n{'='*80}")
    output.append(f"[{index}] {title}")
    output.append(f"{'─'*80}")
    output.append(f"Source: {source}  |  Section: {section}  |  Date: {date}  |  Relevance: {score_pct:.1f}%")
    if page:
        output.append(f"Page: {page}  |  File: {filename}")
    output.append(f"\nPreview:")
    output.append(f"  {preview}")
    output.append(f"{'='*80}")
    
    return "\n".join(output)


def deduplicate_results(results: list, top_per_doc: int = 1) -> list:
    """Deduplicate results - keep only the top chunk per document."""
    doc_results = defaultdict(list)
    
    for result in results:
        doc_id = result.get('doc_id', '')
        doc_results[doc_id].append(result)
    
    # For each document, keep only the highest scoring chunk
    deduplicated = []
    for doc_id, chunks in doc_results.items():
        # Sort by score and take top chunk
        sorted_chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)
        deduplicated.append(sorted_chunks[0])
    
    # Re-sort all deduplicated results by score
    deduplicated.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return deduplicated


def search_documents(query: str,
                    size: int = 10,
                    source: Optional[str] = None,
                    section: Optional[str] = None,
                    deduplicate: bool = True,
                    search_type: str = 'semantic',
                    es_host: str = 'localhost',
                    es_port: int = 9200,
                    es_username: Optional[str] = None,
                    es_password: Optional[str] = None):
    """
    Search documents and display results.
    
    Args:
        query: Search query string
        size: Number of results to return
        source: Filter by source (rbi, income_tax, caqm)
        section: Filter by section
        deduplicate: Whether to deduplicate results (one per document)
        es_host: Elasticsearch host
        es_port: Elasticsearch port
        es_username: Elasticsearch username
        es_password: Elasticsearch password
    """
    search_type_label = "Semantic (Vector-based)" if search_type == 'semantic' else "Keyword (BM25)"
    print(f"\n🔍 Searching for: '{query}'")
    print(f"   Search type: {search_type_label}")
    if source:
        print(f"   Filter: Source = {source}")
    if section:
        print(f"   Filter: Section = {section}")
    print()
    
    try:
        # Initialize services
        es_setup = ElasticsearchSetup(
            host=es_host,
            port=es_port,
            username=es_username,
            password=es_password
        )
        
        embedding_service = EmbeddingService()
        search_service = SearchService(
            es_setup=es_setup,
            embedding_service=embedding_service,
            index_name='government_documents'
        )
        
        # Perform search (get more results if deduplicating)
        search_size = size * 3 if deduplicate else size
        
        if search_type == 'semantic':
            results = search_service.search(
                query=query,
                size=search_size,
                source=source,
                section=section
            )
        else:  # keyword search
            results = search_service.keyword_search(
                query=query,
                size=search_size,
                source=source,
                section=section
            )
        
        if not results:
            print("❌ No results found.")
            print("\nTry:")
            print("  - Broadening your search terms")
            print("  - Removing filters")
            print("  - Checking spelling")
            return
        
        # Deduplicate if requested
        if deduplicate:
            results = deduplicate_results(results, top_per_doc=1)
            results = results[:size]  # Limit to requested size after deduplication
        
        # Display results
        print(f"✅ Found {len(results)} result(s):\n")
        
        for i, result in enumerate(results, 1):
            print(format_result(result, i))
        
        print(f"\n📊 Summary: {len(results)} document(s) found")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Search interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error("Search failed", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Search government documents using semantic search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python src/search_documents.py "income tax return filing"
  
  # Search with source filter
  python src/search_documents.py "banking regulations" --source rbi
  
  # Search with section filter
  python src/search_documents.py "tax rules" --section Circulars
  
  # Get more results
  python src/search_documents.py "pollution control" --size 20
  
  # Show all chunks (no deduplication)
  python src/search_documents.py "monetary policy" --no-deduplicate
        """
    )
    
    parser.add_argument(
        'query',
        type=str,
        help='Search query text'
    )
    
    parser.add_argument(
        '--size',
        type=int,
        default=10,
        help='Number of results to return (default: 10)'
    )
    
    parser.add_argument(
        '--source',
        type=str,
        choices=['rbi', 'income_tax', 'caqm'],
        help='Filter by source: rbi, income_tax, or caqm'
    )
    
    parser.add_argument(
        '--section',
        type=str,
        help='Filter by section (e.g., Circulars, Notifications)'
    )
    
    parser.add_argument(
        '--no-deduplicate',
        action='store_true',
        help='Show all chunks instead of one per document'
    )
    
    parser.add_argument(
        '--search-type',
        type=str,
        choices=['semantic', 'keyword', 'both'],
        default='semantic',
        help='Search type: semantic (vector-based), keyword (BM25), or both (default: semantic)'
    )
    
    parser.add_argument(
        '--es-host',
        type=str,
        default='localhost',
        help='Elasticsearch host (default: localhost)'
    )
    
    parser.add_argument(
        '--es-port',
        type=int,
        default=9200,
        help='Elasticsearch port (default: 9200)'
    )
    
    parser.add_argument(
        '--es-username',
        type=str,
        default=None,
        help='Elasticsearch username'
    )
    
    parser.add_argument(
        '--es-password',
        type=str,
        default=None,
        help='Elasticsearch password'
    )
    
    args = parser.parse_args()
    
    # Handle 'both' search type
    if args.search_type == 'both':
        # Run semantic search
        print("=" * 80)
        print("SEMANTIC SEARCH RESULTS")
        print("=" * 80)
        search_documents(
            query=args.query,
            size=args.size,
            source=args.source,
            section=args.section,
            deduplicate=not args.no_deduplicate,
            search_type='semantic',
            es_host=args.es_host,
            es_port=args.es_port,
            es_username=args.es_username,
            es_password=args.es_password
        )
        print("\n" + "=" * 80)
        print("KEYWORD SEARCH RESULTS")
        print("=" * 80)
        # Run keyword search
        search_documents(
            query=args.query,
            size=args.size,
            source=args.source,
            section=args.section,
            deduplicate=not args.no_deduplicate,
            search_type='keyword',
            es_host=args.es_host,
            es_port=args.es_port,
            es_username=args.es_username,
            es_password=args.es_password
        )
    else:
        # Run single search type
        search_documents(
            query=args.query,
            size=args.size,
            source=args.source,
            section=args.section,
            deduplicate=not args.no_deduplicate,
            search_type=args.search_type,
            es_host=args.es_host,
            es_port=args.es_port,
            es_username=args.es_username,
            es_password=args.es_password
        )


if __name__ == "__main__":
    main()

