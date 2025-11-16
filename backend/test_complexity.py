#!/usr/bin/env python3

def needs_llm_analysis(question):
    # Analytical keywords
    analytical = ['어떤', '가장', '높은', '낮은', '비교', '분석', '왜', '어떻게', '차이', '설명', '해석', '의견', '판단', '방법', '기준', '요건', '범위']
    # Question patterns (fixed patterns)
    complex_patterns = ['에 대해', '관련해서', '의 경우', '라면', '할 때', '한다면', '에서는', '에 따라', '을 위해', '를 위해']
    # Legal reasoning keywords
    legal_reasoning = ['판례', '근거', '법리', '해석', '적용', '검토', '의미', '취지', '원칙', '효력', '책임', '의무']
    # Context-dependent words
    context_words = ['그럼', '그러면', '이 경우', '앞서', '위에서', '그것', '이것', '그런데', '또한', '하지만']
    # Question words that indicate complexity
    question_words = ['어떻게', '왜', '무엇', '언제', '어디서', '누가', '얼마나']
    
    question_lower = question.lower()
    
    # Check for multiple criteria
    has_analytical = any(kw in question for kw in analytical)
    has_patterns = any(pattern in question for pattern in complex_patterns)
    has_legal = any(kw in question for kw in legal_reasoning)
    has_context = any(kw in question for kw in context_words)
    has_question_words = any(kw in question for kw in question_words)
    is_long = len(question) > 15  # Reduced threshold
    has_multiple_concepts = question.count(' ') > 3  # Reduced threshold
    ends_with_question = question.strip().endswith('?') or question.strip().endswith('요')
    
    # Debug output
    print(f"🔍 Question: {question}")
    print(f"   Analytical: {has_analytical}, Patterns: {has_patterns}, Legal: {has_legal}")
    print(f"   Context: {has_context}, Question words: {has_question_words}")
    print(f"   Long: {is_long}, Multiple concepts: {has_multiple_concepts}, Question format: {ends_with_question}")
    
    # More aggressive detection
    is_complex = (has_analytical or has_patterns or has_legal or has_context or 
                 has_question_words or (is_long and has_multiple_concepts) or
                 (ends_with_question and len(question) > 10))
    
    print(f"   → Complex: {is_complex}\n")
    return is_complex

# Test cases
test_questions = [
    # Simple (should be False)
    "임대차 계약",
    "손해배상",
    "교통사고",
    
    # Complex (should be True)
    "계약 위반 시 손해배상 범위는 어떻게 결정되나요?",
    "임대차보증금 반환청구권과 우선변제권의 관계에 대해 분석해주세요",
    "교통사고 손해배상은 어떻게 계산하나요?",
    "그럼 과실비율은 어떻게 정해지나요?",
    "부동산 매매계약 해제 시 중개수수료 반환 기준을 설명해주세요"
]

print("🧪 Testing Complexity Detection\n")

for question in test_questions:
    result = needs_llm_analysis(question)
    expected = "Complex" if result else "Simple"
    print(f"Result: {expected}")
    print("-" * 50)
