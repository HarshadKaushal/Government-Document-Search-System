#!/usr/bin/env python3
"""
Quick script to view vector embedding of a single document.
Fastest way to check embeddings!
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search import ElasticsearchSetup

def view_embedding(doc_id: str = None, chunk_id: int = None, es_password: str = None):
    """View embedding for a single document/chunk."""
    
    # Connect to Elasticsearch
    es_setup = ElasticsearchSetup(
        host="localhost",
        port=9200,
        username="elastic",
        password=es_password
    )
    es = es_setup.get_client()
    
    # Build query
    if doc_id and chunk_id is not None:
        query = {
            "bool": {
                "must": [
                    {"term": {"doc_id": doc_id}},
                    {"term": {"chunk_id": chunk_id}}
                ]
            }
        }
        print(f"Fetching embedding for document: {doc_id}, chunk: {chunk_id}")
    elif doc_id:
        query = {"term": {"doc_id": doc_id}}
        print(f"Fetching first embedding for document: {doc_id}")
    else:
        query = {"match_all": {}}
        print("Fetching first available embedding...")
    
    # Search
    response = es.search(
        index="government_documents",
        query=query,
        size=1,
        _source=["doc_id", "title", "chunk_id", "text_chunk", "embedding"]
    )
    
    hits = response['hits']['hits']
    
    if not hits:
        print("❌ No documents found!")
        return
    
    hit = hits[0]
    source = hit['_source']
    embedding = source.get('embedding', [])
    
    # Display results
    print("\n" + "=" * 80)
    print(f"📄 Document ID: {source.get('doc_id')}")
    print(f"📝 Title: {source.get('title', 'N/A')}")
    print(f"🔢 Chunk ID: {source.get('chunk_id', 'N/A')}")
    print(f"📊 Embedding Dimension: {len(embedding)}")
    print("\n" + "-" * 80)
    print("🔢 EMBEDDING VECTOR (384 dimensions):")
    print("-" * 80)
    
    # Show first 20 values, then summary
    print(f"\nFirst 20 values: {embedding[:20]}")
    print(f"\nLast 10 values: {embedding[-10:]}")
    print(f"\nVector stats:")
    print(f"  - Min value: {min(embedding):.6f}")
    print(f"  - Max value: {max(embedding):.6f}")
    print(f"  - Mean: {sum(embedding)/len(embedding):.6f}")
    
    # Show full vector in compact format
    print(f"\n{'=' * 80}")
    print("📋 FULL VECTOR (comma-separated):")
    print("-" * 80)
    print(json.dumps(embedding, indent=2)[:500] + "..." if len(json.dumps(embedding)) > 500 else json.dumps(embedding, indent=2))
    
    # Text preview
    text_preview = source.get('text_chunk', '')[:200]
    print(f"\n{'=' * 80}")
    print(f"📄 TEXT CHUNK PREVIEW:")
    print("-" * 80)
    print(text_preview + "..." if len(source.get('text_chunk', '')) > 200 else text_preview)
    print("=" * 80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick view of vector embedding for a document')
    parser.add_argument('--doc-id', type=str, help='Document ID')
    parser.add_argument('--chunk-id', type=int, help='Chunk ID (optional)')
    parser.add_argument('--es-password', type=str, help='Elasticsearch password')
    
    args = parser.parse_args()
    
    view_embedding(
        doc_id=args.doc_id,
        chunk_id=args.chunk_id,
        es_password=args.es_password
    )

