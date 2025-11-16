import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Database models import
from user_mgmt.models import ChatHistory, UploadedDocument

# Import RAG integration
try:
    from .rag_integration import rag_chatbot
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("RAG integration not available. Using fallback responses.")

@csrf_exempt
def chat_message(request):
    """Handle chat messages with smart LLM + database search + context"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            session_id = data.get("user_session_id", "ANONYMOUS")
            
            if not message.strip():
                return JsonResponse({"error": "Empty message"}, status=400)
            
            # Enhanced complexity detection
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
                
                print(f"   → Complex: {is_complex}")
                return is_complex
            
            needs_llm = needs_llm_analysis(message)
            
            # Get recent chat history for context
            recent_chats = ChatHistory.objects.filter(
                user_session_id=session_id
            ).order_by('-timestamp')[:5]  # Last 5 exchanges
            
            try:
                from .db_search import legal_search
                
                # Search legal database
                search_results = legal_search.search_legal_documents(message)
                
                if search_results:
                    if needs_llm:
                        # Use LLM for analytical questions with context
                        reply = legal_search.generate_answer_with_context(
                            message, search_results, recent_chats
                        )
                    else:
                        # Use structured summary for simple searches
                        reply = legal_search._create_enhanced_summary(message, search_results)
                else:
                    reply = "관련 법률 정보를 찾을 수 없습니다. 다른 키워드로 검색해보세요."
                    
            except Exception as e:
                reply = f"검색 중 오류: {str(e)}"
            
            # Save chat history
            try:
                ChatHistory.objects.create(
                    user_session_id=session_id, 
                    question=message,
                    answer=reply
                )
            except Exception as db_e:
                print(f"DB save failed: {db_e}")
                
            return JsonResponse({"reply": reply})
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST 요청만 가능"}, status=400)

@csrf_exempt
def upload_pdf(request):
    """Handle PDF upload with database integration"""
    if request.method == "POST" and request.FILES.get("pdf"):
        try:
            pdf_file = request.FILES["pdf"]
            session_id = request.POST.get("user_session_id", "ANONYMOUS")
            
            if not pdf_file.name.lower().endswith('.pdf'):
                return JsonResponse({"error": "PDF 파일만 업로드 가능합니다."}, status=400)
            
            # Save to database
            uploaded_doc = UploadedDocument.objects.create(
                user_session_id=session_id,
                file=pdf_file,
                filename=pdf_file.name
            )
            
            # Process with RAG system if available
            if RAG_AVAILABLE:
                file_path = uploaded_doc.file.path
                processing_result = rag_chatbot.process_pdf(file_path)
                
                # Update RAG processing status
                uploaded_doc.is_rag_ready = True
                uploaded_doc.save()
                
                reply = f"PDF 업로드 완료: {pdf_file.name}\n{processing_result}"
            else:
                reply = f"PDF 업로드 완료: {pdf_file.name} (RAG 처리 불가)"

            return JsonResponse({"reply": reply})
            
        except Exception as e:
            return JsonResponse({"error": f"PDF 처리 중 오류: {str(e)}"}, status=500)

    return JsonResponse({"error": "PDF 파일이 없습니다."}, status=400)

@csrf_exempt
def upload_json_csv(request):
    """Handle JSON/CSV upload with database integration"""
    if request.method == "POST" and request.FILES.get("file"):
        try:
            uploaded_file = request.FILES["file"]
            session_id = request.POST.get("user_session_id", "ANONYMOUS")
            
            if not (uploaded_file.name.lower().endswith('.json') or 
                   uploaded_file.name.lower().endswith('.csv')):
                return JsonResponse({"error": "JSON 또는 CSV 파일만 업로드 가능합니다."}, status=400)
            
            # Save to database
            uploaded_doc = UploadedDocument.objects.create(
                user_session_id=session_id,
                file=uploaded_file,
                filename=uploaded_file.name
            )
            
            # Process with RAG system if available
            if RAG_AVAILABLE:
                try:
                    file_path = uploaded_doc.file.path
                    text_data = rag_chatbot.processor.load_data(file_path)
                    chunks = rag_chatbot.processor.chunk_text(text_data)
                    
                    if not rag_chatbot.is_initialized:
                        rag_chatbot.processor.create_embeddings(chunks)
                        rag_chatbot.processor.create_faiss_index()
                    else:
                        new_embeddings = rag_chatbot.processor.embedding_model.encode(chunks)
                        rag_chatbot.processor.chunks.extend(chunks)
                        rag_chatbot.processor.index.add(new_embeddings.astype('float32'))
                    
                    rag_chatbot.processor.save_index()
                    rag_chatbot.is_initialized = True
                    
                    # Update processing status
                    uploaded_doc.is_rag_ready = True
                    uploaded_doc.save()
                    
                    reply = f"데이터 파일 처리 완료: {uploaded_file.name}\n{len(chunks)}개 청크가 지식베이스에 추가되었습니다."
                except Exception as e:
                    reply = f"데이터 파일 업로드 완료: {uploaded_file.name}\n처리 중 오류: {str(e)}"
            else:
                reply = f"데이터 파일 업로드 완료: {uploaded_file.name} (RAG 처리 불가)"

            return JsonResponse({"reply": reply})
            
        except Exception as e:
            return JsonResponse({"error": f"파일 처리 중 오류: {str(e)}"}, status=500)

    return JsonResponse({"error": "파일이 없습니다."}, status=400)
