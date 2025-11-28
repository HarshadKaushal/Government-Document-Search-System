# Web Interface - Complete ✅

## What's Been Built

A complete, modern web interface for searching government documents with full search type selection and filtering capabilities.

## Features Implemented

### ✅ Search Type Selection
- **Semantic Search** (Vector-based) - Understands meaning and context
- **Keyword Search** (BM25) - Exact word matching  
- **Both** - Compare results from both methods side-by-side

### ✅ Advanced Filtering
- **Source Filter**: Income Tax, RBI, CAQM, or All Sources
- **Section Filter**: Circulars, Notifications, Orders, or All Sections
- **Result Count**: 5, 10, 20, or 50 results
- **Deduplication**: Toggle to show one result per document

### ✅ Beautiful UI/UX
- Modern, responsive design with gradient background
- Clean search form with intuitive filters
- Real-time search with loading indicators
- Formatted results with metadata badges
- System statistics display
- Error handling and no-results messages

### ✅ Technical Features
- RESTful API endpoints
- Asynchronous search requests
- Result deduplication logic
- Score formatting (percentage display)
- Responsive design (mobile-friendly)

## Files Created

1. **`src/app.py`** - Flask backend application
   - Search API endpoint (`/api/search`)
   - Statistics API endpoint (`/api/stats`)
   - Result formatting and deduplication
   - Error handling

2. **`src/templates/index.html`** - Main HTML template
   - Search form with all filters
   - Results display area
   - Statistics section
   - Loading and error states

3. **`src/static/style.css`** - Styling
   - Modern gradient design
   - Responsive layout
   - Beautiful result cards
   - Color-coded badges

4. **`src/static/script.js`** - Frontend JavaScript
   - Form handling
   - API integration
   - Result rendering
   - Dynamic updates

5. **`src/run_server.py`** - Server startup script
   - Environment variable configuration
   - Server initialization

6. **`requirements.txt`** - Updated with Flask dependency

## How to Use

### Start the Server

```bash
python src/run_server.py
```

### Access the Interface

Open your browser to: `http://localhost:5000`

### Search Options

1. **Enter Query**: Type your search text
2. **Choose Search Type**: Select semantic, keyword, or both
3. **Apply Filters**: 
   - Select source (Income Tax, RBI, CAQM)
   - Select section (Circulars, Notifications, Orders)
   - Choose result count
   - Toggle deduplication
4. **Click Search**: View formatted results

## Example Usage

### Semantic Search
- Query: "income tax return filing"
- Search Type: Semantic
- Source: Income Tax
- Results: Contextually relevant documents

### Keyword Search
- Query: "RBI circular"
- Search Type: Keyword
- Source: RBI
- Section: Circulars
- Results: Documents containing exact terms

### Compare Both
- Query: "tax regulations"
- Search Type: Both
- Results: Side-by-side comparison of semantic vs keyword results

## API Endpoints

### POST /api/search
Search documents with filters and search type selection.

**Request Body:**
```json
{
  "query": "search text",
  "search_type": "semantic|keyword|both",
  "source": "income_tax|rbi|caqm|all",
  "section": "Circulars|Notifications|Orders|all",
  "size": 10,
  "deduplicate": true
}
```

**Response:**
```json
{
  "query": "search text",
  "search_type": "semantic",
  "results": [...],
  "total": 10
}
```

### GET /api/stats
Get system statistics (document count, source distribution).

**Response:**
```json
{
  "total_documents": 961,
  "sources": {
    "income_tax": 500,
    "rbi": 300,
    "caqm": 161
  },
  "sections": {...}
}
```

## UI Features

### Search Form
- Large, prominent search input
- Dropdown filters for easy selection
- Checkbox for deduplication
- Submit button with hover effects

### Results Display
- Numbered results with clear hierarchy
- Color-coded badges (source, section, score)
- Text previews with truncation
- Metadata display (date, page, filename)
- Hover effects for interactivity

### Statistics Panel
- Total document count
- Distribution by source
- Distribution by section
- Auto-loads on page load

## Configuration

### Environment Variables
- `ES_HOST` - Elasticsearch host (default: localhost)
- `ES_PORT` - Elasticsearch port (default: 9200)
- `ES_USERNAME` - Elasticsearch username (optional)
- `ES_PASSWORD` - Elasticsearch password (optional)
- `PORT` - Flask port (default: 5000)
- `FLASK_DEBUG` - Enable debug mode (default: False)

## Status

✅ **Complete and Ready to Use**
- All features implemented
- Beautiful, responsive UI
- Full search type selection
- Comprehensive filtering
- Error handling
- Statistics display

---

**Ready to launch!** Run `python src/run_server.py` and open `http://localhost:5000` in your browser.

