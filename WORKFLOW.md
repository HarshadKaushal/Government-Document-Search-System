# Government Document Semantic Search System - Workflow

## Project Goal
Build a comprehensive system that:
1. **Scrapes PDFs** from government websites (Income Tax, RBI, CAQM)
2. **Processes & Indexes** documents using semantic embeddings
3. **Searches** documents using semantic similarity
4. **Summarizes** relevant documents for users

---

## System Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Scrapers  │────▶│  PDF Processing  │────▶│  Embedding &    │
│  (3 Sources)    │     │  (Text + OCR)    │     │  Indexing       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Interface │────▶│  Semantic Search │────▶│   Document      │
│  (Flask/Web)    │     │  Engine          │     │   Summarization │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Current State Assessment

### ✅ **Completed Components**
1. **Scrapers Infrastructure**
   - `BaseScraper` with common functionality
   - `IncomeTaxScraper` - Functional
   - `RBIScraper` - Functional (minor bug to fix)
   - `CAQMScraper` - Functional
   - Metadata extraction utilities
   - PDF download with retry logic
   - Document filtering (citizen-relevant vs technical)

2. **Dependencies**
   - Scraping: `requests`, `beautifulsoup4`
   - PDF Processing: `pdfplumber`, `pytesseract`, `pdf2image`
   - ML/Semantic Search: `sentence-transformers`, `transformers`, `torch`
   - Search Backend: `elasticsearch`
   - Web Interface: `flask`
   - Summarization: `deepseek-ai`, `transformers`

3. **Data**
   - PDFs downloaded in `downloads/` folder
   - Organized by source (rbi, income_tax, caqm)

### ❌ **Missing Components**
1. Main entry point scripts (`download_pdfs.py`, `process_and_index.py`, `search_documents.py`)
2. PDF processing pipeline (text extraction + OCR for scanned PDFs)
3. Semantic embedding generation and storage
4. Elasticsearch indexing setup
5. Semantic search implementation
6. Document summarization module
7. Web interface/API for users
8. Bug fix in `rbi_scraper.py` (missing `scrape_rbi()` function)

---

## Complete Workflow - Phase by Phase

### **PHASE 1: Fix & Complete Scrapers** 🔧

#### Step 1.1: Fix Bug in RBI Scraper
- **File**: `src/scrapers/rbi_scraper.py`
- **Issue**: Line 134 calls `scrape_rbi()` which doesn't exist
- **Fix**: Create standalone function or proper main block

#### Step 1.2: Create Main Download Script
- **File**: `src/download_pdfs.py`
- **Purpose**: Unified entry point to run all scrapers
- **Features**:
  - Run all three scrapers (or specific ones via CLI args)
  - Progress tracking
  - Error handling and logging
  - Skip already downloaded files

#### Step 1.3: Update Scrapers Module
- **File**: `src/scrapers/__init__.py`
- **Action**: Add `IncomeTaxScraper` to exports

---

### **PHASE 2: PDF Processing Pipeline** 📄

#### Step 2.1: Create PDF Processor Module
- **File**: `src/processors/pdf_processor.py`
- **Functionality**:
  - Extract text from PDFs using `pdfplumber` (for text-based PDFs)
  - OCR using `pytesseract` for scanned PDFs
  - Detect if PDF is scanned or text-based
  - Clean extracted text
  - Split into chunks (for long documents)
  - Extract metadata (title, date, source, page numbers)

#### Step 2.2: Document Schema Definition
- **Structure**:
```python
{
    "doc_id": "unique_id",
    "title": "Document Title",
    "source": "rbi|income_tax|caqm",
    "date": "YYYY-MM-DD",
    "section": "Notifications|Circulars|...",
    "filepath": "path/to/file.pdf",
    "text_chunks": [
        {"chunk_id": 0, "text": "...", "page": 1},
        ...
    ],
    "full_text": "complete extracted text",
    "metadata": {...}
}
```

#### Step 2.3: Batch Processing Script
- **File**: `src/process_documents.py`
- **Purpose**: Process all downloaded PDFs
- **Features**:
  - Walk through `downloads/` directory
  - Process each PDF
  - Save processed data to JSON/parquet for next phase
  - Progress bar with tqdm
  - Resume capability (skip already processed)

---

