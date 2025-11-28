# Quick View Vector Embedding - Fastest Methods

## 🚀 Method 1: Using the Script (Recommended)

### View any document's embedding:
```bash
python src/view_embedding.py --es-password YOUR_PASSWORD
```

### View specific document:
```bash
python src/view_embedding.py --doc-id "YOUR_DOC_ID" --es-password YOUR_PASSWORD
```

### View specific chunk:
```bash
python src/view_embedding.py --doc-id "YOUR_DOC_ID" --chunk-id 0 --es-password YOUR_PASSWORD
```

---

## ⚡ Method 2: Python One-Liner (Fastest!)

### Quick one-liner to see first embedding:
```bash
python -c "import sys, os; sys.path.insert(0, 'src'); from search import ElasticsearchSetup; es = ElasticsearchSetup(password='YOUR_PASSWORD'); r = es.get_client().search(index='government_documents', body={'size': 1, '_source': ['doc_id', 'title', 'embedding']}); print('Doc:', r['hits']['hits'][0]['_source']['doc_id']); print('Title:', r['hits']['hits'][0]['_source']['title']); print('Embedding (first 10):', r['hits']['hits'][0]['_source']['embedding'][:10])"
```

### View embedding for specific doc_id:
```bash
python -c "import sys, os; sys.path.insert(0, 'src'); from search import ElasticsearchSetup; es = ElasticsearchSetup(password='YOUR_PASSWORD'); r = es.get_client().search(index='government_documents', body={'size': 1, '_source': ['embedding'], 'query': {'term': {'doc_id': 'YOUR_DOC_ID'}}}); print(r['hits']['hits'][0]['_source']['embedding'][:20])"
```

---

## 🌐 Method 3: Direct Elasticsearch API (curl)

```bash
curl -X GET "localhost:9200/government_documents/_search?pretty" -H 'Content-Type: application/json' -d'{"size": 1, "_source": ["doc_id", "title", "embedding"], "query": {"match_all": {}}}'
```

### With authentication:
```bash
curl -u elastic:YOUR_PASSWORD -X GET "localhost:9200/government_documents/_search?pretty" -H 'Content-Type: application/json' -d'{"size": 1, "_source": ["doc_id", "title", "embedding"]}'
```

---

## 📝 Example Output

The script will show:
- Document ID and Title
- Chunk ID
- Embedding dimension (384)
- First 20 values
- Last 10 values
- Vector statistics (min, max, mean)
- Full vector array
- Text chunk preview

---

## 🔍 Find a Document ID First

If you don't know a doc_id, use `find_doc_id.py`:
```bash
python src/find_doc_id.py "filename.pdf"
```

