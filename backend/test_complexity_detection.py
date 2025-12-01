#!/usr/bin/env python
"""Test complexity detection logic"""

def needs_llm_analysis(question):
    # Simple search indicators (should NOT use LLM)
    simple_search = ['찾아줘', '찾아주세요', '검색', '알려줘', '알려주세요', '보여줘', '보여주세요', '있어?', '있나요']
    
    # Check if it's a simple search request
    if any(kw in question for kw in simple_search):
        return False
    
    # Analytical keywords requiring interpretation
    analytical = ['가장', '높은', '낮은', '비교', '분석', '왜', '어떻게', '차이', '설명', '해석', '의견', '판단']
    # Question patterns requiring reasoning
    complex_patterns = ['에 대해', '의 경우', '라면', '할 때', '한다면']
    # Legal reasoning keywords
    legal_reasoning = ['근거', '법리', '적용', '검토', '의미', '취지', '원칙', '효력']
    # Context-dependent words
    context_words = ['그럼', '그러면', '이 경우', '앞서', '위에서', '그것', '이것']
    # Question words requiring explanation
    question_words = ['어떻게', '왜', '무엇', '언제']
    
    # Check for complexity indicators
    has_analytical = any(kw in question for kw in analytical)
    has_patterns = any(pattern in question for pattern in complex_patterns)
    has_legal = any(kw in question for kw in legal_reasoning)
    has_context = any(kw in question for kw in context_words)
    has_question_words = any(kw in question for kw in question_words)
    
    # Requires LLM only if has reasoning/interpretation needs
    is_complex = (has_analytical or has_patterns or has_legal or 
                 has_context or has_question_words)
    
    return is_complex

# Test cases
test_cases = [
    # Simple searches (should be False)
    ("손해배상 관련 판례를 2개만 찾아줘", False),
    ("교통사고 사건 알려줘", False),
    ("부동산 매매 계약 검색", False),
    ("임대차 분쟁 있어?", False),
    ("계약 위반 판례 보여주세요", False),
    
    # Complex questions (should be True)
    ("계약 해제의 요건은 무엇인가요?", True),
    ("불법행위와 채무불이행의 차이는?", True),
    ("이 경우 손해배상을 청구할 수 있나요?", True),
    ("왜 과실상계가 적용되나요?", True),
    ("손해배상액은 어떻게 산정하나요?", True),
    ("그럼 소멸시효는 언제까지인가요?", True),
]

print("="*60)
print("복잡도 감지 테스트")
print("="*60)

passed = 0
failed = 0

for question, expected in test_cases:
    result = needs_llm_analysis(question)
    status = "✅" if result == expected else "❌"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} '{question}'")
    print(f"   예상: {'LLM 필요' if expected else 'DB 검색'}, "
          f"결과: {'LLM 필요' if result else 'DB 검색'}\n")

print("="*60)
print(f"결과: {passed}개 통과, {failed}개 실패")
print("="*60)
