"""
Elasticsearch setup and configuration for document indexing.
"""

import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    logger.error("elasticsearch package not available. Install it for indexing.")


class ElasticsearchSetup:
    """Setup and manage Elasticsearch index for document search."""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 9200,
                 username: str = "elastic",
                 password: Optional[str] = None,
                 use_ssl: bool = False,
                 verify_certs: bool = False):
        """
        Initialize Elasticsearch client.
        
        Args:
            host: Elasticsearch host
            port: Elasticsearch port
            username: Elasticsearch username
            password: Elasticsearch password (if required)
            use_ssl: Whether to use SSL
            verify_certs: Whether to verify SSL certificates
        """
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("elasticsearch package is required. Install it first.")
        
        # Build connection URL
        scheme = "https" if use_ssl else "http"
        url = f"{scheme}://{host}:{port}"
        
        # Build connection parameters for Elasticsearch 8.x
        connection_params = {
            "hosts": [url],
            "request_timeout": 60
        }
        
        # Add authentication if provided
        if username and password:
            connection_params["basic_auth"] = (username, password)
        
        # Add SSL verification settings if using SSL
        if use_ssl:
            connection_params["verify_certs"] = verify_certs
            if not verify_certs:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Create Elasticsearch client
        self.es = Elasticsearch(**connection_params)
        
        # Test connection
        try:
            if self.es.ping():
                logger.info(f"Connected to Elasticsearch at {host}:{port}")
            else:
                raise ConnectionError("Failed to connect to Elasticsearch")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise
    
    def create_index(self, index_name: str, embedding_dim: int = 384, 
                     delete_existing: bool = False) -> bool:
        """
        Create Elasticsearch index with proper mapping for document search.
        
        Args:
            index_name: Name of the index to create
            embedding_dim: Dimension of embedding vectors (default: 384 for all-MiniLM-L6-v2)
            delete_existing: Whether to delete existing index if it exists
            
        Returns:
            True if index was created successfully
        """
        # Delete existing index if requested
        if delete_existing and self.es.indices.exists(index=index_name):
            logger.info(f"Deleting existing index: {index_name}")
            self.es.indices.delete(index=index_name)
        
        # Check if index already exists
        if self.es.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return True
        
        # Define index mapping
        mapping = {
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "source": {"type": "keyword"},
                    "date": {"type": "date"},
                    "section": {"type": "keyword"},
                    "chunk_id": {"type": "integer"},
                    "text_chunk": {"type": "text"},
                    "page": {"type": "integer"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": embedding_dim,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "full_text": {"type": "text"},
                    "filename": {"type": "keyword"},
                    "filepath": {"type": "keyword"},
                    "is_scanned": {"type": "boolean"},
                    "num_pages": {"type": "integer"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            }
        }
        
        # Create index
        try:
            # Elasticsearch 8.x API - mappings and settings are separate parameters
            self.es.indices.create(
                index=index_name,
                mappings=mapping.get('mappings', {}),
                settings=mapping.get('settings', {})
            )
            logger.info(f"Created index: {index_name} with embedding dimension: {embedding_dim}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def index_document(self, index_name: str, document: Dict) -> bool:
        """
        Index a single document chunk into Elasticsearch.
        
        Args:
            index_name: Name of the index
            document: Document dictionary with all required fields
            
        Returns:
            True if indexing was successful
        """
        try:
            self.es.index(index=index_name, document=document)
            return True
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return False
    
    def bulk_index(self, index_name: str, documents: list) -> bool:
        """
        Bulk index multiple documents (more efficient).
        
        Args:
            index_name: Name of the index
            documents: List of document dictionaries
            
        Returns:
            True if bulk indexing was successful
        """
        if not documents:
            return True
        
        try:
            from elasticsearch.helpers import bulk
            
            actions = [
                {
                    "_index": index_name,
                    "_source": doc
                }
                for doc in documents
            ]
            
            success, failed = bulk(self.es, actions, raise_on_error=False)
            
            if failed:
                logger.warning(f"Failed to index {len(failed)} documents out of {len(documents)}")
            
            logger.info(f"Bulk indexed {success} documents to {index_name}")
            return len(failed) == 0
            
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return False
    
    def search(self, index_name: str, query_embedding: List[float], 
               size: int = 10, filters: Optional[Dict] = None) -> list:
        """
        Perform semantic search using dense vector search (knn query for Elasticsearch 8.x).
        
        Args:
            index_name: Name of the index
            query_embedding: Query embedding vector
            size: Number of results to return
            filters: Optional filters (e.g., {"source": "rbi"})
            
        Returns:
            List of search results
        """
        try:
            # Build knn query for Elasticsearch 8.x (using indexed dense vectors)
            # Note: similarity is defined in mapping, not in query
            knn = {
                "field": "embedding",
                "query_vector": query_embedding,
                "k": size,
                "num_candidates": min(size * 10, 100)  # Consider more candidates for better results
            }
            
            # Build filter if provided
            filter_clauses = []
            if filters:
                if "source" in filters:
                    filter_clauses.append({"term": {"source": filters["source"]}})
                
                if "section" in filters:
                    filter_clauses.append({"term": {"section": filters["section"]}})
            
            # If filters exist, add them to knn query
            if filter_clauses:
                knn["filter"] = filter_clauses if len(filter_clauses) == 1 else {"bool": {"must": filter_clauses}}
            
            # Perform knn search
            response = self.es.search(
                index=index_name,
                knn=knn,
                size=size
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['score'] = hit['_score']
                results.append(result)
            
            return results
            
        except Exception as e:
            # Fallback: use match_all query (just return documents)
            logger.warning(f"KNN search failed: {e}. Using simple match_all as fallback.")
            try:
                query = {"match_all": {}}
                
                # Add filters if provided
                if filters:
                    bool_query = {
                        "must": [query],
                        "filter": []
                    }
                    
                    if "source" in filters:
                        bool_query["filter"].append({"term": {"source": filters["source"]}})
                    
                    if "section" in filters:
                        bool_query["filter"].append({"term": {"section": filters["section"]}})
                    
                    query = {"bool": bool_query}
                
                response = self.es.search(index=index_name, query=query, size=size)
                
                results = []
                for hit in response['hits']['hits']:
                    result = hit['_source']
                    result['score'] = hit['_score'] if '_score' in hit else 1.0
                    results.append(result)
                
                logger.warning("Using fallback query - semantic similarity not available. Consider checking Elasticsearch configuration.")
                return results
                
            except Exception as e2:
                logger.error(f"All search methods failed: {e2}")
                import traceback
                traceback.print_exc()
                return []
    
    def keyword_search(self, index_name: str, query_text: str,
                      size: int = 10, filters: Optional[Dict] = None) -> list:
        """
        Perform basic keyword search using BM25 algorithm.
        
        Args:
            index_name: Name of the index
            query_text: Search query text
            size: Number of results to return
            filters: Optional filters (e.g., {"source": "rbi"})
            
        Returns:
            List of search results
        """
        # Build keyword search query
        query = {
            "bool": {
                "should": [
                    {"match": {"text_chunk": {"query": query_text, "boost": 2.0}}},
                    {"match": {"title": {"query": query_text, "boost": 1.5}}},
                    {"match": {"full_text": {"query": query_text}}}
                ],
                "minimum_should_match": 1
            }
        }
        
        # Add filters if provided
        if filters:
            query["bool"]["filter"] = []
            
            if "source" in filters:
                query["bool"]["filter"].append({"term": {"source": filters["source"]}})
            
            if "section" in filters:
                query["bool"]["filter"].append({"term": {"section": filters["section"]}})
        
        try:
            response = self.es.search(index=index_name, query=query, size=size)
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['score'] = hit['_score']
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_client(self):
        """Get the underlying Elasticsearch client."""
        return self.es

