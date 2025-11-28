# View Vector Embeddings Using Elasticsearch Dev Tools

## What is Dev Tools?

Elasticsearch Dev Tools (also called Kibana Dev Console) is a web-based interface to query Elasticsearch directly. It's the fastest way to inspect your data!

---

## How to Access Dev Tools

### Option 1: Via Kibana (Recommended)
1. Install Kibana (optional but recommended)
2. Go to: `http://localhost:5601`
3. Click **Dev Tools** in the left sidebar (or press `Ctrl + I`)
4. You'll see a console where you can type queries

### Option 2: Via Elasticsearch API Directly
If you don't have Kibana, you can use curl or any HTTP client

---

## Quick Queries to View Embeddings

### 1. Get First Document with Embedding

```json
GET government_documents/_search
{
  "size": 1,
  "_source": {
    "includes": ["doc_id", "title", "chunk_id", "embedding"]
  },
  "query": {
    "match_all": {}
  }
}
```

### 2. Get Embedding for Specific Document

```json
GET government_documents/_search
{
  "size": 5,
  "_source": {
    "includes": ["doc_id", "title", "chunk_id", "embedding", "text_chunk"]
  },
  "query": {
    "term": {
      "doc_id": "YOUR_DOC_ID_HERE"
    }
  }
}
```

### 3. Get Only Embedding Vector (No Other Fields)

```json
GET government_documents/_search
{
  "size": 1,
  "_source": ["embedding"],
  "query": {
    "match_all": {}
  }
}
```

### 4. Count Total Documents with Embeddings

```json
GET government_documents/_count
```

### 5. View Index Mapping (Check Embedding Field Configuration)

```json
GET government_documents/_mapping
```

This will show you the embedding field definition:
```json
{
  "embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  }
}
```

---

## Using curl (Command Line)

### Get First Embedding:
```bash
curl -X GET "localhost:9200/government_documents/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 1,
    "_source": ["doc_id", "title", "embedding"],
    "query": {
      "match_all": {}
    }
  }'
```

### Get Embedding for Specific Doc ID:
```bash
curl -X GET "localhost:9200/government_documents/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "size": 1,
    "_source": ["doc_id", "title", "embedding"],
    "query": {
      "term": {
        "doc_id": "YOUR_DOC_ID_HERE"
      }
    }
  }'
```

### View Index Mapping:
```bash
curl "localhost:9200/government_documents/_mapping?pretty"
```

---

## Understanding the Response

When you run a query, you'll get a response like:

```json
{
  "took": 5,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 961,
      "relation": "eq"
    },
    "max_score": 1.0,
    "hits": [
      {
        "_index": "government_documents",
        "_id": "abc123",
        "_score": 1.0,
        "_source": {
          "doc_id": "doc_xyz",
          "title": "Income Tax Circular",
          "chunk_id": 0,
          "embedding": [
            0.123456,
            -0.789012,
            0.345678,
            ... (384 values total)
          ]
        }
      }
    ]
  }
}
```

**Key parts:**
- `hits.total.value`: Total number of documents
- `hits.hits[0]._source.embedding`: The 384-dimension vector array
- `hits.hits[0]._source.doc_id`: Document identifier
- `hits.hits[0]._source.title`: Document title

---

## Common Queries

### Get All Chunks for a Document:
```json
GET government_documents/_search
{
  "size": 100,
  "query": {
    "term": {
      "doc_id": "YOUR_DOC_ID"
    }
  },
  "sort": [
    {
      "chunk_id": {
        "order": "asc"
      }
    }
  ],
  "_source": ["doc_id", "chunk_id", "embedding"]
}
```

### Get Documents by Source:
```json
GET government_documents/_search
{
  "size": 5,
  "query": {
    "term": {
      "source": "rbi"
    }
  },
  "_source": ["doc_id", "title", "source", "embedding"]
}
```

### View Embedding Statistics (First 10 Documents):
```json
GET government_documents/_search
{
  "size": 10,
  "_source": ["doc_id", "embedding"],
  "query": {
    "match_all": {}
  }
}
```

---

## Pro Tips

1. **Pretty Format**: Add `?pretty` to URLs for formatted JSON output
2. **Limit Results**: Always use `"size": 1` or `"size": 5` when just checking embeddings (they're large!)
3. **Specific Fields**: Use `"_source": ["embedding"]` to get only the vector (faster)
4. **Check Mapping First**: Run `GET government_documents/_mapping` to see all available fields

---

## Troubleshooting

### Embedding field not showing?
- Dense vector fields ARE stored and retrievable in Elasticsearch
- Make sure you're using `"_source": ["embedding"]` or `"includes": ["embedding"]`
- Check if documents were actually indexed with embeddings

### No documents found?
- Verify index exists: `GET _cat/indices?v`
- Check if documents are indexed: `GET government_documents/_count`

### Password Required?
If you have authentication enabled, add credentials:
```bash
curl -u elastic:YOUR_PASSWORD -X GET "localhost:9200/government_documents/_search?pretty" ...
```

---

## Quick Reference

| Query | Purpose |
|-------|---------|
| `GET government_documents/_search` | Search documents |
| `GET government_documents/_count` | Count documents |
| `GET government_documents/_mapping` | View field structure |
| `GET _cat/indices?v` | List all indices |

---

## Example: Complete Workflow

1. **Check if index exists:**
   ```json
   GET _cat/indices?v
   ```

2. **Count documents:**
   ```json
   GET government_documents/_count
   ```

3. **View mapping (see embedding field):**
   ```json
   GET government_documents/_mapping
   ```

4. **Get first embedding:**
   ```json
   GET government_documents/_search
   {
     "size": 1,
     "_source": ["doc_id", "title", "embedding"]
   }
   ```

5. **Get specific document's embedding:**
   ```json
   GET government_documents/_search
   {
     "size": 1,
     "query": {
       "term": {"doc_id": "your_doc_id"}
     },
     "_source": ["embedding"]
   }
   ```

