"""
Embedding service for generating semantic embeddings from text.
Uses sentence-transformers for fast and efficient embeddings.
"""

import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.error("sentence-transformers not available. Install it for embeddings.")


class EmbeddingService:
    """Service for generating semantic embeddings from text."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model
                       Options:
                       - all-MiniLM-L6-v2 (fast, 384 dim, recommended)
                       - paraphrase-multilingual-MiniLM-L12-v2 (multilingual, 384 dim)
                       - all-mpnet-base-v2 (higher quality, 768 dim, slower)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers is required for embeddings. Install it first.")
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.embedding_dim
        
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32, 
                                   show_progress: bool = False) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts (more efficient).
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts and remember indices
        non_empty_indices = []
        non_empty_texts = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_indices.append(i)
                non_empty_texts.append(text)
        
        if not non_empty_texts:
            # All texts are empty, return zero vectors
            return [[0.0] * self.embedding_dim] * len(texts)
        
        # Generate embeddings for non-empty texts
        embeddings = self.model.encode(
            non_empty_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )
        
        # Map back to original indices
        result = []
        embedding_idx = 0
        
        for i in range(len(texts)):
            if i in non_empty_indices:
                result.append(embeddings[embedding_idx].tolist())
                embedding_idx += 1
            else:
                result.append([0.0] * self.embedding_dim)
        
        return result
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.embedding_dim


