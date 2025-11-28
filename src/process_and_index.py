#!/usr/bin/env python3
"""
Process PDFs and index them into Elasticsearch with semantic embeddings.
This script:
1. Loads processed documents (or processes PDFs if not already processed)
2. Generates embeddings for all text chunks
3. Indexes documents into Elasticsearch
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
from embeddings import EmbeddingService
from search import ElasticsearchSetup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_processed_documents(processed_dir: str) -> List[Dict]:
    """
    Load all processed documents from JSON files.
    
    Args:
        processed_dir: Directory containing processed JSON files
        
    Returns:
        List of document dictionaries
    """
    documents = []
    processed_path = Path(processed_dir)
    
    if not processed_path.exists():
        logger.warning(f"Processed directory does not exist: {processed_dir}")
        return documents
    
    json_files = list(processed_path.glob("*.json"))
    logger.info(f"Loading {len(json_files)} processed documents...")
    
    for json_file in tqdm(json_files, desc="Loading documents"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to load {json_file}: {e}")
    
    return documents


def index_documents(documents: List[Dict],
                   embedding_service: EmbeddingService,
                   es_setup: ElasticsearchSetup,
                   index_name: str,
                   batch_size: int = 32):
    """
    Generate embeddings and index documents into Elasticsearch.
    
    Args:
        documents: List of processed document dictionaries
        embedding_service: EmbeddingService instance
        es_setup: ElasticsearchSetup instance
        index_name: Name of the Elasticsearch index
        batch_size: Batch size for embedding generation
    """
    logger.info(f"Indexing {len(documents)} documents...")
    
    total_chunks = sum(len(doc.get('text_chunks', [])) for doc in documents)
    logger.info(f"Total chunks to index: {total_chunks}")
    
    indexed_count = 0
    failed_count = 0
    
    # Process documents in batches
    for doc in tqdm(documents, desc="Processing documents"):
        try:
            text_chunks = doc.get('text_chunks', [])
            
            if not text_chunks:
                logger.warning(f"No chunks found in document: {doc.get('title', 'Unknown')}")
                continue
            
            # Generate embeddings for all chunks in this document
            chunk_texts = [chunk['text'] for chunk in text_chunks]
            embeddings = embedding_service.generate_embeddings_batch(
                chunk_texts,
                batch_size=batch_size,
                show_progress=False
            )
            
            # Prepare documents for indexing (one per chunk)
            es_documents = []
            for chunk, embedding in zip(text_chunks, embeddings):
                es_doc = {
                    'doc_id': doc['doc_id'],
                    'title': doc['title'],
                    'source': doc['source'],
                    'date': doc.get('date'),
                    'section': doc.get('section', 'Document'),
                    'chunk_id': chunk['chunk_id'],
                    'text_chunk': chunk['text'],
                    'page': chunk.get('page'),
                    'embedding': embedding,
                    'full_text': doc.get('full_text', ''),
                    'filename': doc['filename'],
                    'filepath': doc['filepath'],
                    'is_scanned': doc.get('is_scanned', False),
                    'num_pages': doc.get('num_pages', 0)
                }
                es_documents.append(es_doc)
            
            # Bulk index chunks for this document
            if es_setup.bulk_index(index_name, es_documents):
                indexed_count += len(es_documents)
            else:
                failed_count += len(es_documents)
                
        except Exception as e:
            logger.error(f"Failed to index document {doc.get('title', 'Unknown')}: {e}", exc_info=True)
            failed_count += len(doc.get('text_chunks', []))
    
    logger.info("="*80)
    logger.info("INDEXING SUMMARY")
    logger.info("="*80)
    logger.info(f"Total documents: {len(documents)}")
    logger.info(f"Chunks indexed: {indexed_count}")
    logger.info(f"Chunks failed: {failed_count}")
    logger.info(f"Index name: {index_name}")
    logger.info("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process PDFs and index them into Elasticsearch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index already processed documents
  python src/process_and_index.py --processed-dir data/processed
  
  # Process PDFs first, then index
  python src/process_and_index.py --download-dir downloads --processed-dir data/processed
        """
    )
    
    parser.add_argument(
        '--processed-dir',
        type=str,
        default='data/processed',
        help='Directory containing processed JSON files (default: data/processed)'
    )
    
    parser.add_argument(
        '--download-dir',
        type=str,
        default=None,
        help='Directory containing PDFs to process first (optional)'
    )
    
    parser.add_argument(
        '--index-name',
        type=str,
        default='government_documents',
        help='Elasticsearch index name (default: government_documents)'
    )
    
    parser.add_argument(
        '--embedding-model',
        type=str,
        default='all-MiniLM-L6-v2',
        help='Sentence transformer model name (default: all-MiniLM-L6-v2)'
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
        default='elastic',
        help='Elasticsearch username (default: elastic)'
    )
    
    parser.add_argument(
        '--es-password',
        type=str,
        default=None,
        help='Elasticsearch password (required if authentication enabled)'
    )
    
    parser.add_argument(
        '--delete-existing',
        action='store_true',
        help='Delete existing index if it exists'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for embedding generation (default: 32)'
    )
    
    args = parser.parse_args()
    
    # Process PDFs first if download-dir is provided
    if args.download_dir:
        logger.info("Processing PDFs first...")
        from process_documents import process_all_pdfs
        process_all_pdfs(
            download_dir=args.download_dir,
            output_dir=args.processed_dir,
            skip_existing=True
        )
    
    # Load processed documents
    documents = load_processed_documents(args.processed_dir)
    
    if not documents:
        logger.error("No processed documents found. Process PDFs first or provide --download-dir.")
        sys.exit(1)
    
    # Initialize embedding service
    logger.info(f"Initializing embedding service with model: {args.embedding_model}")
    embedding_service = EmbeddingService(model_name=args.embedding_model)
    embedding_dim = embedding_service.get_embedding_dimension()
    
    # Initialize Elasticsearch
    logger.info(f"Connecting to Elasticsearch at {args.es_host}:{args.es_port}")
    es_setup = ElasticsearchSetup(
        host=args.es_host,
        port=args.es_port,
        username=args.es_username,
        password=args.es_password
    )
    
    # Create index
    logger.info(f"Creating/checking index: {args.index_name}")
    es_setup.create_index(
        index_name=args.index_name,
        embedding_dim=embedding_dim,
        delete_existing=args.delete_existing
    )
    
    # Index documents
    index_documents(
        documents=documents,
        embedding_service=embedding_service,
        es_setup=es_setup,
        index_name=args.index_name,
        batch_size=args.batch_size
    )
    
    logger.info("Indexing completed successfully!")


if __name__ == "__main__":
    main()


