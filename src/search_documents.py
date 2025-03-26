from process_documents import DocumentProcessor
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Search through indexed documents')
    parser.add_argument('--es-password', required=True, help='Elasticsearch password')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--source', help='Filter by source (income_tax, rbi, or caqm)', default=None)
    args = parser.parse_args()

    # Initialize processor
    processor = DocumentProcessor(es_password=args.es_password)
    
    # Search documents
    results = processor.search_documents(args.query, args.source)
    
    # Print results
    print(f"\nFound {len(results)} matching documents:")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Date: {result['date']}")
        print(f"   Source: {result['source']}")
        print(f"   Section: {result['section']}")
        print(f"   File: {result['file_path']}")
        if result['highlights']:
            print("   Matching content:")
            for highlight in result['highlights']:
                print(f"   - {highlight}")
        print("-" * 80)

if __name__ == "__main__":
    main() 