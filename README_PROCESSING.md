# Processing and Indexing Guide

This guide explains how to process PDFs and index them into Elasticsearch for semantic search.

## Overview

The processing and indexing pipeline consists of:

1. **PDF Processing** - Extract text from PDFs and split into chunks
2. **Embedding Generation** - Generate semantic embeddings for text chunks
3. **Elasticsearch Indexing** - Index documents with embeddings for semantic search

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `pymupdf` or `pdfplumber` - PDF text extraction
- `sentence-transformers` - Semantic embeddings
- `elasticsearch` - Search backend
- `tqdm` - Progress bars

### 2. Install Elasticsearch

**Option A: Docker (Recommended)**
```bash
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  elasticsearch:8.9.0
```

**Option B: Local Installation**
- Download Elasticsearch 8.9.0 from [elastic.co](https://www.elastic.co/downloads/elasticsearch)
- Follow installation instructions
- Start Elasticsearch service

Verify Elasticsearch is running:
```bash
curl http://localhost:9200
```

## Usage

### Step 1: Process PDFs

Extract text from all downloaded PDFs and save as JSON:

```bash
python src/process_documents.py
```

Options:
- `--download-dir downloads` - Directory with PDFs (default: downloads)
- `--output-dir data/processed` - Output directory (default: data/processed)
- `--chunk-size 500` - Words per chunk (default: 500)
- `--chunk-overlap 100` - Overlap between chunks (default: 100)
- `--no-skip-existing` - Re-process existing files

**Output:** JSON files in `data/processed/` with extracted text and chunks.

### Step 2: Index Documents

Generate embeddings and index documents into Elasticsearch:

```bash
python src/process_and_index.py --es-password YOUR_PASSWORD
```

If Elasticsearch has no password:
```bash
python src/process_and_index.py --es-username "" --es-password ""
```

Options:
- `--processed-dir data/processed` - Directory with processed JSON files
- `--index-name government_documents` - Elasticsearch index name
- `--embedding-model all-MiniLM-L6-v2` - Embedding model (default: all-MiniLM-L6-v2)
- `--es-host localhost` - Elasticsearch host
- `--es-port 9200` - Elasticsearch port
- `--es-username elastic` - Elasticsearch username
- `--es-password PASSWORD` - Elasticsearch password
- `--delete-existing` - Delete existing index if it exists
- `--batch-size 32` - Batch size for embeddings

**Alternative: Process and Index in One Step**

If you haven't processed PDFs yet:
```bash
python src/process_and_index.py \
  --download-dir downloads \
  --processed-dir data/processed \
  --es-password YOUR_PASSWORD
```

This will:
1. Process all PDFs in `downloads/`
2. Save processed JSON to `data/processed/`
3. Generate embeddings
4. Index into Elasticsearch

## Embedding Models

Available models (from sentence-transformers):

- **all-MiniLM-L6-v2** (default)
  - Fast, 384 dimensions
  - Good quality for English
  - Recommended for most use cases

- **paraphrase-multilingual-MiniLM-L12-v2**
  - Multilingual support
  - 384 dimensions
  - Good for Hindi/English documents

- **all-mpnet-base-v2**
  - Higher quality, slower
  - 768 dimensions
  - Best quality if speed is not critical

## Data Structure

### Processed Document Structure

Each processed document is saved as JSON with:

```json
{
  "doc_id": "unique_hash",
  "title": "Document Title",
  "source": "rbi|income_tax|caqm",
  "date": "YYYY-MM-DD",
  "section": "Circulars|Notifications|...",
  "filepath": "downloads/...",
  "filename": "document.pdf",
  "file_size": 12345,
  "is_scanned": false,
  "text_chunks": [
    {
      "chunk_id": 0,
      "text": "chunk text...",
      "page": 1
    }
  ],
  "full_text": "complete extracted text",
  "num_chunks": 5,
  "num_pages": 10,
  "metadata": {
    "processed_at": "2024-01-01T00:00:00Z",
    "extraction_method": "fitz"
  }
}
```

### Elasticsearch Index Structure

Each chunk is indexed as a separate document with:

- `doc_id` - Document identifier
- `title` - Document title
- `source` - Source (rbi, income_tax, caqm)
- `date` - Document date
- `section` - Section name
- `chunk_id` - Chunk identifier within document
- `text_chunk` - Chunk text
- `page` - Page number
- `embedding` - 384-dimension embedding vector
- `full_text` - Full document text
- `filename` - PDF filename
- `filepath` - Full file path
- `is_scanned` - Whether PDF is scanned
- `num_pages` - Number of pages

## Troubleshooting

### Elasticsearch Connection Failed

- Check if Elasticsearch is running: `curl http://localhost:9200`
- Verify host/port settings
- Check authentication credentials

### No Text Extracted from PDFs

- PDFs may be scanned/image-only
- Install OCR dependencies for scanned PDFs (pytesseract, pdf2image)
- OCR processing is not included in basic pipeline

### Out of Memory

- Reduce `--batch-size` for embeddings
- Process fewer documents at once
- Increase Elasticsearch heap size

### Slow Processing

- Use PyMuPDF (fitz) for faster extraction (included in requirements)
- Use smaller embedding model (all-MiniLM-L6-v2)
- Reduce chunk size
- Process in batches

## Next Steps

After indexing, you can:
1. Create a search interface (see Phase 4 in WORKFLOW.md)
2. Build a web API for search
3. Add document summarization

See `WORKFLOW.md` for the complete project roadmap.


