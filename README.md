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
1. Clone the repository
```bash
git clone [repository-url]
```

2. Install Python dependencies
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR
- Windows: Download from GitHub
- Linux: `sudo apt-get install tesseract-ocr`

4. Install Poppler
- Windows: Download and add to PATH
- Linux: `sudo apt-get install poppler-utils`

5. Setup Elasticsearch
- Download and install Elasticsearch 8.17.4
- Start Elasticsearch service

## Usage
1. Download PDFs:
```bash
python src/download_pdfs.py
```

2. Process and index documents:
```bash
python src/process_and_index.py --es-password YOUR_PASSWORD
```

3. Search documents:
```bash
python src/search_documents.py --es-password YOUR_PASSWORD "your search query"
```

## Project Structure

src/
├── scrapers/
│ ├── init.py
│ ├── base_scraper.py
│ ├── income_tax_scraper.py
│ ├── rbi_scraper.py
│ └── caqm_scraper.py
├── download_pdfs.py
├── process_documents.py
└── search_documents.py

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
