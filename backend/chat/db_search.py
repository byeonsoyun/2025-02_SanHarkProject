"""
Scalable database search system for legal documents
Handles 200K+ documents efficiently
"""
from django.db.models import Q
from .models import LawDocument
from .ollama_client import OllamaClient
import re
import os
import sys
from pathlib import Path

# Load environment variables
sys.path.append(str(Path(__file__).parent.parent))
try:
    from load_env import load_env
    load_env()
except ImportError:
    pass

class LegalDBSearch:
    def __init__(self):
        # Initialize with environment-based configuration
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        self.ollama_client = OllamaClient(base_url=base_url, model=model)
        
        # Print connection info for debugging
        print(f"🔗 Ollama 연결: {base_url} (모델: {model})")
    
    def search_legal_documents(self, query, limit=10):
        """Enhanced search with better ranking"""
        
        keywords = self._extract_keywords(query)
        
        # Weighted search - title matches score higher
        results = []
        
        # 1. Exact title matches (highest priority)
        for keyword in keywords:
            title_matches = LawDocument.objects.filter(
                title__icontains=keyword
            ).distinct()[:5]
            results.extend(title_matches)
        
        # 2. Content matches
        content_query = Q()
        for keyword in keywords:
            content_query |= Q(content__icontains=keyword)
        
        content_matches = LawDocument.objects.filter(content_query).distinct()[:10]
        results.extend(content_matches)
        
        # 3. Court/case number matches
        meta_query = Q()
        for keyword in keywords:
            meta_query |= (
                Q(court_name__icontains=keyword) |
                Q(case_number__icontains=keyword)
            )
        
        meta_matches = LawDocument.objects.filter(meta_query).distinct()[:5]
        results.extend(meta_matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for doc in results:
            if doc.document_id not in seen:  # Use document_id instead of id
                seen.add(doc.document_id)
                unique_results.append(doc)
        
        return unique_results[:limit]
    
    def generate_answer_with_context(self, question, search_results, recent_chats):
        """Enhanced answer generation with chat context"""
        
        if not search_results:
            return "죄송합니다. 관련 판례를 찾을 수 없습니다. 다른 키워드로 검색해보시거나 더 구체적인 질문을 해주세요."
        
        # Prepare chat context
        context_history = ""
        if recent_chats:
            context_history = "\n【이전 대화 내용】\n"
            for chat in reversed(recent_chats):  # Oldest first
                context_history += f"Q: {chat.question}\nA: {chat.answer[:200]}...\n\n"
        
        # Prepare detailed legal context
        context_parts = []
        for i, doc in enumerate(search_results[:5], 1):
            context_parts.append(
                f"【판례 {i}】\n"
                f"제목: {doc.title}\n"
                f"법원: {doc.court_name}\n"
                f"사건번호: {doc.case_number}\n"
                f"선고일: {doc.enforcement_date}\n"
                f"내용: {doc.content[:300]}...\n"
            )
        
        legal_context = "\n".join(context_parts)
        
        # Enhanced prompt with context awareness
        prompt = f"""당신은 민사법 전문가입니다. 이전 대화 맥락을 고려하여 현재 질문에 대한 전문적인 답변을 작성해주세요.

{context_history}

【검색된 관련 판례】
{legal_context}

【현재 질문】
{question}

【답변 작성 지침】
1. 이전 대화와의 연관성을 고려하여 답변
2. 관련 판례를 구체적으로 인용하여 설명
3. 법적 쟁점과 판단 기준 명시
4. 실무적 시사점 제시
5. 명확하고 이해하기 쉬운 한국어로 작성
6. 맥락상 "그럼", "이 경우" 등의 표현이 있으면 이전 대화를 참조하여 답변

답변:"""
        
        try:
            response = self.ollama_client.generate_response(prompt)
            
            # Add source information
            source_info = f"\n\n【참고 판례】\n"
            for i, doc in enumerate(search_results[:3], 1):
                source_info += f"{i}. {doc.title} ({doc.court_name}, {doc.enforcement_date})\n"
            
            return response + source_info
            
        except Exception as e:
            print(f"Ollama error: {e}")
            # Enhanced fallback with context
            return self._create_enhanced_summary_with_context(question, search_results, recent_chats)
    
    def _create_enhanced_summary_with_context(self, question, results, recent_chats):
        """Create enhanced summary with context awareness"""
        if not results:
            return "관련 판례를 찾을 수 없습니다."
        
        summary = f"【{question}】에 대한 검색 결과\n\n"
        
        # Add context reference if available
        if recent_chats and any(word in question for word in ['그럼', '그러면', '이 경우', '그것', '이것']):
            summary += f"※ 이전 대화와 연관된 질문으로 보입니다.\n\n"
        
        summary += f"총 {len(results)}건의 관련 판례를 찾았습니다.\n\n"
        
        # Group by court for better organization
        court_groups = {}
        for doc in results[:10]:
            court = doc.court_name or "기타"
            if court not in court_groups:
                court_groups[court] = []
            court_groups[court].append(doc)
        
        for court, docs in court_groups.items():
            summary += f"▶ {court}\n"
            for doc in docs[:3]:  # Limit per court
                summary += f"  • {doc.title}\n"
                summary += f"    사건번호: {doc.case_number} | 선고일: {doc.enforcement_date}\n"
            if len(docs) > 3:
                summary += f"    ... 외 {len(docs) - 3}건\n"
            summary += "\n"
        
        summary += "더 구체적인 분석을 원하시면 특정 판례나 법적 쟁점을 명시해 주세요."
        
        return summary
        """Enhanced answer generation with better prompts"""
        
        if not search_results:
            return "죄송합니다. 관련 판례를 찾을 수 없습니다. 다른 키워드로 검색해보시거나 더 구체적인 질문을 해주세요."
        
        # Prepare detailed context
        context_parts = []
        for i, doc in enumerate(search_results[:5], 1):
            context_parts.append(
                f"【판례 {i}】\n"
                f"제목: {doc.title}\n"
                f"법원: {doc.court_name}\n"
                f"사건번호: {doc.case_number}\n"
                f"선고일: {doc.enforcement_date}\n"
                f"내용: {doc.content[:300]}...\n"
            )
        
        context = "\n".join(context_parts)
        
        # Enhanced prompt for better legal analysis
        prompt = f"""당신은 법률 전문가입니다. 다음 판례들을 분석하여 질문에 대한 전문적인 답변을 작성해주세요.

【검색된 관련 판례】
{context}

【질문】
{question}

【답변 작성 지침】
1. 관련 판례를 구체적으로 인용하여 설명
2. 법적 쟁점과 판단 기준 명시
3. 실무적 시사점 제시
4. 명확하고 이해하기 쉬운 한국어로 작성

답변:"""
        
        try:
            response = self.ollama_client.generate_response(prompt)
            
            # Add source information
            source_info = f"\n\n【참고 판례】\n"
            for i, doc in enumerate(search_results[:3], 1):
                source_info += f"{i}. {doc.title} ({doc.court_name}, {doc.enforcement_date})\n"
            
            return response + source_info
            
        except Exception as e:
            print(f"Ollama error: {e}")
            # Enhanced fallback
            return self._create_enhanced_summary(question, search_results)
    
    def _extract_keywords(self, query):
        """Enhanced keyword extraction for legal queries"""
        
        # Legal-specific stop words
        stop_words = {
            '은', '는', '이', '가', '을', '를', '에', '의', '와', '과', '로', '으로',
            '있는', '없는', '하는', '되는', '관련', '대한', '에서', '에게', '부터',
            '까지', '같은', '다른', '어떤', '무엇', '어디', '언제', '왜', '어떻게'
        }
        
        # Important legal terms (boost these)
        legal_terms = {
            '민사', '판결', '법원', '손해배상', '계약', '불법행위', '소유권', '채권', '채무',
            '소송', '판결', '선고', '사건', '재판', '법률', '민법', '상법', '부동산',
            '교통사고', '의료사고', '임금', '해고', '계약해지', '위약금', '손해'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', query)
        
        # Prioritize legal terms, then filter stop words
        keywords = []
        
        # First add legal terms found in query
        for word in words:
            if word in legal_terms:
                keywords.append(word)
        
        # Then add other meaningful words
        for word in words:
            if (len(word) > 1 and 
                word not in stop_words and 
                word not in keywords):
                keywords.append(word)
        
        return keywords[:7]  # Increased limit for better coverage
    
    def _create_enhanced_summary(self, question, results):
        """Create enhanced summary without LLM"""
        if not results:
            return "관련 판례를 찾을 수 없습니다."
        
        summary = f"【{question}】에 대한 검색 결과\n\n"
        summary += f"총 {len(results)}건의 관련 판례를 찾았습니다.\n\n"
        
        # Group by court for better organization
        court_groups = {}
        for doc in results[:10]:
            court = doc.court_name or "기타"
            if court not in court_groups:
                court_groups[court] = []
            court_groups[court].append(doc)
        
        for court, docs in court_groups.items():
            summary += f"▶ {court}\n"
            for doc in docs[:3]:  # Limit per court
                summary += f"  • {doc.title}\n"
                summary += f"    사건번호: {doc.case_number} | 선고일: {doc.enforcement_date}\n"
            if len(docs) > 3:
                summary += f"    ... 외 {len(docs) - 3}건\n"
            summary += "\n"
        
        summary += "더 구체적인 분석을 원하시면 특정 판례나 법적 쟁점을 명시해 주세요."
        
        return summary

# Global instance
legal_search = LegalDBSearch()
