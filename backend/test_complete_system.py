#!/usr/bin/env python
"""Test complete civil law chatbot system"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.db_search import legal_search

def test_vector_search():
    print("=" * 60)
    print("1. Vector Search Test")
    print("=" * 60)
    
    queries = [
        "계약 위반 시 손해배상",
        "부동산 매매 계약",
        "불법행위 책임"
    ]
    
    for query in queries:
        print(f"\n질문: {query}")
        results = legal_search.search_legal_documents(query, limit=3)
        print(f"결과: {len(results)}건")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['title']} (거리: {r['distance']:.4f})")

def test_llm_generation():
    print("\n" + "=" * 60)
    print("2. LLM Answer Generation Test")
    print("=" * 60)
    
    query = "계약 해제의 요건은 무엇인가요?"
    print(f"\n질문: {query}")
    
    results = legal_search.search_legal_documents(query, limit=3)
    answer = legal_search.generate_answer_with_context(query, results, [])
    
    print(f"\n답변:\n{answer[:300]}...")

if __name__ == "__main__":
    test_vector_search()
    test_llm_generation()
    print("\n✅ 시스템 테스트 완료")