### **PHASE 3: Semantic Embedding & Indexing** 🧠

#### Step 3.1: Embedding Model Selection
- **Options**:
  - `all-MiniLM-L6-v2` (fast, good quality, 384 dim)
  - `paraphrase-multilingual-MiniLM-L12-v2` (multilingual support)
  - `all-mpnet-base-v2` (higher quality, slower, 768 dim)
- **Recommendation**: Start with `all-MiniLM-L6-v2` for speed

#### Step 3.2: Create Embedding Module
- **File**: `src/embeddings/embedding_service.py`
- **Functionality**:
  - Load sentence transformer model
  - Generate embeddings for text chunks
  - Batch processing for efficiency
  - Cache embeddings (save to disk)
  - Generate embeddings for search queries

#### Step 3.3: Elasticsearch Setup & Configuration
- **File**: `src/search/es_setup.py`
- **Purpose**: Configure Elasticsearch index
- **Index Schema**:
```json
{
  "mappings": {
    "properties": {
      "doc_id": {"type": "keyword"},
      "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
      "source": {"type": "keyword"},
      "date": {"type": "date"},
      "section": {"type": "keyword"},
      "text_chunk": {"type": "text"},
      "chunk_id": {"type": "integer"},
      "page": {"type": "integer"},
      "embedding": {"type": "dense_vector", "dims": 384},
      "full_text": {"type": "text"}
    }
  }
}
```

#### Step 3.4: Indexing Script
- **File**: `src/process_and_index.py`
- **Purpose**: Create embeddings and index to Elasticsearch
- **Flow**:
  1. Load processed documents
  2. Generate embeddings for all text chunks
  3. Index to Elasticsearch with embeddings
  4. Store metadata alongside vectors
  5. Progress tracking and error handling

---

### **PHASE 4: Semantic Search Engine** 🔍

#### Step 4.1: Search Service Module
- **File**: `src/search/search_service.py`
- **Functionality**:
  - Accept user query
  - Generate query embedding
  - Perform semantic search using:
    - **Dense vector search** (cosine similarity on embeddings)
    - **Hybrid search** (combine with BM25 for better results)
  - Return ranked results with relevance scores
  - Support filters (source, date range, section)

#### Step 4.2: Result Post-Processing
- **Features**:
  - Deduplicate results (same document, different chunks)
  - Aggregate scores from multiple chunks
  - Highlight relevant snippets
  - Return top N most relevant documents
  - Include metadata (title, date, source, link to PDF)

#### Step 4.3: CLI Search Script
- **File**: `src/search_documents.py`
- **Purpose**: Command-line search interface
- **Usage**: `python src/search_documents.py --es-password PASSWORD "your query"`

---

### **PHASE 5: Document Summarization** 📝

#### Step 5.1: Summarization Module
- **File**: `src/summarization/summarizer.py`
- **Approach Options**:
  
  **Option A: Extractive Summarization** (Faster)
  - Use sentence embeddings to find most representative sentences
  - Preserves original text (good for legal/gov documents)
  - Libraries: `sentence-transformers`, `sumy`
  
  **Option B: Abstractive Summarization** (Better quality)
  - Use LLM (DeepSeek, BART, T5) to generate summaries
  - Creates concise summaries in own words
  - Libraries: `transformers`, `deepseek-ai`
  
  **Option C: Hybrid** (Recommended)
  - Use extractive for quick preview
  - Use abstractive for detailed summary when user requests

#### Step 5.2: Summary Generation Strategy
- **For Search Results**:
  - Generate quick 2-3 sentence summary per document
  - Cache summaries to avoid recomputation
- **For Selected Document**:
  - Generate detailed summary (150-200 words)
  - Include key points, dates, and important information

#### Step 5.3: Integration with Search
- Modify search service to include summaries in results
- Lazy loading: Generate summaries on-demand (not all at once)

---

### **PHASE 6: Web Interface & API** 🌐

#### Step 6.1: Flask API Backend
- **File**: `src/api/app.py`
- **Endpoints**:
  - `GET /api/search?query=...&source=...&date_from=...` - Search documents
  - `GET /api/document/<doc_id>` - Get full document with summary
  - `GET /api/document/<doc_id>/pdf` - Download PDF
  - `POST /api/refresh` - Re-scrape and re-index
  - `GET /api/stats` - System statistics

