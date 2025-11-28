# Search Accuracy Evaluation System - Complete ✅

## What's Been Built

A comprehensive evaluation framework for measuring search accuracy with metrics, matrices, and visualizations.

## Components Created

### 1. **Metrics Module** (`src/evaluation/metrics.py`)
✅ Comprehensive metrics calculation:
- **Precision@K**: Proportion of relevant results in top K
- **Recall@K**: Proportion of relevant documents retrieved
- **F1 Score**: Harmonic mean of precision and recall
- **MRR (Mean Reciprocal Rank)**: How quickly relevant docs appear
- **MAP (Mean Average Precision)**: Comprehensive accuracy measure
- **NDCG@K**: Ranking quality considering position

### 2. **Visualization Module** (`src/evaluation/visualizations.py`)
✅ Beautiful graphs and matrices:
- **Confusion Matrix**: Agreement between semantic/keyword search
- **Metrics Comparison**: Side-by-side bar charts
- **Precision-Recall Curve**: Performance at different K values
- **Score Distribution**: Distribution of search scores
- **Accuracy by Source**: Performance breakdown by document source

### 3. **Main Evaluation Script** (`src/evaluate_search_accuracy.py`)
✅ Complete evaluation pipeline:
- Loads test queries
- Runs semantic and keyword search
- Calculates all metrics
- Generates visualizations
- Creates comprehensive reports

### 4. **Test Query Format** (`src/evaluation/test_queries.json`)
✅ Structured format for evaluation queries with relevance judgments

## Metrics Explained

### Precision@K
- **What**: Of the top K results, how many are relevant?
- **Range**: 0.0 to 1.0 (higher is better)
- **Example**: Precision@10 = 0.7 means 7 out of 10 results are relevant

### Recall@K
- **What**: Of all relevant documents, how many did we find in top K?
- **Range**: 0.0 to 1.0 (higher is better)
- **Example**: Recall@10 = 0.5 means we found 50% of relevant documents

### MRR (Mean Reciprocal Rank)
- **What**: Average of 1/rank for first relevant document
- **Range**: 0.0 to 1.0 (higher is better)
- **Example**: MRR = 0.5 means relevant docs appear on average at position 2

### MAP (Mean Average Precision)
- **What**: Average precision across all relevant documents
- **Range**: 0.0 to 1.0 (higher is better)
- **Example**: MAP = 0.8 means very good overall ranking quality

## Visualizations Generated

1. **Confusion Matrix** (`confusion_matrix.png`)
   - Shows agreement/disagreement between search methods
   - Helps understand when semantic vs keyword work differently

2. **Metrics Comparison** (`metrics_comparison.png`)
   - Side-by-side comparison of all metrics
   - Easy to see which method performs better

3. **Precision-Recall Curve** (`precision_recall_curve.png`)
   - Shows trade-off between precision and recall
   - Curves closer to top-right are better

4. **Score Distribution** (`score_distribution.png`)
   - Histogram and box plot of search scores
   - Helps understand score patterns

5. **Accuracy by Source** (`accuracy_by_source.png`)
   - Performance breakdown by document source (RBI, Income Tax, CAQM)
   - Identifies which sources are easier/harder to search

## How to Use

### Quick Start

1. **Install dependencies**:
   ```bash
   pip install matplotlib seaborn pandas
   ```

2. **Prepare test queries** (add relevance judgments):
   ```json
   {
     "query": "income tax return filing",
     "relevant_doc_ids": ["doc_123", "doc_456"]
   }
   ```

3. **Run evaluation**:
   ```bash
   python src/evaluate_search_accuracy.py
   ```

4. **View results**:
   - Check `evaluation_results/` directory
   - Open generated PNG files
   - Read `evaluation_report.txt`

### Detailed Steps

#### Step 1: Collect Relevance Judgments

To evaluate accuracy, you need to know which documents are relevant:

1. Run searches manually for each query
2. Review results and identify relevant documents
3. Note the `doc_id` of relevant documents
4. Add to `test_queries.json` in `relevant_doc_ids` array

