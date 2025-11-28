# Web Interface - User Guide

## Overview

A beautiful, modern web interface for searching government documents with semantic and keyword search capabilities.

## Features

✅ **Search Type Selection**
- Semantic Search (Vector-based) - Understands meaning and context
- Keyword Search (BM25) - Exact word matching
- Both - Compare results from both methods

✅ **Advanced Filtering**
- Filter by Source (Income Tax, RBI, CAQM, or All)
- Filter by Section (Circulars, Notifications, Orders, or All)
- Adjustable result count (5, 10, 20, 50)
- Deduplication option (one result per document)

✅ **Beautiful UI**
- Modern, responsive design
- Real-time search results
- System statistics display
- Clean result formatting

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install Flask and all other required packages.

### 2. Ensure Elasticsearch is Running

Make sure Elasticsearch is running on `localhost:9200` (or configure via environment variables).

## Running the Web Interface

### Quick Start

```bash
python src/run_server.py
```

### With Custom Configuration

```bash
# Set environment variables
set ES_HOST=localhost
set ES_PORT=9200
set PORT=5000
set FLASK_DEBUG=True

python src/run_server.py
```

### Access the Interface

Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Basic Search

1. Enter your search query in the search box
2. Click "Search" or press Enter
3. View results with relevance scores

### Choose Search Type

Select from the "Search Type" dropdown:
- **Semantic** - Best for conceptual queries (default)
- **Keyword** - Best for exact term matching
- **Both** - Compare results side-by-side

### Apply Filters

Use the filter dropdowns to narrow results:
- **Source**: Filter by Income Tax, RBI, or CAQM
- **Section**: Filter by Circulars, Notifications, or Orders
- **Results**: Choose how many results to show
- **Deduplicate**: Toggle to show one result per document

### Example Searches

- "income tax return filing" - Find tax filing information
- "banking regulations" - Find RBI banking documents
- "air quality pollution" - Find CAQM environmental documents

## API Endpoints

The web interface uses these API endpoints:

### Search
```
POST /api/search
{
  "query": "search text",
  "search_type": "semantic|keyword|both",
  "source": "income_tax|rbi|caqm|all",
  "section": "Circulars|Notifications|Orders|all",
  "size": 10,
  "deduplicate": true
}
```

### Statistics
```
GET /api/stats
```

Returns total document count and distribution by source/section.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ES_HOST` | Elasticsearch host | localhost |
| `ES_PORT` | Elasticsearch port | 9200 |
| `ES_USERNAME` | Elasticsearch username | None |
| `ES_PASSWORD` | Elasticsearch password | None |
| `PORT` | Flask server port | 5000 |
| `HOST` | Flask server host | 0.0.0.0 |
| `FLASK_DEBUG` | Enable debug mode | False |

## Troubleshooting

### Server won't start
- Check if port 5000 is already in use
- Verify Flask is installed: `pip install flask`
- Check Elasticsearch connection

### No results found
- Verify Elasticsearch is running
- Check if documents are indexed
- Try a different search query
- Remove filters to broaden search

### Connection errors
- Ensure Elasticsearch is accessible
- Check host/port configuration
- Verify credentials if authentication is enabled

## File Structure

```
src/
├── app.py                 # Flask application
├── run_server.py          # Server startup script
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── style.css         # CSS styles
    └── script.js         # JavaScript for interactivity
```

## Next Steps

- Add document summarization
- Add PDF download links
- Add document detail view
- Add search history
- Add saved searches

---

**Status**: ✅ Fully functional web interface ready to use!

