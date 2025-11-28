@echo off
echo Setting up environment variables for Government Document Search System

REM Set Elasticsearch password
set ES_PASSWORD=elastic
echo ES_PASSWORD environment variable set to: elastic

REM Create data directory if it doesn't exist
if not exist data mkdir data
echo Data directory checked/created

REM Create models directory if it doesn't exist
if not exist models mkdir models
echo Models directory checked/created

echo.
echo Environment setup complete!
echo You can now run the document processing scripts.
echo.
echo To process documents: python src/process_and_index.py
echo To prepare BERT data: python src/bert_document_processor.py
echo.
pause 