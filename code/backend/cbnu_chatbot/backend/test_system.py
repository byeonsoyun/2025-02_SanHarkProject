#!/usr/bin/env python
"""
충북대 챗봇 시스템 테스트 스크립트
"""
import os
import django
import sys

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.models import ChbNotice, NoticeRagIndex, ChatMessage
from chat.services import RAGService

def test_database():
    """데이터베이스 연결 및 데이터 확인"""
    print("\n" + "="*60)
    print("1️⃣ 데이터베이스 테스트")
    print("="*60)
    
    try:
        notice_count = ChbNotice.objects.count()
        index_count = NoticeRagIndex.objects.count()
        chat_count = ChatMessage.objects.count()
        
        print(f"✅ 데이터베이스 연결 성공")
        print(f"   - 공지사항: {notice_count}건")
        print(f"   - RAG 인덱스: {index_count}건")
        print(f"   - 채팅 기록: {chat_count}건")
        
        if notice_count == 0:
            print("\n⚠️ 공지사항이 없습니다. 크롤러를 실행하세요:")
            print("   python manage.py run_crawler")
        
        if index_count == 0:
            print("\n⚠️ RAG 인덱스가 없습니다. 인덱싱을 실행하세요:")
            print("   python manage.py run_rag_index")
        
        return notice_count > 0 and index_count > 0
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        return False


def test_rag_service():
    """RAG 서비스 초기화 테스트"""
    print("\n" + "="*60)
    print("2️⃣ RAG 서비스 테스트")
    print("="*60)
    
    try:
        rag = RAGService()
        
        if rag.embedder is None:
            print("❌ 임베딩 모델 로드 실패")
            return False
        
        print("✅ RAG 서비스 초기화 성공")
        print(f"   - 임베딩 모델: {rag.EMBEDDING_MODEL_NAME}")
        print(f"   - 벡터 차원: {rag.VECTOR_DIMENSION}")
        print(f"   - Ollama URL: {rag.ollama_url}")
        print(f"   - Ollama 모델: {rag.ollama_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG 서비스 오류: {e}")
        return False


def test_search():
    """검색 기능 테스트"""
    print("\n" + "="*60)
    print("3️⃣ 검색 기능 테스트")
    print("="*60)
    
    if NoticeRagIndex.objects.count() == 0:
        print("⚠️ RAG 인덱스가 없어 검색을 건너뜁니다.")
        return False
    
    try:
        rag = RAGService()
        
        test_queries = [
            "기숙사",
            "장학금",
            "취업"
        ]
        
        for query in test_queries:
            print(f"\n🔍 검색어: '{query}'")
            results = rag.retrieve_context(query)
            
            if results:
                print(f"   ✅ {len(results)}건 검색됨")
                for i, r in enumerate(results[:2], 1):
                    title = r['metadata'].get('title', 'N/A')
                    score = r.get('score', 0)
                    print(f"   [{i}] {title} (유사도: {score:.4f})")
            else:
                print(f"   ⚠️ 검색 결과 없음")
        
        return True
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complexity_detection():
    """복잡도 감지 테스트"""
    print("\n" + "="*60)
    print("4️⃣ 복잡도 감지 테스트")
    print("="*60)
    
    try:
        rag = RAGService()
        
        test_cases = [
            ("기숙사 공지 찾아줘", False),  # 단순
            ("장학금 있어?", False),  # 단순
            ("기숙사 신청 방법은 어떻게 되나요?", True),  # 복잡
            ("졸업요건에 대해 설명해줘", True),  # 복잡
            ("올해 취업공고에 뭐뭐 있는지 알려줘", False),  # 단순
        ]
        
        correct = 0
        for query, expected in test_cases:
            result = rag.needs_llm_analysis(query)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{query}'")
            print(f"   예상: {'LLM' if expected else '단순'}, 결과: {'LLM' if result else '단순'}")
            if result == expected:
                correct += 1
        
        print(f"\n정확도: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.1f}%)")
        return correct == len(test_cases)
        
    except Exception as e:
        print(f"❌ 복잡도 감지 오류: {e}")
        return False


def test_ollama():
    """Ollama 연결 테스트"""
    print("\n" + "="*60)
    print("5️⃣ Ollama 연결 테스트")
    print("="*60)
    
    try:
        import requests
        from django.conf import settings
        
        ollama_url = getattr(settings, 'LLM_API_URL', 'http://127.0.0.1:11434/api/generate')
        base_url = ollama_url.replace('/api/generate', '')
        
        # Ollama 서버 상태 확인
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama 서버 연결 성공")
            print(f"   - URL: {base_url}")
            print(f"   - 설치된 모델: {len(models)}개")
            
            for model in models:
                name = model.get('name', 'Unknown')
                print(f"     • {name}")
            
            # llama3 모델 확인
            model_names = [m.get('name', '') for m in models]
            if any('llama3' in name for name in model_names):
                print("\n✅ llama3 모델 확인됨")
                return True
            else:
                print("\n⚠️ llama3 모델이 없습니다. 다운로드하세요:")
                print("   ollama pull llama3")
                return False
        else:
            print(f"❌ Ollama 서버 응답 오류: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Ollama 서버에 연결할 수 없습니다.")
        print("   Ollama가 실행 중인지 확인하세요:")
        print("   ollama serve")
        return False
    except Exception as e:
        print(f"❌ Ollama 테스트 오류: {e}")
        return False


def main():
    """전체 테스트 실행"""
    print("\n" + "="*60)
    print("충북대 챗봇 시스템 테스트")
    print("="*60)
    
    results = {
        "데이터베이스": test_database(),
        "RAG 서비스": test_rag_service(),
        "검색 기능": test_search(),
        "복잡도 감지": test_complexity_detection(),
        "Ollama 연결": test_ollama(),
    }
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{status} - {name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n총 {passed_count}/{total_count} 테스트 통과")
    
    if passed_count == total_count:
        print("\n🎉 모든 테스트 통과! 시스템이 정상 작동합니다.")
        print("\n다음 단계:")
        print("1. 서버 실행: python manage.py runserver")
        print("2. API 테스트: curl -X POST http://localhost:8000/chat/message/ \\")
        print("              -H 'Content-Type: application/json' \\")
        print("              -d '{\"message\": \"기숙사 신청 방법 알려줘\", \"session_id\": \"test\"}'")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 위의 오류 메시지를 확인하세요.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
