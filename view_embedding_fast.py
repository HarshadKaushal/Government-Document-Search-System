#!/usr/bin/env python3
"""Fastest way to view embedding - uses search service that we know works!"""

import sys, os
sys.path.insert(0, 'src')

from search.search_service import SearchService
from search.es_setup import ElasticsearchSetup
from embeddings.embedding_service import EmbeddingService

# Connect
es = ElasticsearchSetup()
emb_service = EmbeddingService()
search_service = SearchService(es, emb_service)

# Get first document - do a search to get actual indexed document
results = search_service.search("income tax", size=1)

if results:
    result = results[0]
    embedding = result.get('embedding', [])
    
    print("\n" + "="*60)
    print("VECTOR EMBEDDING")
    print("="*60)
    print(f"Document ID: {result.get('doc_id', 'N/A')}")
    print(f"Title: {result.get('title', 'N/A')}")
    print(f"Chunk ID: {result.get('chunk_id', 'N/A')}")
    print(f"Embedding Dimension: {len(embedding)}")
    print(f"\nFirst 20 values:")
    print(embedding[:20])
    print(f"\nLast 10 values:")
    print(embedding[-10:])
    print(f"\nFull Vector (384 dimensions):")
    print(embedding)
else:
    print("No documents found!")

