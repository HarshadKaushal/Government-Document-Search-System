"""
Document summarization using extractive methods.
Uses sentence embeddings to find the most representative sentences.
"""

import re
import logging
from typing import List, Dict, Optional
from collections import Counter

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Summarization will be limited.")


class DocumentSummarizer:
    """Extractive document summarization using sentence embeddings."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize summarizer.
        
        Args:
            model_name: Sentence transformer model name (default: all-MiniLM-L6-v2)
        """
        self.model_name = model_name
        self.model = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading summarization model: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info("Summarization model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load model {model_name}: {e}")
                self.model = None
        else:
            logger.warning("Sentence transformers not available. Using fallback summarization.")
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not text:
            return []
        
        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]+\s+', text)
        # Filter out very short sentences (likely artifacts)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return sentences
    
    def summarize_extractive(self, 
                            text: str, 
                            num_sentences: int = 3,
                            query: Optional[str] = None) -> str:
        """
        Generate extractive summary by selecting most representative sentences.
        
        Args:
            text: Full text to summarize
            num_sentences: Number of sentences to include in summary
            query: Optional query to bias summary towards query-relevant content
            
        Returns:
            Summary text
        """
        if not text or len(text.strip()) < 50:
            return text[:200] if text else "No text available for summarization."
        
        # Split into sentences
        sentences = self.split_into_sentences(text)
        
        if len(sentences) <= num_sentences:
            # Document is already short enough
            return ' '.join(sentences)
        
        if not self.model:
            # Fallback: return first N sentences
            return ' '.join(sentences[:num_sentences])
        
        try:
            # Generate embeddings for all sentences
            sentence_embeddings = self.model.encode(sentences, show_progress_bar=False)
            
            if query and NUMPY_AVAILABLE:
                # If query provided, bias towards query-relevant sentences
                query_embedding = self.model.encode([query], show_progress_bar=False)[0]
                
                # Calculate similarity to query using cosine similarity
                similarities = []
                query_norm = np.linalg.norm(query_embedding)
                for sent_emb in sentence_embeddings:
                    sent_norm = np.linalg.norm(sent_emb)
                    if sent_norm > 0 and query_norm > 0:
                        similarity = np.dot(sent_emb, query_embedding) / (sent_norm * query_norm)
                        similarities.append(similarity)
                    else:
                        similarities.append(0.0)
                
                # Select top sentences by query relevance
                sentence_scores = list(enumerate(similarities))
                sentence_scores.sort(key=lambda x: x[1], reverse=True)
                selected_indices = [idx for idx, _ in sentence_scores[:num_sentences]]
                selected_indices.sort()  # Maintain original order
                
            else:
                # Select diverse, representative sentences
                # Simple approach: use centroid of all sentences, pick closest to centroid
                if NUMPY_AVAILABLE:
                    centroid = np.mean(sentence_embeddings, axis=0)
                    distances = [
                        np.linalg.norm(emb - centroid) for emb in sentence_embeddings
                    ]
                else:
                    # Fallback: just pick first N sentences
                    distances = list(range(len(sentence_embeddings)))
                
                # Pick sentences closest to centroid (most representative)
                sentence_scores = list(enumerate(distances))
                sentence_scores.sort(key=lambda x: x[1])  # Sort by distance (ascending)
                selected_indices = [idx for idx, _ in sentence_scores[:num_sentences]]
                selected_indices.sort()  # Maintain original order
            
            # Build summary from selected sentences
            summary_sentences = [sentences[i] for i in selected_indices]
            summary = ' '.join(summary_sentences)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback: return first N sentences
            return ' '.join(sentences[:num_sentences])
    
    def summarize_document(self, 
                          document: Dict,
                          num_sentences: int = 3,
                          query: Optional[str] = None) -> str:
        """
        Summarize a document from search results.
        
        Args:
            document: Document dictionary with 'full_text' or 'text_chunk'
            num_sentences: Number of sentences in summary
            query: Optional query to guide summarization
            
        Returns:
            Summary text
        """
        # Use full_text if available, otherwise use text_chunk
        text = document.get('full_text', '') or document.get('text_chunk', '')
        
        if not text:
            return "No text available for summarization."
        
        # Limit text length for summarization (process max 5000 chars for speed)
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        return self.summarize_extractive(text, num_sentences, query)
    
    def summarize_search_results(self,
                                results: List[Dict],
                                num_sentences_per_doc: int = 2,
                                query: Optional[str] = None) -> List[Dict]:
        """
        Add summaries to search results.
        
        Args:
            results: List of search result dictionaries
            num_sentences_per_doc: Sentences per summary
            query: Search query to guide summarization
            
        Returns:
            Results with added 'summary' field
        """
        for result in results:
            if 'summary' not in result:
                result['summary'] = self.summarize_document(
                    result,
                    num_sentences=num_sentences_per_doc,
                    query=query
                )
        
        return results

