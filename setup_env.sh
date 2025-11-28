#!/bin/bash
echo "Setting up environment variables for Government Document Search System"

# Set Elasticsearch password
export ES_PASSWORD=elastic
echo "ES_PASSWORD environment variable set to: elastic"

# Create data directory if it doesn't exist
mkdir -p data
echo "Data directory checked/created"

# Create models directory if it doesn't exist
mkdir -p models
echo "Models directory checked/created"

echo ""
echo "Environment setup complete!"
echo "You can now run the document processing scripts."
echo ""
echo "To process documents: python src/process_and_index.py"
echo "To prepare BERT data: python src/bert_document_processor.py"
echo "" 