Example workflow:
```bash
# Search for documents
python src/search_documents.py "income tax return filing" --size 20

# Review output, identify relevant doc_ids like:
# doc_income_tax_2023_001
# doc_income_tax_2023_045

# Add to test_queries.json:
{
  "query": "income tax return filing",
  "relevant_doc_ids": ["doc_income_tax_2023_001", "doc_income_tax_2023_045"]
}
```

#### Step 2: Run Evaluation

```bash
python src/evaluate_search_accuracy.py \
  --query-file src/evaluation/test_queries.json \
  --output-dir evaluation_results \
  --no-show  # Don't display plots (save only)
```

#### Step 3: Analyze Results

1. **Check the report**: `evaluation_results/evaluation_report.txt`
2. **View visualizations**: Open PNG files in `evaluation_results/`
3. **Compare metrics**: Look at Precision, Recall, MRR, MAP

## Example Output

```
SEMANTIC SEARCH METRICS:
  Precision@5       : 0.8500
  Precision@10      : 0.7500
  Recall@10         : 0.6000
  F1@10             : 0.6667
  MRR               : 0.8500
  MAP               : 0.7200

KEYWORD SEARCH METRICS:
  Precision@5       : 0.7500
  Precision@10      : 0.6500
  Recall@10         : 0.5500
  F1@10             : 0.5952
  MRR               : 0.7500
  MAP               : 0.6800
```

## Interpretation

### High Precision, Low Recall
- Found documents are relevant, but missing many relevant ones
- Try increasing result size or improving search algorithm

### Low Precision, High Recall
- Finding many documents but many aren't relevant
- Need better ranking/filtering

### Both High
- Excellent search quality! ✅

### Confusion Matrix Insights
- **High "both"**: Methods agree - consistent results
- **High "only_semantic"**: Semantic finds unique relevant docs
- **High "only_keyword"**: Keyword finds unique relevant docs
- **Different methods**: Consider hybrid search

## Command Line Options

```bash
python src/evaluate_search_accuracy.py \
  --query-file src/evaluation/test_queries.json \  # Test queries file
  --output-dir evaluation_results \                 # Output directory
  --es-host localhost \                             # Elasticsearch host
  --es-port 9200 \                                  # Elasticsearch port
  --es-username elastic \                           # ES username
  --es-password YOUR_PASSWORD \                     # ES password
  --index-name government_documents \               # Index name
  --no-show                                         # Save plots only
```

## File Structure

```
src/
├── evaluation/
│   ├── __init__.py              # Module exports
│   ├── metrics.py               # Metrics calculation
│   ├── visualizations.py        # Plotting functions
│   └── test_queries.json        # Test query dataset
├── evaluate_search_accuracy.py  # Main evaluation script
```

## Tips for Good Evaluation

1. **Diverse queries**: Include different query types
   - Short queries: "tax filing"
   - Long queries: "How do I file my income tax return?"
   - Specific: "RBI circular 2023"
   - General: "banking regulations"

2. **Multiple relevance levels**: Start with binary (relevant/not relevant)
   - Can extend to graded relevance later

3. **Representative sample**: 10-20 queries minimum for meaningful stats

4. **Iterative improvement**:
   - Run evaluation
   - Identify weak areas
   - Improve search/indexing
   - Re-evaluate

## Next Steps

1. **Collect relevance judgments**: Start with 5-10 queries
2. **Run first evaluation**: See baseline performance
3. **Analyze results**: Identify improvement opportunities
4. **Iterate**: Improve system and re-evaluate

## Troubleshooting

**"No queries were evaluated"**
→ Add `relevant_doc_ids` to test queries

**"Error connecting to Elasticsearch"**
→ Check ES is running: `curl http://localhost:9200`

**"Module not found"**
→ Install dependencies: `pip install matplotlib seaborn pandas`

**Plots not showing**
→ Use `--no-show` flag to save without displaying

---

## Status: ✅ Complete and Ready!

The evaluation system is fully implemented and ready to use. Just:
1. Add relevance judgments to test queries
2. Run the evaluation script
3. View the beautiful graphs and metrics!

For detailed usage, see `EVALUATION_GUIDE.md`.

