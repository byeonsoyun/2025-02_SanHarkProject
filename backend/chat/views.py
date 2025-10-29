import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Import RAG integration
try:
    from .rag_integration import rag_chatbot
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("RAG integration not available. Using fallback responses.")

@csrf_exempt
def chat_message(request):
    """Handle chat messages with RAG integration"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            
            if not message.strip():
                return JsonResponse({"error": "Empty message"}, status=400)
            
            # Use RAG system if available
            if RAG_AVAILABLE:
                reply = rag_chatbot.chat(message)
            else:
                # Fallback response
                reply = f"Echo: {message} (RAG system not available)"
            
            return JsonResponse({"reply": reply})
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST 요청만 가능"}, status=400)

@csrf_exempt
def upload_pdf(request):
    """Handle PDF upload and processing with RAG"""
    if request.method == "POST" and request.FILES.get("pdf"):
        try:
            pdf_file = request.FILES["pdf"]
            
            # Validate file type
            if not pdf_file.name.lower().endswith('.pdf'):
                return JsonResponse({"error": "PDF 파일만 업로드 가능합니다."}, status=400)
            
            # Save file
            save_dir = os.path.join(settings.MEDIA_ROOT, "uploaded_pdfs")
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, pdf_file.name)

            with open(file_path, "wb+") as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)

            # Process with RAG system if available
            if RAG_AVAILABLE:
                processing_result = rag_chatbot.process_pdf(file_path)
                reply = f"PDF 업로드 완료: {pdf_file.name}\n{processing_result}"
            else:
                reply = f"PDF 업로드 완료: {pdf_file.name} (RAG 처리 불가)"

            return JsonResponse({"reply": reply})
            
        except Exception as e:
            return JsonResponse({"error": f"PDF 처리 중 오류: {str(e)}"}, status=500)

    return JsonResponse({"error": "PDF 파일이 없습니다."}, status=400)

@csrf_exempt
def upload_json_csv(request):
    """Handle JSON/CSV upload for RAG system"""
    if request.method == "POST" and request.FILES.get("file"):
        try:
            uploaded_file = request.FILES["file"]
            
            # Validate file type
            if not (uploaded_file.name.lower().endswith('.json') or 
                   uploaded_file.name.lower().endswith('.csv')):
                return JsonResponse({"error": "JSON 또는 CSV 파일만 업로드 가능합니다."}, status=400)
            
            # Save file
            save_dir = os.path.join(settings.MEDIA_ROOT, "uploaded_data")
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, uploaded_file.name)

            with open(file_path, "wb+") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Process with RAG system if available
            if RAG_AVAILABLE:
                try:
                    # Load and process data
                    text_data = rag_chatbot.processor.load_data(file_path)
                    chunks = rag_chatbot.processor.chunk_text(text_data)
                    
                    if not rag_chatbot.is_initialized:
                        rag_chatbot.processor.create_embeddings(chunks)
                        rag_chatbot.processor.create_faiss_index()
                    else:
                        # Add to existing index
                        new_embeddings = rag_chatbot.processor.embedding_model.encode(chunks)
                        rag_chatbot.processor.chunks.extend(chunks)
                        rag_chatbot.processor.index.add(new_embeddings.astype('float32'))
                    
                    # Save updated index
                    rag_chatbot.processor.save_index()
                    rag_chatbot.is_initialized = True
                    
                    reply = f"데이터 파일 처리 완료: {uploaded_file.name}\n{len(chunks)}개 청크가 지식베이스에 추가되었습니다."
                except Exception as e:
                    reply = f"데이터 파일 업로드 완료: {uploaded_file.name}\n처리 중 오류: {str(e)}"
            else:
                reply = f"데이터 파일 업로드 완료: {uploaded_file.name} (RAG 처리 불가)"

            return JsonResponse({"reply": reply})
            
        except Exception as e:
            return JsonResponse({"error": f"파일 처리 중 오류: {str(e)}"}, status=500)

    return JsonResponse({"error": "파일이 없습니다."}, status=400)
