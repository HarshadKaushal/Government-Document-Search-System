"""Evaluation module for search accuracy metrics and visualizations."""

from .metrics import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_mrr,
    calculate_f1_score,
    calculate_map,
    evaluate_search_results
)

from .visualizations import (
    plot_confusion_matrix,
    plot_metrics_comparison,
    plot_score_distribution,
    plot_precision_recall_curve,
    plot_accuracy_by_source,
    create_evaluation_report
)

__all__ = [
    'calculate_precision_at_k',
    'calculate_recall_at_k',
    'calculate_mrr',
    'calculate_f1_score',
    'calculate_map',
    'evaluate_search_results',
    'plot_confusion_matrix',
    'plot_metrics_comparison',
    'plot_score_distribution',
    'plot_precision_recall_curve',
    'plot_accuracy_by_source',
    'create_evaluation_report'
]

