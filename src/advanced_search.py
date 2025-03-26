from elasticsearch import Elasticsearch
from openai import OpenAI  # Could also use Anthropic's Claude
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os

class AdvancedSearchEngine:
    def __init__(self, es_password: str, openai_key: str):
        # Initialize Elasticsearch
        self.es = Elasticsearch(
            "http://localhost:9200",
            basic_auth=("elastic", es_password),
            verify_certs=False
        )
        
        # Initialize OpenAI
        self.openai_client = OpenAI(api_key=openai_key)
        
        # Initialize BERT model for initial filtering
        self.encoder = SentenceTransformer('all-mpnet-base-v2')  # Better than MiniLM for understanding

    def understand_query(self, user_query: str) -> Dict:
        """Use GPT-4 to understand query context and generate search strategy"""
        prompt = f"""
        Analyze this search query and help me understand:
        1. Main topics
        2. Related concepts
        3. Relevant document types
        4. Time period relevance
        
        Query: {user_query}
        
        Provide response as JSON with these keys.
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return eval(response.choices[0].message.content)

    def semantic_search(self, query: str, query_understanding: Dict) -> List[Dict]:
        """Perform semantic search with context awareness"""
        # Generate embeddings for query
        query_vector = self.encoder.encode(query)
        
        # Build advanced search query
        search_body = {
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["title^2", "content"],
                                        "fuzziness": "AUTO"
                                    }
                                }
                            ],
                            "should": [
                                # Add topic-based boosting
                                *[{
                                    "match": {
                                        "content": {
                                            "query": topic,
                                            "boost": 1.5
                                        }
                                    }
                                } for topic in query_understanding["main_topics"]],
                                
                                # Add related concepts
                                *[{
                                    "match": {
                                        "content": {
                                            "query": concept,
                                            "boost": 1.2
                                        }
                                    }
                                } for concept in query_understanding["related_concepts"]]
                            ],
                            "filter": [
                                # Add time period filter if specified
                                *self._build_time_filters(query_understanding)
                            ]
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                        "params": {"query_vector": query_vector.tolist()}
                    }
                }
            },
            "size": 10
        }
        
        results = self.es.search(index="documents", body=search_body)
        return self._process_results(results, query, query_understanding)

    def _process_results(self, results: Dict, query: str, understanding: Dict) -> List[Dict]:
        """Process and enhance search results using GPT-4"""
        processed_results = []
        
        for hit in results['hits']['hits']:
            doc = hit['_source']
            
            # Use GPT-4 to analyze relevance and extract key points
            analysis_prompt = f"""
            Given the search query context:
            {understanding}
            
            Analyze this document's relevance:
            Title: {doc['title']}
            Content: {doc['content'][:500]}...
            
            Provide:
            1. Relevance score (0-100)
            2. Key matching points
            3. Important excerpts
            """
            
            analysis = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            processed_results.append({
                'title': doc['title'],
                'source': doc['source'],
                'date': doc['date'],
                'relevance_score': hit['_score'],
                'gpt_analysis': analysis.choices[0].message.content,
                'content_preview': self._get_smart_excerpt(doc['content'], query)
            })
        
        return processed_results

    def _get_smart_excerpt(self, content: str, query: str) -> str:
        """Use GPT-4 to generate a smart, contextual excerpt"""
        prompt = f"""
        Given this search query: {query}
        And this document content: {content[:1500]}...
        
        Generate a brief, relevant excerpt that best answers the query.
        Include page numbers or sections if mentioned.
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content

    def _build_time_filters(self, understanding: Dict) -> List[Dict]:
        """Build time-based filters based on query understanding"""
        filters = []
        if "time_period" in understanding:
            # Add appropriate date range filters
            pass
        return filters 