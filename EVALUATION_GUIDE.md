# Search Accuracy Evaluation Guide

## Overview

This evaluation system calculates search accuracy metrics and generates visualizations to compare semantic and keyword search performance.

## Metrics Calculated

### 1. **Precision@K**
- Proportion of relevant documents in top K results
- Higher is better (0.0 to 1.0)

### 2. **Recall@K**
- Proportion of relevant documents retrieved in top K
- Higher is better (0.0 to 1.0)

### 3. **F1 Score@K**
- Harmonic mean of Precision and Recall
- Balanced metric

### 4. **MRR (Mean Reciprocal Rank)**
- Average reciprocal rank of first relevant document
- Measures how quickly relevant documents appear

### 5. **MAP (Mean Average Precision)**
- Average precision across all relevant documents
- Comprehensive accuracy measure

### 6. **NDCG@K (Normalized Discounted Cumulative Gain)**
- Measures ranking quality considering position
- Accounts for relevance ordering

## Visualizations Generated

1. **Confusion Matrix**: Agreement between semantic and keyword search
2. **Metrics Comparison**: Side-by-side bar chart of all metrics
3. **Precision-Recall Curve**: Performance at different K values
4. **Score Distribution**: Distribution of search scores
5. **Accuracy by Source**: Performance breakdown by document source

## How to Use

### Step 1: Prepare Test Queries

Edit `src/evaluation/test_queries.json`:

```json
{
  "test_queries": [
    {
      "query": "income tax return filing",
      "relevant_doc_ids": ["doc_123", "doc_456"],
      "description": "Query about income tax return filing procedures"
    }
  ]
}
```

**Important**: You need to manually specify which documents are relevant for each query.

### Step 2: Collect Relevance Judgments

To evaluate accuracy, you need to know which documents are relevant for each query:

1. **Run search** for each query manually
2. **Review results** and identify relevant documents
3. **Note document IDs** of relevant documents
4. **Add to test_queries.json** in the `relevant_doc_ids` array

Example workflow:
```bash
# Search for documents
python src/search_documents.py "income tax return filing"

# Review results, identify relevant doc_ids
# Add to test_queries.json
```

### Step 3: Run Evaluation

```bash
python src/evaluate_search_accuracy.py
```

### Step 4: View Results

Results are saved to `evaluation_results/`:
- `evaluation_report.txt` - Text summary
- `confusion_matrix.png` - Agreement matrix
- `metrics_comparison.png` - Metrics comparison chart
- `precision_recall_curve.png` - PR curve
- `score_distribution.png` - Score distributions

## Command Line Options

```bash
python src/evaluate_search_accuracy.py \
  --query-file src/evaluation/test_queries.json \
  --output-dir evaluation_results \
  --es-host localhost \
  --es-port 9200 \
  --index-name government_documents \
  --no-show  # Don't display plots (save only)
```

## Understanding the Results

### Confusion Matrix
Shows how many documents are found by:
- **Both methods**: High agreement = both methods find similar results
- **Only semantic**: Documents found by semantic but not keyword
- **Only keyword**: Documents found by keyword but not semantic

### Metrics Comparison
- **Higher bars** = better performance
- Compare semantic vs keyword for each metric
- Look for consistent patterns across metrics

### Precision-Recall Curve
- **Top-right** = best (high precision and recall)
- Curves closer to top-right are better
- Shows trade-off between precision and recall at different K values

## Quick Start

1. **Quick test with minimal setup**:
   ```bash
   # Just see what queries exist (no evaluation yet)
   python src/evaluate_search_accuracy.py
   ```

2. **For full evaluation**, you need relevance judgments:
   - Run searches manually
   - Identify relevant documents
   - Add `relevant_doc_ids` to test_queries.json
   - Run evaluation again

## Tips

- Start with 5-10 queries to test the system
- Focus on diverse query types (different topics, lengths)
- Include both specific and general queries
- Add relevance judgments gradually (you don't need all at once)

## Example Output

```
SEMANTIC SEARCH METRICS:
  Precision@10      : 0.7500
  Recall@10         : 0.6000
  F1@10             : 0.6667
  MRR               : 0.8500
  MAP               : 0.7200

KEYWORD SEARCH METRICS:
  Precision@10      : 0.6500
  Recall@10         : 0.5500
  F1@10             : 0.5952
  MRR               : 0.7500
  MAP               : 0.6800
```

## Troubleshooting

**"No queries were evaluated"**
- Add `relevant_doc_ids` to your test queries

**"Error connecting to Elasticsearch"**
- Make sure Elasticsearch is running
- Check host/port settings

**Plots not displaying**
- Install matplotlib: `pip install matplotlib seaborn pandas`
- Use `--no-show` to save plots without displaying

---

**Status**: ✅ Evaluation system ready to use!