#### Step 6.2: Frontend (Optional but Recommended)
- **File**: `src/static/index.html` + `src/static/app.js`
- **Features**:
  - Search bar
  - Results display with snippets and summaries
  - Filters (source, date range)
  - Document viewer
  - Download links

#### Step 6.3: Run Script
- **File**: `src/run_server.py`
- **Purpose**: Start Flask development server
- **Usage**: `python src/run_server.py`

---

## Implementation Priority & Timeline

### **Week 1: Foundation**
1. ✅ Fix RBI scraper bug
2. ✅ Create `download_pdfs.py`
3. ✅ Build PDF processor
4. ✅ Test on sample PDFs

### **Week 2: Search Infrastructure**
1. ✅ Set up Elasticsearch
2. ✅ Implement embedding service
3. ✅ Create indexing script
4. ✅ Build search service
5. ✅ Test semantic search

### **Week 3: Summarization & Polish**
1. ✅ Implement summarization
2. ✅ Integrate with search
3. ✅ Create CLI search tool
4. ✅ Testing & optimization

### **Week 4: User Interface**
1. ✅ Build Flask API
2. ✅ Create simple web interface (optional)
3. ✅ End-to-end testing
4. ✅ Documentation

---

## Technical Decisions & Notes

### **Semantic Search Strategy**
- **Primary**: Dense vector search using sentence-transformers
- **Enhancement**: Hybrid search (combine with BM25) for better recall
- **Why**: Government documents have specific terminology; semantic search understands context better than keyword search

### **Chunking Strategy**
- **Size**: 500-800 tokens per chunk
- **Overlap**: 100 tokens overlap between chunks (for context)
- **Why**: Long documents need chunking; overlap maintains context

### **Embedding Model**
- **Initial**: `all-MiniLM-L6-v2` (384 dimensions)
- **Rationale**: Good balance of speed and quality
- **Future**: Can upgrade to larger models if needed

### **Summarization Model**
- **For Gov Docs**: Prefer extractive + keyword highlighting
- **Reason**: Legal/regulatory documents need exact text preservation
- **Tool**: Use sentence-transformers for extractive + BART/T5 for abstractive when needed

### **Data Storage**
- **Processed Text**: Store as JSON/Parquet in `data/processed/`
- **Embeddings**: Store in Elasticsearch (primary) + optional cache on disk
- **Metadata**: Store in Elasticsearch alongside embeddings

---

## File Structure (Final)

```
INFO RET/
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── income_tax_scraper.py
│   │   ├── rbi_scraper.py
│   │   ├── caqm_scraper.py
│   │   └── metadata_utils.py
│   ├── processors/
│   │   ├── __init__.py
│   │   └── pdf_processor.py
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedding_service.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── es_setup.py
│   │   └── search_service.py
│   ├── summarization/
│   │   ├── __init__.py
│   │   └── summarizer.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py
│   ├── download_pdfs.py          # Entry point for scraping
│   ├── process_documents.py      # Process PDFs to text
│   ├── process_and_index.py      # Generate embeddings & index
│   ├── search_documents.py       # CLI search tool
│   └── run_server.py             # Start web server
├── downloads/                    # Raw PDFs
│   ├── rbi/
│   ├── income_tax/
│   └── caqm/
├── data/                         # Processed data
│   ├── processed/                # Extracted text
│   └── embeddings/               # Cached embeddings (optional)
├── models/                       # Downloaded ML models
├── requirements.txt
├── README.md
└── WORKFLOW.md                   # This file
```

---

## Next Steps (Immediate Actions)

1. **Review this workflow** - Confirm approach and priorities
2. **Fix RBI scraper bug** - Quick win
3. **Create PDF processor** - Foundation for everything else
4. **Set up Elasticsearch** - Install and configure locally
5. **Build embedding service** - Core of semantic search

---

## Success Metrics

- ✅ Can scrape PDFs from all 3 sources
- ✅ Can extract text from both text and scanned PDFs
- ✅ Can generate semantic embeddings for all documents
- ✅ Can search and find relevant documents semantically
- ✅ Can summarize documents accurately
- ✅ System responds in <2 seconds for search queries
- ✅ Handles 1000+ documents efficiently

---

*Last Updated: [Current Date]*
*Status: Planning Phase*

