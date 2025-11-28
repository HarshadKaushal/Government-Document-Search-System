"""
Simple and fast PDF processor for text extraction.
Extracts text from PDFs, splits into chunks, and extracts metadata.
"""

import os
import re
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Try PyMuPDF first (fastest)
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF (fitz) not available. Falling back to pdfplumber.")

# Fallback to pdfplumber
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    if not FITZ_AVAILABLE:
        logger.error("Neither PyMuPDF nor pdfplumber available! Install one of them.")


class PDFProcessor:
    """Fast PDF processor for text extraction and chunking."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize PDF processor.
        
        Args:
            chunk_size: Number of words per chunk
            chunk_overlap: Number of words to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.fitz_available = FITZ_AVAILABLE
        self.pdfplumber_available = PDFPLUMBER_AVAILABLE
        
        if not self.fitz_available and not self.pdfplumber_available:
            raise ImportError("No PDF library available. Install PyMuPDF or pdfplumber.")
        
    def generate_doc_id(self, filepath: str) -> str:
        """Generate unique document ID from filepath and metadata."""
        content = f"{filepath}_{os.path.getsize(filepath)}_{os.path.getmtime(filepath)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def extract_text_fast(self, pdf_path: str) -> Tuple[str, int, str]:
        """
        Extract text using fastest available method.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (text, page_count, extraction_method)
        """
        # Try PyMuPDF first (fastest)
        if self.fitz_available:
            try:
                doc = fitz.open(pdf_path)
                text_parts = []
                page_count = len(doc)
                
                for page_num in range(page_count):
                    page = doc[page_num]
                    text = page.get_text()
                    if text:
                        text_parts.append(f"[Page {page_num + 1}]\n{text}\n")
                
                doc.close()
                full_text = "\n".join(text_parts)
                return full_text, page_count, 'fitz'
            except Exception as e:
                logger.warning(f"Fitz extraction failed for {pdf_path}: {e}")
        
        # Fallback to pdfplumber
        if self.pdfplumber_available:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text_parts = []
                    page_count = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if text:
                            text_parts.append(f"[Page {page_num}]\n{text}\n")
                    
                    full_text = "\n".join(text_parts)
                    return full_text, page_count, 'pdfplumber'
            except Exception as e:
                logger.error(f"pdfplumber extraction failed for {pdf_path}: {e}")
        
        return "", 0, 'none'
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text - minimal processing for speed."""
        if not text:
            return ""
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Limit consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def split_into_chunks(self, text: str) -> List[Dict[str, any]]:
        """
        Split text into chunks with overlap - optimized for large documents.
        Uses character-based chunking with word boundary detection to avoid
        creating huge word lists in memory.
        
        Args:
            text: Full text to split
            
        Returns:
            List of chunk dictionaries
        """
        if not text:
            return []
        
        # Use a generator-based approach: find words on-demand without creating full list
        # Estimate words per chunk based on average word length (~5 chars + 1 space = 6)
        avg_chars_per_word = 6
        chunk_char_size = self.chunk_size * avg_chars_per_word
        overlap_char_size = self.chunk_overlap * avg_chars_per_word
        
        # Quick check: estimate if document fits in one chunk
        estimated_words = (len(text) // avg_chars_per_word) + 1
        if estimated_words <= self.chunk_size:
            return [{
                'chunk_id': 0,
                'text': text,
                'page': self._extract_page(text)
            }]
        
        chunks = []
        chunk_id = 0
        start_idx = 0
        text_len = len(text)
        
        # Use iterator to process text in chunks without loading all words
        while start_idx < text_len:
            # Calculate end position
            end_idx = min(start_idx + chunk_char_size, text_len)
            
            # Adjust to word boundary if not at end
            if end_idx < text_len:
                # Look backwards for space/newline (up to 200 chars)
                search_start = max(start_idx, end_idx - 200)
                last_break = text.rfind(' ', search_start, end_idx)
                if last_break == -1:
                    last_break = text.rfind('\n', search_start, end_idx)
                if last_break > search_start:
                    end_idx = last_break + 1
                else:
                    # Look forwards for next space (up to 100 chars)
                    next_break = text.find(' ', end_idx, min(end_idx + 100, text_len))
                    if next_break != -1:
                        end_idx = next_break + 1
            
            # Extract chunk text
            chunk_text = text[start_idx:end_idx].strip()
            
            # Verify word count is reasonable (check without splitting whole text)
            if chunk_text:
                # Quick word count check on chunk only
                word_count = len(chunk_text.split())
                
                # If chunk is too small, try to extend (but limit iterations)
                if word_count < self.chunk_size * 0.5 and end_idx < text_len:
                    # Extend to next good boundary
                    next_break = text.find(' ', end_idx, min(end_idx + chunk_char_size, text_len))
                    if next_break != -1:
                        chunk_text = text[start_idx:next_break + 1].strip()
                        end_idx = next_break + 1
                
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'page': self._extract_page(chunk_text)
                })
                chunk_id += 1
            
            # Move to next chunk with overlap
            if end_idx >= text_len:
                break
            
            # Calculate overlap start
            overlap_start = max(start_idx, end_idx - overlap_char_size)
            # Find word boundary for overlap
            if overlap_start < end_idx:
                space_pos = text.find(' ', overlap_start, min(overlap_start + 200, text_len))
                if space_pos != -1 and space_pos < end_idx:
                    start_idx = space_pos + 1
                else:
                    # Find next word start
                    match = re.search(r'\S', text[overlap_start:min(overlap_start + 200, text_len)])
                    if match:
                        start_idx = overlap_start + match.start()
                    else:
                        start_idx = end_idx
            else:
                start_idx = end_idx
            
            # Safety: prevent infinite loops
            if start_idx >= end_idx:
                start_idx = end_idx + 1
                if start_idx >= text_len:
                    break
        
        return chunks if chunks else [{
            'chunk_id': 0,
            'text': text,
            'page': self._extract_page(text)
        }]
    
    def _extract_page(self, text: str) -> Optional[int]:
        """Extract page number from text if available."""
        match = re.search(r'\[Page\s+(\d+)\]', text)
        return int(match.group(1)) if match else None
    
    def extract_metadata(self, filepath: str) -> Dict[str, any]:
        """Extract metadata from filepath."""
        metadata = {
            'filename': os.path.basename(filepath),
            'filepath': filepath,
            'file_size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            'source': 'unknown'
        }
        
        # Extract source from path
        path_parts = filepath.split(os.sep)
        if 'downloads' in path_parts:
            idx = path_parts.index('downloads')
            if idx + 1 < len(path_parts):
                metadata['source'] = path_parts[idx + 1]
        
        # Try to extract date and section from filename
        filename = metadata['filename']
        
        # Extract date pattern (YYYY-MM-DD or NODATE)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        # Extract section (e.g., Circulars_, Notifications_)
        section_match = re.match(r'^([A-Za-z]+)_', filename)
        if section_match:
            metadata['section'] = section_match.group(1)
        
        return metadata
    
    def process_pdf(self, pdf_path: str, title: str = None, date: str = None, 
                   section: str = None) -> Optional[Dict[str, any]]:
        """
        Process a PDF file and return structured document data.
        
        Args:
            pdf_path: Path to PDF file
            title: Document title (optional, will use filename if not provided)
            date: Document date (optional)
            section: Document section (optional)
            
        Returns:
            Document dictionary or None if processing failed
        """
        if not os.path.exists(pdf_path):
            logger.warning(f"PDF file not found: {pdf_path}")
            return None
        
        filename = os.path.basename(pdf_path)
        logger.info(f"Processing: {filename}")
        
        # Extract text
        full_text, page_count, method = self.extract_text_fast(pdf_path)
        
        if not full_text or len(full_text.strip()) < 50:
            logger.warning(f"No text extracted from {filename} (may be scanned/image-only PDF)")
            # Still return document but mark as scanned
            is_scanned = True
        else:
            is_scanned = False
        
        # Clean text once
        full_text = self.clean_text(full_text)
        
        # Split into chunks only if we have text
        chunks = self.split_into_chunks(full_text) if full_text else []
        
        # Get metadata
        metadata = self.extract_metadata(pdf_path)
        
        # Build document
        doc = {
            'doc_id': self.generate_doc_id(pdf_path),
            'title': title or metadata['filename'].replace('.pdf', '').replace('_', ' '),
            'source': metadata.get('source', 'unknown'),
            'date': date or metadata.get('date'),
            'section': section or metadata.get('section', 'Document'),
            'filepath': pdf_path,
            'filename': metadata['filename'],
            'file_size': metadata['file_size'],
            'is_scanned': is_scanned,
            'text_chunks': chunks,
            'full_text': full_text,
            'num_chunks': len(chunks),
            'num_pages': page_count,
            'metadata': {
                'processed_at': datetime.utcnow().isoformat() + 'Z',
                'extraction_method': method
            }
        }
        
        logger.info(f"Processed: {filename} - {len(chunks)} chunks, {len(full_text)} chars, {page_count} pages")
        return doc
