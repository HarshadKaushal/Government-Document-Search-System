# Models Used in This Project

## Important Clarification: No LLMs Used!

This project **does NOT use Large Language Models (LLMs)** like GPT, BERT for generation, or any text generation models.

---

## What Models ARE Used:

### 1. **Sentence Transformers (Embedding Models)**
**Type**: Embedding/Encoder models (NOT LLMs)  
**Purpose**: Convert text into numerical vectors for semantic search

#### Model: `all-MiniLM-L6-v2`
- **Library**: `sentence-transformers` (uses PyTorch/TensorFlow backend)
- **Type**: BERT-based encoder model
- **Output**: 384-dimensional vectors (not text)
- **File**: `src/embeddings/embedding_service.py`
- **Used For**:
  - Converting document text → embedding vectors
  - Converting search queries → embedding vectors
  - Semantic similarity calculations

**Code Location**:
```python
# src/embeddings/embedding_service.py
from sentence_transformers import SentenceTransformer
self.model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = self.model.encode(text)  # Returns vector, NOT text
```

---

### 2. **Document Summarization (Extractive, NOT LLM-based)**

**Type**: Extractive summarization using sentence embeddings  
**Purpose**: Select existing sentences from documents (does NOT generate new text)

#### Same Model Used: `all-MiniLM-L6-v2`
- **File**: `src/summarization/summarizer.py`
- **Method**: 
  1. Splits document into sentences
  2. Generates embeddings for each sentence
  3. Selects most representative sentences (using cosine similarity)
  4. Returns selected sentences verbatim (NO text generation)

**How It Works**:
```python
# src/summarization/summarizer.py
# Uses sentence embeddings to find best sentences
sentence_embeddings = self.model.encode(sentences)
# Selects sentences based on similarity to query/document centroid
# Returns original sentences (not generated text)
```

**Key Point**: This is **extractive summarization** - it selects existing sentences. It does NOT generate new text like an LLM would.

---

## Difference: Embedding Models vs LLMs

| Feature | Sentence Transformers (What we use) | LLMs (What we DON'T use) |
|---------|-------------------------------------|--------------------------|
| **Output** | Numerical vectors (384 numbers) | Generated text |
| **Purpose** | Text → Vector conversion | Text generation/understanding |
| **Example** | "income tax" → `[0.123, -0.456, ...]` | "income tax" → "Income tax is..." |
| **Model Type** | Encoder-only | Encoder-Decoder or Decoder-only |
| **Use Case** | Similarity search, embeddings | Chat, text generation, QA |

---

## Where Models Are Used:

### 1. **Embedding Generation for Search**
- **File**: `src/embeddings/embedding_service.py`
- **When**: During indexing and search
- **What it does**: Converts text to vectors

### 2. **Semantic Search**
- **File**: `src/search/search_service.py`
- **When**: Every search query
- **What it does**: Converts query to embedding, finds similar document embeddings

### 3. **Document Summarization**
- **File**: `src/summarization/summarizer.py`
- **When**: When user requests summary
- **What it does**: Uses embeddings to select best sentences (extractive)

---

## Optional Models (Mentioned but NOT Implemented):

The workflow document mentions these as **future options** but they're **NOT currently used**:

### Abstractive Summarization Models (NOT USED):
- BART (mentioned in WORKFLOW.md as optional)
- T5 (mentioned in WORKFLOW.md as optional)

These would be actual LLMs for text generation, but they're not implemented.

---

## Summary:

✅ **What We Use**: Sentence Transformers (`all-MiniLM-L6-v2`) for embeddings  
❌ **What We DON'T Use**: LLMs for text generation

**Why?**
- Embeddings are fast and efficient for semantic search
- Extractive summarization preserves exact text (important for legal documents)
- No text generation needed - we just find and rank relevant documents

---

## Future Possibilities (If You Want LLMs):

If you wanted to add LLM capabilities, you could:

1. **Abstractive Summarization**: Use BART/T5 to generate summaries
2. **Question Answering**: Use GPT/BERT to answer questions from documents
3. **Document Generation**: Use LLMs to generate explanations

But currently, the project uses **embedding models only** for semantic search!

