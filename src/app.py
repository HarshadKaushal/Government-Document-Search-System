#!/usr/bin/env python3
"""
Flask web application for government document search.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort
from typing import Optional, List, Dict

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search.es_setup import ElasticsearchSetup
from search.search_service import SearchService
from embeddings.embedding_service import EmbeddingService
from summarization.summarizer import DocumentSummarizer

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Support non-ASCII characters

# Initialize services (lazy loading)
_es_setup = None
_embedding_service = None
_search_service = None
_summarizer = None


def get_search_service():
    """Get or initialize search service."""
    global _es_setup, _embedding_service, _search_service
    
    if _search_service is None:
        # Get Elasticsearch connection params from environment or defaults
        es_host = os.getenv('ES_HOST', 'localhost')
        es_port = int(os.getenv('ES_PORT', '9200'))
        es_username = os.getenv('ES_USERNAME', None)
        es_password = os.getenv('ES_PASSWORD', None)
        
        _es_setup = ElasticsearchSetup(
            host=es_host,
            port=es_port,
            username=es_username,
            password=es_password
        )
        _embedding_service = EmbeddingService()
        _search_service = SearchService(
            es_setup=_es_setup,
            embedding_service=_embedding_service,
            index_name='government_documents'
        )
    
    return _search_service


def get_summarizer():
    """Get or initialize summarizer."""
    global _summarizer
    
    if _summarizer is None:
        _summarizer = DocumentSummarizer()
    
    return _summarizer


@app.route('/')
def index():
    """Render main search page."""
    return render_template('index.html')


@app.route('/api/search', methods=['GET', 'POST'])
def search():
    """Search endpoint."""
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json()
            query = data.get('query', '')
            search_type = data.get('search_type', 'semantic')
            source = data.get('source', None)
            section = data.get('section', None)
            size = int(data.get('size', 10))
            deduplicate = data.get('deduplicate', True)
        else:
            query = request.args.get('query', '')
            search_type = request.args.get('search_type', 'semantic')
            source = request.args.get('source', None)
            section = request.args.get('section', None)
            size = int(request.args.get('size', 10))
            deduplicate = request.args.get('deduplicate', 'true').lower() == 'true'
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get search service
        search_service = get_search_service()
        
        # Prepare filters
        filters = {}
        if source and source != 'all':
            filters['source'] = source
        if section and section != 'all':
            filters['section'] = section
        
        # Perform search
        if search_type == 'semantic':
            results = search_service.search(
                query=query,
                size=size * 3 if deduplicate else size,
                source=filters.get('source'),
                section=filters.get('section')
            )
        elif search_type == 'keyword':
            results = search_service.keyword_search(
                query=query,
                size=size * 3 if deduplicate else size,
                source=filters.get('source'),
                section=filters.get('section')
            )
        else:  # both
            semantic_results = search_service.search(
                query=query,
                size=size,
                source=filters.get('source'),
                section=filters.get('section')
            )
            keyword_results = search_service.keyword_search(
                query=query,
                size=size,
                source=filters.get('source'),
                section=filters.get('section')
            )
            semantic_formatted = format_results(semantic_results, deduplicate, size)
            keyword_formatted = format_results(keyword_results, deduplicate, size)
            
            # Add search_type to each result
            for result in semantic_formatted:
                result['search_type'] = 'semantic'
            for result in keyword_formatted:
                result['search_type'] = 'keyword'
            
            # Check if summaries are requested
            include_summaries = data.get('include_summaries', False) if request.method == 'POST' else request.args.get('include_summaries', 'false').lower() == 'true'
            
            # Generate summaries if requested
            if include_summaries:
                try:
                    summarizer = get_summarizer()
                    if semantic_formatted:
                        semantic_formatted = summarizer.summarize_search_results(
                            semantic_formatted,
                            num_sentences_per_doc=2,
                            query=query
                        )
                    if keyword_formatted:
                        keyword_formatted = summarizer.summarize_search_results(
                            keyword_formatted,
                            num_sentences_per_doc=2,
                            query=query
                        )
                except Exception as e:
                    logger.error(f"Error generating summaries: {e}")
            
            return jsonify({
                'query': query,
                'search_type': 'both',
                'semantic_results': semantic_formatted,
                'keyword_results': keyword_formatted,
                'total_semantic': len(semantic_formatted),
                'total_keyword': len(keyword_formatted),
                'summaries_included': include_summaries
            })
        
        # Format results
        formatted_results = format_results(results, deduplicate, size)
        
        # Add search_type to each result for proper score formatting
        for result in formatted_results:
            result['search_type'] = search_type
        
        # Check if summaries are requested
        include_summaries = data.get('include_summaries', False) if request.method == 'POST' else request.args.get('include_summaries', 'false').lower() == 'true'
        
        # Generate summaries if requested
        if include_summaries and formatted_results:
            try:
                summarizer = get_summarizer()
                formatted_results = summarizer.summarize_search_results(
                    formatted_results,
                    num_sentences_per_doc=2,
                    query=query
                )
            except Exception as e:
                logger.error(f"Error generating summaries: {e}")
                # Continue without summaries if generation fails
        
        return jsonify({
            'query': query,
            'search_type': search_type,
            'results': formatted_results,
            'total': len(formatted_results),
            'summaries_included': include_summaries
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def format_results(results: List[Dict], deduplicate: bool, max_size: int) -> List[Dict]:
    """Format search results."""
    if not results:
        return []
    
    # Deduplicate if requested
    if deduplicate:
        from collections import defaultdict
        doc_results = defaultdict(list)
        
        for result in results:
            doc_id = result.get('doc_id', '')
            doc_results[doc_id].append(result)
        
        # Keep best chunk per document
        deduplicated = []
        for doc_id, chunks in doc_results.items():
            sorted_chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)
            deduplicated.append(sorted_chunks[0])
        
        # Re-sort and limit
        deduplicated.sort(key=lambda x: x.get('score', 0), reverse=True)
        results = deduplicated[:max_size]
    
    # Format for JSON response
    formatted = []
    for result in results:
        formatted.append({
            'doc_id': result.get('doc_id', ''),
            'title': result.get('title', 'Unknown Title'),
            'source': result.get('source', 'unknown'),
            'section': result.get('section', 'Document'),
            'date': result.get('date', None),
            'score': result.get('score', 0),
            'raw_score': result.get('score', 0),  # Keep original score
            'text_chunk': result.get('text_chunk', ''),
            'page': result.get('page', None),
            'filename': result.get('filename', ''),
            'filepath': result.get('filepath', ''),
            'is_scanned': result.get('is_scanned', False),
            'num_pages': result.get('num_pages', 0)
        })
    
    return formatted


@app.route('/api/stats', methods=['GET'])
def stats():
    """Get system statistics."""
    try:
        search_service = get_search_service()
        es_client = search_service.es_setup.get_client()
        
        # Get document count
        count_response = es_client.count(index='government_documents')
        total_docs = count_response['count']
        
        # Get source distribution (Elasticsearch 8.x API)
        aggregation = es_client.search(
            index='government_documents',
            size=0,
            aggs={
                "sources": {
                    "terms": {"field": "source", "size": 10}
                },
                "sections": {
                    "terms": {"field": "section", "size": 10}
                }
            }
        )
        
        sources = {bucket['key']: bucket['doc_count'] 
                  for bucket in aggregation['aggregations']['sources']['buckets']}
        sections = {bucket['key']: bucket['doc_count'] 
                   for bucket in aggregation['aggregations']['sections']['buckets']}
        
        return jsonify({
            'total_documents': total_docs,
            'sources': sources,
            'sections': sections
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdf/<path:filepath>', methods=['GET'])
def serve_pdf(filepath):
    """
    Serve PDF files from the downloads directory.
    
    Args:
        filepath: Relative path to PDF file (e.g., 'downloads/rbi/circulars/doc.pdf')
    """
    try:
        # Get project root directory
        project_root = Path(__file__).parent.parent.resolve()
        
        # Construct full path
        # Handle both formats: "downloads/..." or just the relative part
        if filepath.startswith('downloads/'):
            pdf_path = project_root / filepath
        else:
            pdf_path = project_root / 'downloads' / filepath
        
        # Resolve to absolute path and normalize
        pdf_path = pdf_path.resolve()
        downloads_dir = project_root / 'downloads'
        downloads_dir = downloads_dir.resolve()
        
        # Security: ensure path is within downloads directory
        try:
            pdf_path.relative_to(downloads_dir)
        except ValueError:
            abort(403, description="Access denied: File outside downloads directory")
        
        # Check if file exists
        if not pdf_path.exists():
            abort(404, description=f"PDF file not found: {filepath}")
        
        if not pdf_path.is_file():
            abort(400, description="Path is not a file")
        
        # Check if it's a PDF
        if pdf_path.suffix.lower() != '.pdf':
            abort(400, description="File is not a PDF")
        
        # Serve the PDF file
        return send_file(
            str(pdf_path),
            mimetype='application/pdf',
            as_attachment=False,  # Display in browser instead of downloading
            download_name=pdf_path.name
        )
        
    except Exception as e:
        logger.error(f"Error serving PDF {filepath}: {e}")
        import traceback
        traceback.print_exc()
        abort(500, description=str(e))


@app.route('/api/pdf', methods=['GET'])
def serve_pdf_by_doc_id():
    """
    Serve PDF by doc_id - looks up filepath from Elasticsearch.
    """
    try:
        doc_id = request.args.get('doc_id')
        page = request.args.get('page', None, type=int)
        
        if not doc_id:
            abort(400, description="doc_id parameter required")
        
        # Get search service to query Elasticsearch
        search_service = get_search_service()
        es_client = search_service.es_setup.get_client()
        
        # Find document by doc_id
        query = {
            "bool": {
                "must": [
                    {"term": {"doc_id": doc_id}}
                ]
            }
        }
        
        response = es_client.search(
            index='government_documents',
            query=query,
            size=1
        )
        
        if not response['hits']['hits']:
            abort(404, description="Document not found")
        
        hit = response['hits']['hits'][0]
        filepath = hit['_source'].get('filepath', '')
        
        if not filepath:
            abort(404, description="PDF filepath not found in document")
        
        # Get project root
        project_root = Path(__file__).parent.parent.resolve()
        downloads_dir = project_root / 'downloads'
        
        # Convert filepath to Path object
        pdf_path = Path(filepath)
        
        # Handle different filepath formats
        if pdf_path.is_absolute():
            # Absolute path - check if it exists
            pdf_path = pdf_path.resolve()
        else:
            # Relative path - resolve from project root
            # Handle both "downloads/..." and just relative paths
            if filepath.startswith('downloads'):
                pdf_path = project_root / filepath
            else:
                pdf_path = downloads_dir / filepath
            pdf_path = pdf_path.resolve()
        
        # Security check - ensure within downloads directory
        try:
            pdf_path.relative_to(downloads_dir.resolve())
        except ValueError:
            # Check if it's a valid absolute path that exists
            if not pdf_path.exists():
                abort(403, description="Access denied: Path outside downloads directory")
        
        if not pdf_path.exists():
            abort(404, description=f"PDF file not found: {filepath}")
        
        # Serve PDF (optionally jump to specific page if supported by browser)
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=pdf_path.name
        )
        
    except Exception as e:
        logger.error(f"Error serving PDF by doc_id: {e}")
        import traceback
        traceback.print_exc()
        abort(500, description=str(e))


@app.route('/api/summarize', methods=['GET', 'POST'])
def summarize():
    """Summarize a document by doc_id."""
    try:
        if request.method == 'POST':
            data = request.get_json()
            doc_id = data.get('doc_id')
            query = data.get('query', None)
            num_sentences = int(data.get('num_sentences', 3))
        else:
            doc_id = request.args.get('doc_id')
            query = request.args.get('query', None)
            num_sentences = int(request.args.get('num_sentences', 3))
        
        if not doc_id:
            return jsonify({'error': 'doc_id is required'}), 400
        
        # Get search service to query Elasticsearch
        search_service = get_search_service()
        es_client = search_service.es_setup.get_client()
        
        # Find document by doc_id
        query_es = {
            "bool": {
                "must": [
                    {"term": {"doc_id": doc_id}}
                ]
            }
        }
        
        response = es_client.search(
            index='government_documents',
            query=query_es,
            size=1
        )
        
        if not response['hits']['hits']:
            return jsonify({'error': 'Document not found'}), 404
        
        hit = response['hits']['hits'][0]
        document = hit['_source']
        
        # Generate summary
        summarizer = get_summarizer()
        summary = summarizer.summarize_document(
            document,
            num_sentences=num_sentences,
            query=query
        )
        
        return jsonify({
            'doc_id': doc_id,
            'title': document.get('title', 'Unknown'),
            'summary': summary,
            'num_sentences': num_sentences,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error summarizing document: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

