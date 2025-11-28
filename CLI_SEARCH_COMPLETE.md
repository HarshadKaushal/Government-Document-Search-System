# CLI Search Tool - Complete ✅

## What's Been Built

### **CLI Search Script** (`src/search_documents.py`)

A comprehensive command-line interface for searching government documents using semantic search.

## Features

✅ **Semantic Search**
- Natural language queries
- Relevance scoring (0-100%)    
- Powered by vector embeddings

✅ **Filtering Options**
- Filter by source (RBI, Income Tax, CAQM)
- Filter by section (Circulars, Notifications, etc.)
- Combine multiple filters

✅ **Result Formatting**
- Clean, readable output
- Document metadata (title, source, section, date)
- Text preview snippets
- Relevance scores

✅ **Result Deduplication**
- Shows one result per document (best chunk)
- Prevents duplicate documents in results
- Option to show all chunks with `--no-deduplicate`

✅ **Flexible Configuration**
- Customizable result count
- Elasticsearch connection options
- Authentication support

## Usage Examples

### Basic Search
```bash
python src/search_documents.py "income tax return filing"
```

### Search with Source Filter
```bash
python src/search_documents.py "banking regulations" --source rbi
```

### Search with Section Filter
```bash
python src/search_documents.py "tax rules" --section Circulars
```

### Get More Results
```bash
python src/search_documents.py "pollution control" --size 20
```

### Show All Chunks (No Deduplication)
```bash
python src/search_documents.py "monetary policy" --no-deduplicate
```

### With Elasticsearch Authentication
```bash
python src/search_documents.py "tax filing" --es-username elastic --es-password YOUR_PASSWORD
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `query` | Search query text (required) | - |
| `--size` | Number of results to return | 10 |
| `--source` | Filter by source (rbi, income_tax, caqm) | None |
| `--section` | Filter by section | None |
| `--no-deduplicate` | Show all chunks instead of one per document | False |
| `--es-host` | Elasticsearch host | localhost |
| `--es-port` | Elasticsearch port | 9200 |
| `--es-username` | Elasticsearch username | None |
| `--es-password` | Elasticsearch password | None |

## Output Format

Each result displays:
- **Title**: Document title
- **Source**: Document source (RBI, INCOME_TAX, CAQM)
- **Section**: Document section (Circulars, Notifications, etc.)
- **Date**: Document date (if available)
- **Relevance**: Similarity score as percentage (0-100%)
- **Page**: Page number of the chunk
- **File**: Original PDF filename
- **Preview**: Text snippet from the matching chunk

## Example Output

```
🔍 Searching for: 'income tax'

✅ Found 3 result(s):

================================================================================
[1] Circulars Tax Payer Charter NODATE
────────────────────────────────────────────────────────────────────────────────
Source: INCOME_TAX  |  Section: Circulars  |  Date: N/A  |  Relevance: 76.2%   
Page: 1  |  File: Circulars_Tax_Payer_Charter_NODATE.pdf

Preview:
  [Page 1] TAXPAYERS' CHARTER THE INCOME TAX DEPARTMENT 1. provide fair, courteous, and reasonable treatment...
================================================================================

📊 Summary: 3 document(s) found
```

## Technical Details

- **Search Method**: Semantic search using dense vector embeddings
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Similarity Metric**: Cosine similarity
- **Result Ranking**: By relevance score (highest first)
- **Deduplication**: Keeps best chunk per document when enabled

## Integration

The CLI tool uses:
- `SearchService` - For search orchestration
- `ElasticsearchSetup` - For Elasticsearch connection
- `EmbeddingService` - For query embedding generation

## Status

✅ **Complete and Working**
- All features implemented
- Tested with various queries
- Formatted output verified
- Filters working correctly
- Deduplication functioning

---

**Next Steps**: 
- Add document summarization feature
- Create web interface/API
- Add export functionality (JSON, CSV)

