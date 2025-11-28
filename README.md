# Government Document Scraper and Search System

A system to scrape, process, and search government documents from multiple sources including Income Tax, RBI, and CAQM.

## Features

- Scrapes PDFs from government websites
- Processes both text and scanned PDFs
- Indexes documents for full-text search
- Provides easy search interface

## Sources

- Income Tax Department (www.incometax.gov.in)
- Reserve Bank of India (www.rbi.org.in)
- Commission for Air Quality Management (caqm.nic.in)

## Requirements

- Python 3.8+
- Elasticsearch 8.17.4
- Tesseract OCR
- Poppler

## Installation

Clone the repository

```bash
git clone [repository-url]
```

Install Python dependencies

```bash
pip install -r requirements.txt
```

Install Tesseract OCR

- Windows: Download from GitHub
- Linux: `sudo apt-get install tesseract-ocr`

Install Poppler

- Windows: Download and add to PATH
- Linux: `sudo apt-get install poppler-utils`

Setup Elasticsearch

- Download and install Elasticsearch 8.17.4
- Start Elasticsearch service

## Usage

1. Download PDFs

```bash
# Download from all sources
python src/download_pdfs.py

# Download from specific source
python src/download_pdfs.py --source income_tax
```

2. Process PDFs

```bash
# Extract text and split into chunks
python src/process_documents.py
```

3. Index Documents (requires Elasticsearch)

```bash
# Index processed documents
python src/process_and_index.py

# If Elasticsearch has password
python src/process_and_index.py --es-password YOUR_PASSWORD

# Process and index in one step
python src/process_and_index.py --download-dir downloads --processed-dir data/processed
```

4. Search Documents

```bash
# Basic search
python src/search_documents.py "income tax return filing"

# Search with source filter
python src/search_documents.py "banking regulations" --source rbi

# Search with section filter
python src/search_documents.py "tax rules" --section Circulars

# Get more results
python src/search_documents.py "pollution control" --size 20

# Show all chunks (no deduplication)
python src/search_documents.py "monetary policy" --no-deduplicate
```

5. Web Interface (Optional)

```bash
# Start the web server
python src/run_server.py

# Then open browser to: http://localhost:5000
```

The web interface provides:

- Search type selection (Semantic, Keyword, or Both)
- Filter by source (Income Tax, RBI, CAQM)
- Filter by section (Circulars, Notifications, Orders)
- Adjustable result count
- Beautiful, responsive UI

## Project Structure

```
src/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py
│   ├── income_tax_scraper.py
│   ├── rbi_scraper.py
│   └── caqm_scraper.py
├── download_pdfs.py
├── process_documents.py
└── search_documents.py
```

## Data Management

The downloaded PDFs are not included in the Git repository due to:

- File size considerations
- Filename length limitations
- Best practices for version control

To get the documents:

1. Run the scraper:
```bash
python src/download_pdfs.py
```

This will automatically download and rename the PDFs with shorter, standardized names.
