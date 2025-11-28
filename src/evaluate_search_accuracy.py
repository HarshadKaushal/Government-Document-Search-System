#!/usr/bin/env python3
"""
Main script to evaluate search accuracy with metrics and visualizations.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search.es_setup import ElasticsearchSetup
from search.search_service import SearchService
from embeddings.embedding_service import EmbeddingService
from evaluation.metrics import (
    evaluate_search_results,
    create_comparison_matrix
)
from evaluation.visualizations import create_evaluation_report

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_queries(query_file: str) -> List[Dict]:
    """Load test queries from JSON file."""
    if not os.path.exists(query_file):
        logger.warning(f"Test query file not found: {query_file}")
        return []
    
    with open(query_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('test_queries', [])


def evaluate_all_queries(queries: List[Dict],
                        search_service: SearchService,
                        k_values: List[int] = [5, 10, 20]) -> Dict:
    """
    Evaluate all test queries and calculate metrics.
    
    Args:
        queries: List of test queries with 'query' and 'relevant_doc_ids'
        search_service: SearchService instance
        k_values: List of K values for evaluation
        
    Returns:
        Dictionary with all evaluation results
    """
    all_semantic_metrics = []
    all_keyword_metrics = []
    all_semantic_results = []
    all_keyword_results = []
    comparison_matrices = []
    
    results_by_source = defaultdict(lambda: {'semantic': [], 'keyword': []})
    
    logger.info(f"Evaluating {len(queries)} test queries...")
    
    for i, test_query in enumerate(queries, 1):
        query = test_query.get('query', '')
        relevant_doc_ids = set(test_query.get('relevant_doc_ids', []))
        
        if not query:
            logger.warning(f"Query {i} is empty, skipping")
            continue
        
        if not relevant_doc_ids:
            logger.warning(f"Query '{query}' has no relevant documents specified. Skipping evaluation.")
            logger.info("Tip: Manually evaluate search results and add 'relevant_doc_ids' to test_queries.json")
            continue
        
        logger.info(f"\n[{i}/{len(queries)}] Evaluating query: '{query}'")
        logger.info(f"  Relevant documents: {len(relevant_doc_ids)}")
        
        # Perform semantic search
        try:
            semantic_results = search_service.search(query, size=max(k_values) * 2)
            semantic_metrics = evaluate_search_results(
                semantic_results,
                relevant_doc_ids,
                k_values=k_values
            )
            all_semantic_metrics.append(semantic_metrics)
            all_semantic_results.extend(semantic_results[:20])
            
            # Track by source
            for result in semantic_results:
                source = result.get('source', 'unknown')
                results_by_source[source]['semantic'].append(result)
            
            logger.info(f"  Semantic - Precision@10: {semantic_metrics.get('Precision@10', 0):.3f}, "
                       f"Recall@10: {semantic_metrics.get('Recall@10', 0):.3f}")
        
        except Exception as e:
            logger.error(f"Error in semantic search for query '{query}': {e}")
            continue
        
        # Perform keyword search
        try:
            keyword_results = search_service.keyword_search(query, size=max(k_values) * 2)
            keyword_metrics = evaluate_search_results(
                keyword_results,
                relevant_doc_ids,
                k_values=k_values
            )
            all_keyword_metrics.append(keyword_metrics)
            all_keyword_results.extend(keyword_results[:20])
            
            # Track by source
            for result in keyword_results:
                source = result.get('source', 'unknown')
                results_by_source[source]['keyword'].append(result)
            
            logger.info(f"  Keyword - Precision@10: {keyword_metrics.get('Precision@10', 0):.3f}, "
                       f"Recall@10: {keyword_metrics.get('Recall@10', 0):.3f}")
        
        except Exception as e:
            logger.error(f"Error in keyword search for query '{query}': {e}")
            continue
        
        # Create comparison matrix
        comparison = create_comparison_matrix(semantic_results, keyword_results, k=10)
        comparison_matrices.append(comparison)
    
    # Calculate average metrics
    if all_semantic_metrics:
        avg_semantic_metrics = {}
        for metric_name in all_semantic_metrics[0].keys():
            values = [m.get(metric_name, 0) for m in all_semantic_metrics if metric_name in m]
            if values:
                avg_semantic_metrics[metric_name] = sum(values) / len(values)
    else:
        avg_semantic_metrics = {}
    
    if all_keyword_metrics:
        avg_keyword_metrics = {}
        for metric_name in all_keyword_metrics[0].keys():
            values = [m.get(metric_name, 0) for m in all_keyword_metrics if metric_name in m]
            if values:
                avg_keyword_metrics[metric_name] = sum(values) / len(values)
    else:
        avg_keyword_metrics = {}
    
    # Aggregate comparison matrix
    aggregated_comparison = {
        'both': sum(c.get('both', 0) for c in comparison_matrices),
        'only_semantic': sum(c.get('only_semantic', 0) for c in comparison_matrices),
        'only_keyword': sum(c.get('only_keyword', 0) for c in comparison_matrices),
        'total_semantic': sum(c.get('total_semantic', 0) for c in comparison_matrices),
        'total_keyword': sum(c.get('total_keyword', 0) for c in comparison_matrices)
    }
    
    # Calculate metrics by source
    by_source_metrics = {}
    for source, results in results_by_source.items():
        if not results['semantic'] and not results['keyword']:
            continue
        
        # Note: This is simplified - you'd need relevant doc IDs per source for accurate metrics
        by_source_metrics[source] = {
            'semantic_count': len(results['semantic']),
            'keyword_count': len(results['keyword'])
        }
    
    return {
        'semantic_metrics': avg_semantic_metrics,
        'keyword_metrics': avg_keyword_metrics,
        'comparison_matrix': aggregated_comparison,
        'semantic_results': all_semantic_results[:50],  # Limit for visualization
        'keyword_results': all_keyword_results[:50],
        'by_source_metrics': by_source_metrics,
        'num_queries_evaluated': len([q for q in queries if q.get('relevant_doc_ids')])
    }


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description='Evaluate search accuracy with metrics and visualizations')
    parser.add_argument('--query-file', type=str, 
                       default='src/evaluation/test_queries.json',
                       help='Path to test queries JSON file')
    parser.add_argument('--output-dir', type=str,
                       default='evaluation_results',
                       help='Directory to save evaluation results')
    parser.add_argument('--es-host', type=str, default='localhost',
                       help='Elasticsearch host')
    parser.add_argument('--es-port', type=int, default=9200,
                       help='Elasticsearch port')
    parser.add_argument('--es-username', type=str, default='elastic',
                       help='Elasticsearch username')
    parser.add_argument('--es-password', type=str, default=None,
                       help='Elasticsearch password')
    parser.add_argument('--index-name', type=str, default='government_documents',
                       help='Elasticsearch index name')
    parser.add_argument('--no-show', action='store_true',
                       help='Don\'t display plots (save only)')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("SEARCH ACCURACY EVALUATION")
    logger.info("=" * 80)
    
    # Load test queries
    logger.info(f"Loading test queries from: {args.query_file}")
    test_queries = load_test_queries(args.query_file)
    
    if not test_queries:
        logger.error("No test queries found. Exiting.")
        logger.info("Create a test_queries.json file with queries and relevant document IDs.")
        return
    
    logger.info(f"Loaded {len(test_queries)} test queries")
    
    # Check how many have relevant doc IDs
    queries_with_relevance = [q for q in test_queries if q.get('relevant_doc_ids')]
    logger.info(f"Queries with relevance judgments: {len(queries_with_relevance)}")
    
    if not queries_with_relevance:
        logger.warning("\n⚠️  No queries have 'relevant_doc_ids' specified!")
        logger.warning("To evaluate accuracy:")
        logger.warning("1. Run search for each query")
        logger.warning("2. Manually identify relevant documents")
        logger.warning("3. Add 'relevant_doc_ids' array to test_queries.json")
        logger.warning("\nFor now, running evaluation will skip queries without relevance judgments.")
    
    # Initialize services
    logger.info("\nInitializing search services...")
    try:
        es_setup = ElasticsearchSetup(
            host=args.es_host,
            port=args.es_port,
            username=args.es_username,
            password=args.es_password
        )
        
        embedding_service = EmbeddingService()
        search_service = SearchService(
            es_setup=es_setup,
            embedding_service=embedding_service,
            index_name=args.index_name
        )
        
        logger.info("✓ Services initialized successfully")
    
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error("Make sure Elasticsearch is running and accessible")
        return
    
    # Run evaluation
    logger.info("\n" + "=" * 80)
    logger.info("RUNNING EVALUATION")
    logger.info("=" * 80)
    
    evaluation_results = evaluate_all_queries(test_queries, search_service)
    
    if evaluation_results.get('num_queries_evaluated', 0) == 0:
        logger.warning("\n⚠️  No queries were evaluated!")
        logger.warning("Add 'relevant_doc_ids' to your test queries to enable evaluation.")
        return
    
    # Generate report and visualizations
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING REPORT AND VISUALIZATIONS")
    logger.info("=" * 80)
    
    report_path = create_evaluation_report(
        evaluation_results,
        output_dir=args.output_dir,
        show_plots=not args.no_show
    )
    
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\nResults saved to: {args.output_dir}")
    logger.info(f"Report: {report_path}")
    logger.info("\nVisualizations generated:")
    logger.info(f"  - Confusion matrix: {args.output_dir}/confusion_matrix.png")
    logger.info(f"  - Metrics comparison: {args.output_dir}/metrics_comparison.png")
    logger.info(f"  - Precision-Recall curve: {args.output_dir}/precision_recall_curve.png")
    logger.info(f"  - Score distribution: {args.output_dir}/score_distribution.png")
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    
    if evaluation_results.get('semantic_metrics'):
        logger.info("\nAverage Semantic Search Metrics:")
        for metric, value in sorted(evaluation_results['semantic_metrics'].items()):
            if isinstance(value, float):
                logger.info(f"  {metric:20s}: {value:.4f}")
    
    if evaluation_results.get('keyword_metrics'):
        logger.info("\nAverage Keyword Search Metrics:")
        for metric, value in sorted(evaluation_results['keyword_metrics'].items()):
            if isinstance(value, float):
                logger.info(f"  {metric:20s}: {value:.4f}")


if __name__ == '__main__':
    main()

