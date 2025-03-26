import os
import pdfplumber   
import pytesseract
from pdf2image import convert_from_path
from elasticsearch import Elasticsearch
import logging
from typing import Dict, List, Optional
import hashlib
from datetime import datetime
import re

class DocumentProcessor:
    def __init__(self, es_password: str = None):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize Elasticsearch with proper SSL configuration
        self.es = Elasticsearch(
            "http://localhost:9200",  # Changed from https to http
            basic_auth=("elastic", es_password),
            verify_certs=False,
            ssl_show_warn=False  # Added to suppress SSL warnings
        )
        
        # Create index if it doesn't exist
        self.index_name = 'government_documents'
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(
                index=self.index_name,
                body={
                    'mappings': {
                        'properties': {
                            'title': {'type': 'text'},
                            'content': {'type': 'text'},
                            'date': {
                                'type': 'date',
                                'format': 'yyyy-MM-dd||dd-MM-yyyy||dd/MM/yyyy||dd MMM yyyy||MMM dd, yyyy||strict_date_optional_time||epoch_millis',
                                'null_value': None
                            },
                            'source': {'type': 'keyword'},
                            'file_path': {'type': 'keyword'},
                            'section': {'type': 'keyword'}
                        }
                    }
                }
            )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using both pdfplumber and OCR if needed"""
        try:
            # First try with pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                
                # If no text found, try OCR
                if not text.strip():
                    self.logger.info(f"No text found with pdfplumber for {pdf_path}, trying OCR...")
                    images = convert_from_path(pdf_path)
                    for image in images:
                        text += pytesseract.image_to_string(image) + '\n'
                
                return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""

    def index_document(self, doc: Dict, pdf_path: str) -> bool:
        """Index document in Elasticsearch"""
        try:
            # Extract text from PDF
            content = self.extract_text_from_pdf(pdf_path)
            if not content:
                self.logger.warning(f"No content extracted from {pdf_path}")
                return False

            # Create document ID from content hash
            doc_id = hashlib.md5(content.encode()).hexdigest()

            # Parse date from filename if possible
            date = None
            date_match = re.search(r'dt\s+(\d{2}[./-]\d{2}[./-]\d{4})', pdf_path)
            if date_match:
                try:
                    date_str = date_match.group(1).replace('.', '-').replace('/', '-')
                    date = datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
                except:
                    date = None

            # Prepare document for indexing
            doc_body = {
                'title': doc['title'],
                'content': content,
                'date': date,  # This will be None if no valid date is found
                'source': doc.get('source', 'unknown'),
                'section': doc.get('section', 'general'),
                'file_path': pdf_path,
                'indexed_at': datetime.now().isoformat()
            }

            # Index the document
            self.es.index(
                index=self.index_name,
                id=doc_id,
                body=doc_body
            )
            self.logger.info(f"Successfully indexed document: {doc['title']}")
            return True

        except Exception as e:
            self.logger.error(f"Error indexing document {doc['title']}: {str(e)}")
            return False

    def search_documents(self, query: str, source: Optional[str] = None) -> List[Dict]:
        """Search for documents matching the query"""
        try:
            search_body = {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'multi_match': {
                                    'query': query,
                                    'fields': ['title^2', 'content'],
                                    'fuzziness': 'AUTO'
                                }
                            }
                        ]
                    }
                },
                'highlight': {
                    'fields': {
                        'content': {
                            'fragment_size': 150,
                            'number_of_fragments': 3
                        }
                    }
                }
            }

            # Add source filter if specified
            if source:
                search_body['query']['bool']['must'].append({
                    'term': {'source': source}
                })

            # Execute search
            results = self.es.search(
                index=self.index_name,
                body=search_body,
                size=10
            )

            # Format results
            formatted_results = []
            for hit in results['hits']['hits']:
                result = {
                    'title': hit['_source']['title'],
                    'date': hit['_source']['date'],
                    'source': hit['_source']['source'],
                    'section': hit['_source']['section'],
                    'file_path': hit['_source']['file_path'],
                    'score': hit['_score'],
                    'highlights': hit.get('highlight', {}).get('content', [])
                }
                formatted_results.append(result)

            return formatted_results

        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []

    def process_document(self, file_path: str, source: str, section: str = None) -> Dict:
        try:
            # Extract text from PDF
            content = self.extract_text_from_pdf(file_path)
            if not content:
                self.logger.warning(f"No content extracted from {file_path}")
                return None

            # Extract title from file name or content
            title = os.path.basename(file_path).split('.')[0]

            # Extract date from title or content
            date = self.extract_date(title) or None

            return {
                'title': title,
                'content': content,
                'date': date,
                'source': source,
                'file_path': file_path,
                'section': section
            }
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {str(e)}")
            return None