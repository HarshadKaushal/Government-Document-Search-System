from elasticsearch import Elasticsearch
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--es-password", required=True, help="Elasticsearch password")
    args = parser.parse_args()

    # Connect to Elasticsearch
    es = Elasticsearch(
        "http://localhost:9200",
        basic_auth=("elastic", args.es_password),
        verify_certs=False
    )

    # Check if the index exists
    index_name = "government_documents"
    if es.indices.exists(index=index_name):
        # Get index stats
        stats = es.indices.stats(index=index_name)
        doc_count = stats['_all']['total']['docs']['count']
        print(f"Index '{index_name}' exists with {doc_count} documents")
        
        # Get a sample of documents
        results = es.search(
            index=index_name,
            body={
                "size": 5,
                "sort": [{"_doc": "asc"}]
            }
        )
        
        print("\nSample documents:")
        for hit in results['hits']['hits']:
            doc = hit['_source']
            print(f"\nTitle: {doc.get('title', 'No title')}")
            print(f"Source: {doc.get('source', 'No source')}")
            print(f"Date: {doc.get('date', 'No date')}")
            print("-" * 80)
    else:
        print(f"Index '{index_name}' does not exist")

if __name__ == "__main__":
    main() 