"""
Search service for semantic document search.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

from .es_setup import ElasticsearchSetup
try:
    from ..embeddings.embedding_service import EmbeddingService
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from embeddings.embedding_service import EmbeddingService


class SearchService:
    """Service for semantic document search."""
    
    def __init__(self, 
                 es_setup: ElasticsearchSetup,
                 embedding_service: EmbeddingService,
                 index_name: str = "government_documents"):
        """
        Initialize search service.
        
        Args:
            es_setup: ElasticsearchSetup instance
            embedding_service: EmbeddingService instance
            index_name: Name of the Elasticsearch index
        """
        self.es_setup = es_setup
        self.embedding_service = embedding_service
        self.index_name = index_name
    
    def search(self, query: str, 
               size: int = 10,
               source: Optional[str] = None,
               section: Optional[str] = None) -> List[Dict]:
        """
        Search for documents using semantic similarity.
        
        Args:
            query: Search query text
            size: Number of results to return
            source: Filter by source (rbi, income_tax, caqm)
            section: Filter by section (Notifications, Circulars, etc.)
            
        Returns:
            List of search results with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Build filters
        filters = {}
        if source:
            filters["source"] = source
        if section:
            filters["section"] = section
        
        # Perform search
        results = self.es_setup.search(
            index_name=self.index_name,
            query_embedding=query_embedding,
            size=size,
            filters=filters if filters else None
        )
        
        return results
    
    def keyword_search(self, query: str,
                      size: int = 10,
                      source: Optional[str] = None,
                      section: Optional[str] = None) -> List[Dict]:
        """
        Search for documents using keyword matching (BM25).
        
        Args:
            query: Search query text
            size: Number of results to return
            source: Filter by source (rbi, income_tax, caqm)
            section: Filter by section (Notifications, Circulars, etc.)
            
        Returns:
            List of search results with scores
        """
        # Build filters
        filters = {}
        if source:
            filters["source"] = source
        if section:
            filters["section"] = section
        
        # Perform keyword search
        results = self.es_setup.keyword_search(
            index_name=self.index_name,
            query_text=query,
            size=size,
            filters=filters if filters else None
        )
        
        return results
    
    def get_index_name(self) -> str:
        """Get the index name."""
        return self.index_name

