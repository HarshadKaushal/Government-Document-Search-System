#!/usr/bin/env python3
"""Ultra-fast one-liner to view embedding - just run: python quick_embedding.py"""

import sys, os
sys.path.insert(0, 'src')

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from search import ElasticsearchSetup

# Get password from command line or prompt
password = sys.argv[1] if len(sys.argv) > 1 else None
doc_id = sys.argv[2] if len(sys.argv) > 2 else None

es = ElasticsearchSetup(password=password)
es_client = es.get_client()

# Try to get a document ID first if not provided
if not doc_id:
    # Get first document ID
    result = es_client.search(index='government_documents', query={'match_all': {}}, size=1, _source=['doc_id', 'title'])
    if result['hits']['hits']:
        doc_id = result['hits']['hits'][0]['_source'].get('doc_id')
        print(f"Using first document: {doc_id}")
    else:
        print("[ERROR] No documents found in index!")
        sys.exit(1)

# Get document directly by doc_id using term query - get first chunk
result = es_client.search(
    index='government_documents', 
    query={'term': {'doc_id': doc_id}}, 
    size=1,
    source_includes=['doc_id', 'title', 'chunk_id', 'embedding', 'text_chunk']
)

if result['hits']['hits']:
    hit = result['hits']['hits'][0]
    src = hit['_source']
    emb = src.get('embedding', [])
    
    if emb:
        print(f"\nDoc ID: {src.get('doc_id', 'N/A')}")
        print(f"Title: {src.get('title', 'N/A')}")
        print(f"Chunk: {src.get('chunk_id', 'N/A')}")
        print(f"Dimension: {len(emb)}")
        print(f"\nFirst 20 values: {emb[:20]}")
        print(f"\nFull vector (384 dimensions):")
        print(emb)
    else:
        print(f"\n[ERROR] Embedding not found in document!")
        print(f"Available fields: {list(src.keys())}")
else:
    print("[ERROR] No document found!")

