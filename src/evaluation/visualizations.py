"""
Visualization functions for search evaluation.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Set style
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
sns.set_palette("husl")


def plot_confusion_matrix(comparison_data: Dict[str, int], 
                         save_path: Optional[str] = None,
                         show: bool = True) -> None:
    """
    Plot confusion matrix comparing semantic and keyword search agreement.
    
    Args:
        comparison_data: Dictionary with 'both', 'only_semantic', 'only_keyword' keys
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    # Create matrix
    matrix = np.array([
        [comparison_data.get('both', 0), comparison_data.get('only_keyword', 0)],
        [comparison_data.get('only_semantic', 0), 0]  # Neither found is not meaningful here
    ])
    
    plt.figure(figsize=(10, 8))
    
    # Create heatmap
    sns.heatmap(matrix, 
                annot=True, 
                fmt='d', 
                cmap='Blues',
                cbar_kws={'label': 'Number of Documents'},
                xticklabels=['In Keyword Results', 'Not in Keyword Results'],
                yticklabels=['In Semantic Results', 'Not in Semantic Results'],
                linewidths=2,
                linecolor='gray')
    
    plt.title('Search Method Agreement Matrix\n(Comparing Top Results)', 
              fontsize=14, fontweight='bold', pad=20)
    plt.ylabel('Semantic Search', fontsize=12, fontweight='bold')
    plt.xlabel('Keyword Search', fontsize=12, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Confusion matrix saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_metrics_comparison(metrics_semantic: Dict[str, float], 
                           metrics_keyword: Dict[str, float],
                           save_path: Optional[str] = None,
                           show: bool = True) -> None:
    """
    Compare metrics between semantic and keyword search.
    
    Args:
        metrics_semantic: Dictionary of metrics for semantic search
        metrics_keyword: Dictionary of metrics for keyword search
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    # Select metrics to compare
    metric_keys = ['Precision@5', 'Precision@10', 'Recall@10', 'MRR', 'MAP']
    available_metrics = [m for m in metric_keys if m in metrics_semantic and m in metrics_keyword]
    
    if not available_metrics:
        logger.warning("No matching metrics found for comparison")
        return
    
    semantic_values = [metrics_semantic.get(m, 0) for m in available_metrics]
    keyword_values = [metrics_keyword.get(m, 0) for m in available_metrics]
    
    x = np.arange(len(available_metrics))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 7))
    bars1 = ax.bar(x - width/2, semantic_values, width, label='Semantic Search', 
                   color='#667eea', alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, keyword_values, width, label='Keyword Search', 
                   color='#f093fb', alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Search Method Accuracy Comparison', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(available_metrics, rotation=45, ha='right')
    ax.legend(fontsize=11, loc='upper left')
    ax.set_ylim([0, 1.1])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{height:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Metrics comparison saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_score_distribution(semantic_results: List[Dict],
                           keyword_results: List[Dict],
                           save_path: Optional[str] = None,
                           show: bool = True) -> None:
    """
    Plot score distribution comparison between semantic and keyword search.
    
    Args:
        semantic_results: Semantic search results with 'score' field
        keyword_results: Keyword search results with 'score' field
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    semantic_scores = [r.get('score', 0) for r in semantic_results[:20]]
    keyword_scores = [r.get('score', 0) for r in keyword_results[:20]]
    
    # Normalize keyword scores for comparison (they're typically much higher)
    if keyword_scores and max(keyword_scores) > 1:
        keyword_scores = [s / max(keyword_scores) for s in keyword_scores]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Score distribution
    ax1.hist(semantic_scores, bins=15, alpha=0.7, label='Semantic', color='#667eea', edgecolor='black')
    ax1.hist(keyword_scores, bins=15, alpha=0.7, label='Keyword', color='#f093fb', edgecolor='black')
    ax1.set_xlabel('Score (Normalized)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax1.set_title('Score Distribution Comparison', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Box plot
    data_to_plot = [semantic_scores, keyword_scores]
    bp = ax2.boxplot(data_to_plot, labels=['Semantic', 'Keyword'], 
                     patch_artist=True, showmeans=True)
    bp['boxes'][0].set_facecolor('#667eea')
    bp['boxes'][1].set_facecolor('#f093fb')
    ax2.set_ylabel('Score (Normalized)', fontsize=11, fontweight='bold')
    ax2.set_title('Score Statistics Comparison', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Score distribution saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_precision_recall_curve(metrics_semantic: Dict[str, float],
                                metrics_keyword: Dict[str, float],
                                k_values: List[int] = [1, 5, 10, 20, 50],
                                save_path: Optional[str] = None,
                                show: bool = True) -> None:
    """
    Plot precision-recall curve at different K values.
    
    Args:
        metrics_semantic: Dictionary of metrics for semantic search
        metrics_keyword: Dictionary of metrics for keyword search
        k_values: List of K values
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    semantic_precisions = [metrics_semantic.get(f'Precision@{k}', 0) for k in k_values]
    semantic_recalls = [metrics_semantic.get(f'Recall@{k}', 0) for k in k_values]
    keyword_precisions = [metrics_keyword.get(f'Precision@{k}', 0) for k in k_values]
    keyword_recalls = [metrics_keyword.get(f'Recall@{k}', 0) for k in k_values]
    
    plt.figure(figsize=(10, 7))
    
    plt.plot(semantic_recalls, semantic_precisions, 
             marker='o', linewidth=2, markersize=8, label='Semantic Search', color='#667eea')
    plt.plot(keyword_recalls, keyword_precisions, 
             marker='s', linewidth=2, markersize=8, label='Keyword Search', color='#f093fb')
    
    # Annotate K values
    for i, k in enumerate(k_values):
        plt.annotate(f'K={k}', 
                    (semantic_recalls[i], semantic_precisions[i]),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
        plt.annotate(f'K={k}', 
                    (keyword_recalls[i], keyword_precisions[i]),
                    textcoords="offset points", xytext=(0,-15), ha='center', fontsize=8)
    
    plt.xlabel('Recall', fontsize=12, fontweight='bold')
    plt.ylabel('Precision', fontsize=12, fontweight='bold')
    plt.title('Precision-Recall Curve at Different K Values', fontsize=14, fontweight='bold', pad=20)
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3, linestyle='--')
    plt.xlim([0, 1.05])
    plt.ylim([0, 1.05])
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Precision-Recall curve saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_accuracy_by_source(results_by_source: Dict[str, Dict[str, float]],
                           save_path: Optional[str] = None,
                           show: bool = True) -> None:
    """
    Plot accuracy metrics by source (RBI, Income Tax, CAQM).
    
    Args:
        results_by_source: Dictionary mapping source to metrics dictionary
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    if not results_by_source:
        logger.warning("No data provided for source-based analysis")
        return
    
    sources = list(results_by_source.keys())
    metrics = ['Precision@10', 'Recall@10', 'MRR']
    
    semantic_data = {}
    keyword_data = {}
    
    for metric in metrics:
        semantic_data[metric] = [results_by_source.get(s, {}).get(f'semantic_{metric}', 0) for s in sources]
        keyword_data[metric] = [results_by_source.get(s, {}).get(f'keyword_{metric}', 0) for s in sources]
    
    x = np.arange(len(sources))
    width = 0.12
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for i, metric in enumerate(metrics):
        offset = width * (i - 1)
        ax.bar(x + offset, semantic_data[metric], width, 
               label=f'{metric} (Semantic)', alpha=0.8)
        ax.bar(x + offset + width * len(metrics), keyword_data[metric], width,
               label=f'{metric} (Keyword)', alpha=0.8)
    
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Search Accuracy by Source', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(sources)
    ax.legend(loc='upper right', fontsize=9)
    ax.set_ylim([0, 1.1])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Accuracy by source saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def create_evaluation_report(all_metrics: Dict,
                            output_dir: str = 'evaluation_results',
                            show_plots: bool = True) -> str:
    """
    Create comprehensive evaluation report with all visualizations.
    
    Args:
        all_metrics: Dictionary containing all evaluation metrics and data
        output_dir: Directory to save report and plots
        show: Whether to display plots
        
    Returns:
        Path to saved report
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all plots
    if 'comparison_matrix' in all_metrics:
        plot_confusion_matrix(
            all_metrics['comparison_matrix'],
            save_path=os.path.join(output_dir, 'confusion_matrix.png'),
            show=show_plots
        )
    
    if 'semantic_metrics' in all_metrics and 'keyword_metrics' in all_metrics:
        plot_metrics_comparison(
            all_metrics['semantic_metrics'],
            all_metrics['keyword_metrics'],
            save_path=os.path.join(output_dir, 'metrics_comparison.png'),
            show=show_plots
        )
        
        plot_precision_recall_curve(
            all_metrics['semantic_metrics'],
            all_metrics['keyword_metrics'],
            save_path=os.path.join(output_dir, 'precision_recall_curve.png'),
            show=show_plots
        )
    
    if 'semantic_results' in all_metrics and 'keyword_results' in all_metrics:
        plot_score_distribution(
            all_metrics['semantic_results'],
            all_metrics['keyword_results'],
            save_path=os.path.join(output_dir, 'score_distribution.png'),
            show=show_plots
        )
    
    if 'by_source_metrics' in all_metrics:
        plot_accuracy_by_source(
            all_metrics['by_source_metrics'],
            save_path=os.path.join(output_dir, 'accuracy_by_source.png'),
            show=show_plots
        )
    
    # Create text report
    report_path = os.path.join(output_dir, 'evaluation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SEARCH ACCURACY EVALUATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        if 'semantic_metrics' in all_metrics:
            f.write("SEMANTIC SEARCH METRICS:\n")
            f.write("-" * 80 + "\n")
            for key, value in sorted(all_metrics['semantic_metrics'].items()):
                f.write(f"  {key:20s}: {value:.4f}\n")
            f.write("\n")
        
        if 'keyword_metrics' in all_metrics:
            f.write("KEYWORD SEARCH METRICS:\n")
            f.write("-" * 80 + "\n")
            for key, value in sorted(all_metrics['keyword_metrics'].items()):
                f.write(f"  {key:20s}: {value:.4f}\n")
            f.write("\n")
        
        if 'comparison_matrix' in all_metrics:
            f.write("SEARCH METHOD AGREEMENT:\n")
            f.write("-" * 80 + "\n")
            cm = all_metrics['comparison_matrix']
            f.write(f"  Documents found by both methods: {cm.get('both', 0)}\n")
            f.write(f"  Only in semantic results: {cm.get('only_semantic', 0)}\n")
            f.write(f"  Only in keyword results: {cm.get('only_keyword', 0)}\n")
            f.write(f"  Total semantic results: {cm.get('total_semantic', 0)}\n")
            f.write(f"  Total keyword results: {cm.get('total_keyword', 0)}\n")
            f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write(f"Report generated. Plots saved to: {output_dir}\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"Evaluation report saved to {report_path}")
    return report_path

