import json

with open('src/evaluation/test_queries.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total queries in file: {len(data['test_queries'])}")
print()

queries_with_ids = [q for q in data['test_queries'] if q.get('relevant_doc_ids')]
print(f"Queries with relevant_doc_ids: {len(queries_with_ids)}")
print()

for i, q in enumerate(data['test_queries'], 1):
    has_ids = bool(q.get('relevant_doc_ids'))
    ids_count = len(q.get('relevant_doc_ids', []))
    print(f"{i}. '{q['query']}' - Has IDs: {has_ids} ({ids_count} doc_ids)")

