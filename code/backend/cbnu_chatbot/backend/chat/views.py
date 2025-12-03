import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatMessage, ChbNotice
from .services import RAGService
import requests
from django.conf import settings

# RAG 서비스 싱글톤 인스턴스
rag_service = RAGService()

@csrf_exempt
def chat_message(request):
    """채팅 메시지 처리 (복잡도 감지 + RAG)"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            session_id = data.get("session_id", "ANONYMOUS")
            user_id = data.get("user_id", "guest")
            
            if not message.strip():
                return JsonResponse({"error": "Empty message"}, status=400)
            
            print(f"\n{'='*60}")
            print(f"📩 새 질문: {message}")
            print(f"   세션: {session_id}, 사용자: {user_id}")
            print(f"{'='*60}")
            
            # 사용자 메시지 저장
            ChatMessage.objects.create(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=message
            )
            
            # 최근 대화 기록 가져오기 (맥락 유지)
            recent_chats = ChatMessage.objects.filter(
                session_id=session_id
            ).order_by('-timestamp')[:10]
            
            # 항상 LLM 사용 (라우팅 제거)
            print("🤖 LLM 분석 모드 (항상 사용)")
            result = rag_service.generate_answer(message, recent_chats)
            reply = result.get("answer", "답변 생성 실패")
            search_results = result.get("sources", [])
            
            # 챗봇 응답 저장
            ChatMessage.objects.create(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=reply
            )
            
            print(f"\n✅ 응답 완료 (길이: {len(reply)}자)")
            
            return JsonResponse({
                "reply": reply,
                "results_count": len(search_results)
            })
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST method required"}, status=405)


@csrf_exempt
def get_chat_history(request):
    """채팅 기록 조회"""
    if request.method == "GET":
        session_id = request.GET.get("session_id", "ANONYMOUS")
        
        messages = ChatMessage.objects.filter(
            session_id=session_id
        ).order_by('timestamp').values('role', 'content', 'timestamp')
        
        return JsonResponse({
            "messages": list(messages)
        })
    
    return JsonResponse({"error": "GET method required"}, status=405)


@csrf_exempt
def clear_chat_history(request):
    """채팅 기록 삭제"""
    if request.method == "POST":
        data = json.loads(request.body)
        session_id = data.get("session_id", "ANONYMOUS")
        
        deleted_count, _ = ChatMessage.objects.filter(
            session_id=session_id
        ).delete()
        
        return JsonResponse({
            "message": f"{deleted_count}개의 메시지가 삭제되었습니다."
        })
    
    return JsonResponse({"error": "POST method required"}, status=405)


@csrf_exempt
def get_calendar_events(request):
    """학사일정 캘린더 이벤트 반환"""
    if request.method == "GET":
        try:
            # 학사일정 가져오기
            schedules = ChbNotice.objects.filter(board_type='학사일정').order_by('post_date')
            
            events = []
            for schedule in schedules:
                # 제목에서 월 정보 추출
                title = schedule.title.replace('[', '').replace(']', '')
                
                events.append({
                    'id': schedule.notice_id,
                    'title': title,
                    'start': schedule.post_date.isoformat(),
                    'description': schedule.content[:200],
                    'url': schedule.source_url,
                    'type': 'schedule'
                })
            
            return JsonResponse({'events': events})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "GET method required"}, status=405)


@csrf_exempt
def extract_event_from_notice(request):
    """공지사항에서 일정 정보 추출"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            notice_id = data.get("notice_id")
            
            if not notice_id:
                return JsonResponse({"error": "notice_id required"}, status=400)
            
            # 공지사항 가져오기
            notice = ChbNotice.objects.get(notice_id=notice_id)
            
            # LLM에게 일정 정보 추출 요청
            prompt = f"""다음 공지사항에서 일정 정보를 추출해주세요.

제목: {notice.title}
내용: {notice.content}

다음 형식의 JSON으로 답변해주세요:
{{
  "title": "일정 제목",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "description": "간단한 설명"
}}

날짜가 명확하지 않으면 null로 표시하세요."""

            # LLM 호출
            response = requests.post(
                f"{settings.LLM_API_URL}",
                json={
                    "model": settings.LLM_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                llm_response = response.json().get('response', '')
                
                # JSON 추출 시도
                try:
                    import re
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        event_data = json.loads(json_match.group())
                        event_data['notice_id'] = notice_id
                        event_data['url'] = notice.source_url
                        return JsonResponse(event_data)
                except:
                    pass
                
                return JsonResponse({
                    "title": notice.title,
                    "start_date": notice.post_date.isoformat(),
                    "end_date": notice.post_date.isoformat(),
                    "description": notice.content[:200],
                    "notice_id": notice_id,
                    "url": notice.source_url
                })
            
            return JsonResponse({"error": "LLM 호출 실패"}, status=500)
            
        except ChbNotice.DoesNotExist:
            return JsonResponse({"error": "공지사항을 찾을 수 없습니다"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST method required"}, status=405)
