"""
Metrics calculation for search evaluation.
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


def calculate_precision_at_k(results: List[Dict], 
                             relevant_doc_ids: Set[str], 
                             k: int) -> float:
    """
    Calculate Precision@K.
    
    Args:
        results: List of search results with 'doc_id' field
        relevant_doc_ids: Set of relevant document IDs
        k: Number of top results to consider
        
    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if not results or k == 0:
        return 0.0
    
    top_k = results[:k]
    relevant_retrieved = sum(1 for r in top_k if r.get('doc_id') in relevant_doc_ids)
    
    return relevant_retrieved / len(top_k)


def calculate_recall_at_k(results: List[Dict], 
                          relevant_doc_ids: Set[str], 
                          k: int, 
                          total_relevant: int) -> float:
    """
    Calculate Recall@K.
    
    Args:
        results: List of search results with 'doc_id' field
        relevant_doc_ids: Set of relevant document IDs
        k: Number of top results to consider
        total_relevant: Total number of relevant documents
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if total_relevant == 0:
        return 0.0
    
    if not results:
        return 0.0
    
    top_k = results[:k]
    relevant_retrieved = sum(1 for r in top_k if r.get('doc_id') in relevant_doc_ids)
    
    return relevant_retrieved / total_relevant


def calculate_mrr(results: List[Dict], relevant_doc_ids: Set[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).
    
    Args:
        results: List of search results with 'doc_id' field
        relevant_doc_ids: Set of relevant document IDs
        
    Returns:
        MRR score (0.0 to 1.0)
    """
    if not results:
        return 0.0
    
    for i, result in enumerate(results, 1):
        if result.get('doc_id') in relevant_doc_ids:
            return 1.0 / i
    
    return 0.0


def calculate_f1_score(results: List[Dict], 
                      relevant_doc_ids: Set[str], 
                      k: int, 
                      total_relevant: int) -> float:
    """
    Calculate F1 Score at K.
    
    Args:
        results: List of search results with 'doc_id' field
        relevant_doc_ids: Set of relevant document IDs
        k: Number of top results to consider
        total_relevant: Total number of relevant documents
        
    Returns:
        F1 Score (0.0 to 1.0)
    """
    precision = calculate_precision_at_k(results, relevant_doc_ids, k)
    recall = calculate_recall_at_k(results, relevant_doc_ids, k, total_relevant)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)


def calculate_map(results: List[Dict], relevant_doc_ids: Set[str], k: Optional[int] = None) -> float:
    """
    Calculate Mean Average Precision (MAP).
    
    Args:
        results: List of search results with 'doc_id' field
        relevant_doc_ids: Set of relevant document IDs
        k: Optional limit on number of results to consider
        
    Returns:
        MAP score (0.0 to 1.0)
    """
    if not results:
        return 0.0
    
    if k is not None:
        results = results[:k]
    
    if not relevant_doc_ids:
        return 0.0
    
    relevant_found = 0
    precision_sum = 0.0
    
    for i, result in enumerate(results, 1):
        if result.get('doc_id') in relevant_doc_ids:
            relevant_found += 1
            precision_sum += relevant_found / i
    
    if relevant_found == 0:
        return 0.0
    
    return precision_sum / len(relevant_doc_ids)


def calculate_ndcg_at_k(results: List[Dict], 
                        relevant_doc_ids: Set[str], 
                        k: int,
                        score_key: str = 'score') -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K (NDCG@K).
    
    Args:
        results: List of search results with 'doc_id' and score fields
        relevant_doc_ids: Set of relevant document IDs
        k: Number of top results to consider
        score_key: Key to use for relevance scores
        
    Returns:
        NDCG@K score (0.0 to 1.0)
    """
    if not results or k == 0:
        return 0.0
    
    top_k = results[:k]
    
    # Calculate DCG
    dcg = 0.0
    for i, result in enumerate(top_k, 1):
        if result.get('doc_id') in relevant_doc_ids:
            # Relevance is 1 if relevant, 0 otherwise
            relevance = 1.0
            dcg += relevance / np.log2(i + 1)
    
    # Calculate IDCG (ideal DCG - all relevant documents at top)
    num_relevant = len([r for r in top_k if r.get('doc_id') in relevant_doc_ids])
    idcg = sum(1.0 / np.log2(i + 1) for i in range(1, min(num_relevant, k) + 1))
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def evaluate_search_results(results: List[Dict],
                           relevant_doc_ids: Set[str],
                           total_relevant: Optional[int] = None,
                           k_values: List[int] = [5, 10, 20]) -> Dict[str, float]:
    """
    Calculate comprehensive metrics for search results.
    
    Args:
        results: List of search results
        relevant_doc_ids: Set of relevant document IDs
        total_relevant: Total number of relevant documents (if None, uses len(relevant_doc_ids))
        k_values: List of K values for precision/recall calculations
        
    Returns:
        Dictionary of metric names and values
    """
    if total_relevant is None:
        total_relevant = len(relevant_doc_ids)
    
    metrics = {}
    
    # Precision and Recall at different K values
    for k in k_values:
        metrics[f'Precision@{k}'] = calculate_precision_at_k(results, relevant_doc_ids, k)
        metrics[f'Recall@{k}'] = calculate_recall_at_k(results, relevant_doc_ids, k, total_relevant)
        metrics[f'F1@{k}'] = calculate_f1_score(results, relevant_doc_ids, k, total_relevant)
        metrics[f'NDCG@{k}'] = calculate_ndcg_at_k(results, relevant_doc_ids, k)
    
    # MRR
    metrics['MRR'] = calculate_mrr(results, relevant_doc_ids)
    
    # MAP
    metrics['MAP'] = calculate_map(results, relevant_doc_ids)
    
    # Number of relevant documents retrieved
    retrieved_doc_ids = {r.get('doc_id') for r in results}
    metrics['Relevant_Retrieved'] = len(retrieved_doc_ids & relevant_doc_ids)
    metrics['Total_Retrieved'] = len(results)
    metrics['Total_Relevant'] = total_relevant
    
    return metrics


def create_comparison_matrix(semantic_results: List[Dict], 
                             keyword_results: List[Dict], 
                             k: int = 10) -> Dict[str, int]:
    """
    Create comparison matrix between semantic and keyword search.
    
    Args:
        semantic_results: Semantic search results
        keyword_results: Keyword search results
        k: Number of top results to compare
        
    Returns:
        Dictionary with overlap statistics
    """
    semantic_doc_ids = {r.get('doc_id') for r in semantic_results[:k]}
    keyword_doc_ids = {r.get('doc_id') for r in keyword_results[:k]}
    
    both = len(semantic_doc_ids & keyword_doc_ids)
    only_semantic = len(semantic_doc_ids - keyword_doc_ids)
    only_keyword = len(keyword_doc_ids - semantic_doc_ids)
    
    return {
        'both': both,
        'only_semantic': only_semantic,
        'only_keyword': only_keyword,
        'total_semantic': len(semantic_doc_ids),
        'total_keyword': len(keyword_doc_ids)
    }

