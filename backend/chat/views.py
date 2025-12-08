import json
import re
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatMessage, UserEvent
from .services import RAGService
from .google_calendar_service import GoogleCalendarService

# RAG 서비스 인스턴스 생성
rag_service = RAGService()

# 일정 추가 키워드 (services.py와 동일하게)
event_keywords = ['일정 추가', '일정추가', '캘린더에 추가', '캘린더 추가', '일정 등록', '일정등록', '추가해줘', '추가해주세요', '넣어줘', '등록해줘']

@csrf_exempt
def chat_message(request):
    """채팅 메시지 처리"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            session_id = data.get("session_id", "anonymous")
            user_id = data.get("user_id", "anonymous")
            
            if not message.strip():
                return JsonResponse({"error": "Empty message"}, status=400)
            
            # 사용자 메시지 저장
            ChatMessage.objects.create(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=message
            )
            
            # 최근 대화 기록 가져오기
            recent_chats = ChatMessage.objects.filter(
                session_id=session_id
            ).order_by('-timestamp')[:10]
            
            # 일정 추가 요청 감지 및 처리 (더 정확한 패턴 매칙)
            event_added = False
            extracted_event_reply = None
            
            # 명시적인 일정 추가 키워드
            explicit_keywords = ['일정 추가', '일정추가', '캘린더에 추가', '캘린더 추가', '일정 등록', '일정등록', '스케줄 추가', '스케줄 등록']
            
            # 맥락적 키워드 (날짜 + 추가/등록/넣어줘)
            import re
            has_date = bool(re.search(r'\d{1,2}월\s*\d{1,2}일|\d{4}-\d{2}-\d{2}|내일|모레|다음주', message))
            contextual_keywords = ['추가해줘', '추가해주세요', '넣어줘', '등록해줘', '등록해주세요']
            
            # "이 일정 추가해줘" 같은 대명사 사용 감지
            pronoun_keywords = ['이 일정', '그 일정', '해당 일정', '위 일정']
            has_pronoun = any(keyword in message for keyword in pronoun_keywords)
            
            # 단순 질문 키워드 (이게 있으면 일정 추가 아님)
            question_keywords = ['언제', '몇시', '며칠', '무슨 날', '알려줘', '알려주세요', '뭐야', '뭐지']
            is_simple_question = any(keyword in message for keyword in question_keywords) and not has_pronoun
            
            is_event_add_request = (
                any(keyword in message for keyword in explicit_keywords) or
                (has_date and any(keyword in message for keyword in contextual_keywords) and not is_simple_question) or
                (has_pronoun and any(keyword in message for keyword in contextual_keywords))
            )
            
            # 대명사 기반 요청인 경우 이전 대화에서 일정 정보 추출
            if has_pronoun and any(kw in message for kw in contextual_keywords):
                # 최근 봇 응답에서 날짜 정보 추출
                last_bot_messages = ChatMessage.objects.filter(
                    session_id=session_id,
                    role='assistant'
                ).order_by('-timestamp')[:1]
                
                if last_bot_messages.exists():
                    bot_content = last_bot_messages.first().content
                    # 날짜 패턴 찾기
                    date_patterns = [
                        (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', 'full'),
                        (r'(\d{1,2})월\s*(\d{1,2})일', 'short'),
                    ]
                    
                    for pattern, ptype in date_patterns:
                        date_match = re.search(pattern, bot_content)
                        if date_match:
                            # 제목 추출
                            title_patterns = [
                                r'###?\s*([^\n]+)',
                                r'\*\*([^\*]+)\*\*',
                                r'([가-힣\w\s]+)\s*일정',
                            ]
                            title = "일정"
                            for tp in title_patterns:
                                title_match = re.search(tp, bot_content)
                                if title_match:
                                    title = title_match.group(1).strip()[:50]
                                    break
                            
                            # 날짜 파싱
                            try:
                                if ptype == 'full':
                                    year, month, day = date_match.groups()
                                else:  # short
                                    month, day = date_match.groups()
                                    year = datetime.now().year
                                
                                event_date = f"{year}-{int(month):02d}-{int(day):02d}"
                                
                                # 직접 일정 생성
                                user_event = UserEvent.objects.create(
                                    user_id=user_id,
                                    title=title,
                                    start_date=event_date,
                                    end_date=event_date,
                                    description=f"이전 대화에서 추출"
                                )
                                
                                event_added = True
                                extracted_event_reply = f"✅ '{title}' 일정이 {event_date}에 추가되었습니다."
                                break
                            except Exception as e:
                                print(f"대명사 기반 일정 추출 실패: {e}")
            
            # RAG 서비스로 답변 생성 (일정이 추출되지 않은 경우에만)
            if extracted_event_reply:
                reply = extracted_event_reply
                result = {"answer": reply, "sources": []}
            else:
                result = rag_service.generate_answer(message, recent_chats)
                reply = result.get("answer", "답변 생성 실패")
            
            if is_event_add_request and not event_added:
                event_match = re.search(r'\[EVENT_ADD\](.*?)\[/EVENT_ADD\]', reply, re.DOTALL)
                if event_match:
                    try:
                        event_data = json.loads(event_match.group(1))
                        
                        # 날짜 형식 검증 및 변환
                        start_date = event_data.get('start_date')
                        end_date = event_data.get('end_date', start_date)
                        
                        # YYYY-MM-DD 형식 검증
                        datetime.strptime(start_date, '%Y-%m-%d')
                        datetime.strptime(end_date, '%Y-%m-%d')
                        
                        # UserEvent 생성
                        user_event = UserEvent.objects.create(
                            user_id=user_id,
                            title=event_data.get('title'),
                            start_date=start_date,
                            end_date=end_date,
                            description=event_data.get('description', '')
                        )
                        
                        # 챗봇에서 추가한 일정은 구글 캘린더에 자동 동기화하지 않음
                        # 사용자가 캘린더 페이지에서 수동으로 "Google" 버튼을 눌러야 함
                        
                        event_added = True
                        # EVENT_ADD 태그 제거
                        reply = re.sub(r'\[EVENT_ADD\].*?\[/EVENT_ADD\]', '', reply, flags=re.DOTALL).strip()
                        reply += "\n\n✅ 일정이 캘린더에 추가되었습니다."
                        
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        print(f"일정 추가 실패: {e}")
                        reply = re.sub(r'\[EVENT_ADD\].*?\[/EVENT_ADD\]', '', reply, flags=re.DOTALL).strip()
                        reply += "\n\n❌ 일정 추가에 실패했습니다. 날짜 형식을 확인해주세요."
            else:
                # 일정 추가 요청이 아닌데 LLM이 태그를 생성했다면 제거
                reply = re.sub(r'\[EVENT_ADD\].*?\[/EVENT_ADD\]', '', reply, flags=re.DOTALL).strip()
            
            # 봇 응답 저장
            ChatMessage.objects.create(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=reply
            )
            
            return JsonResponse({
                "reply": {
                    "answer": reply,
                    "sources": result.get("sources", [])
                },
                "event_added": event_added
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Error in chat_message: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST method required"}, status=400)


@csrf_exempt
def get_events(request):
    """사용자 일정 및 학사일정 조회"""
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id", "anonymous")
            start_date = request.GET.get("start_date")
            end_date = request.GET.get("end_date")
            
            # 사용자 개인 일정
            user_events = UserEvent.objects.filter(user_id=user_id)
            
            if start_date:
                user_events = user_events.filter(start_date__gte=start_date)
            if end_date:
                user_events = user_events.filter(end_date__lte=end_date)
            
            events_list = []
            
            # 개인 일정 추가
            for event in user_events:
                events_list.append({
                    "id": f"user_{event.id}",
                    "title": event.title,
                    "start": event.start_date.strftime('%Y-%m-%d'),
                    "end": event.end_date.strftime('%Y-%m-%d') if event.end_date else event.start_date.strftime('%Y-%m-%d'),
                    "description": event.description,
                    "type": "personal",
                    "url": None
                })
            
            # 학사일정 추가 (ChbNotice에서 가져오기)
            from .models import ChbNotice
            academic_events = ChbNotice.objects.filter(board_type='학사일정')
            
            for event in academic_events:
                # 날짜 파싱 (content에서 추출)
                import re
                date_match = re.search(r'일시:\s*(\d{2})\.(\d{2})', event.content)
                if date_match:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    
                    # 학년도 추출 (없으면 post_date 기반으로 계산)
                    year_match = re.search(r'학년도:\s*(\d{4})학년도', event.content)
                    if year_match:
                        academic_year = int(year_match.group(1))
                        # 실제 연도 계산
                        if month in [1, 2]:
                            year = academic_year + 1
                        else:
                            year = academic_year
                    else:
                        # 학년도 정보 없으면 post_date 사용
                        year = event.post_date.year
                        # 월이 post_date보다 작으면 다음 해
                        if month < event.post_date.month:
                            year += 1
                    
                    try:
                        event_date = datetime(year, month, day).strftime('%Y-%m-%d')
                        
                        # 제목에서 [월] 제거하고 이벤트명만 추출
                        title = re.sub(r'\[\d+월\]\s*', '', event.title)
                        
                        events_list.append({
                            "id": f"academic_{event.notice_id}",
                            "title": title,
                            "start": event_date,
                            "end": event_date,
                            "description": event.content,
                            "type": "academic",
                            "url": event.source_url
                        })
                    except ValueError as e:
                        print(f"날짜 파싱 오류: {event.title}, {year}-{month}-{day}, {e}")
                        continue
            
            return JsonResponse({"events": events_list})
            
        except Exception as e:
            print(f"Error in get_events: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "GET method required"}, status=400)


@csrf_exempt
def add_event(request):
    """일정 추가 (로컬에만 저장, 구글 연동은 수동)"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id", "anonymous")
            
            start_date_str = data.get("start_date")
            end_date_str = data.get("end_date", start_date_str)
            
            # 문자열을 date 객체로 변환
            start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # UserEvent 생성 (구글 연동 없이)
            event = UserEvent.objects.create(
                user_id=user_id,
                title=data.get("title"),
                start_date=start_date_obj,
                end_date=end_date_obj,
                description=data.get("description", "")
            )
            
            return JsonResponse({
                "success": True,
                "event": {
                    "id": event.id,
                    "title": event.title,
                    "start_date": event.start_date.strftime('%Y-%m-%d'),
                    "end_date": event.end_date.strftime('%Y-%m-%d') if event.end_date else None
                }
            })
        except Exception as e:
            print(f"Error adding event: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST method required"}, status=400)


@csrf_exempt
def delete_event(request, event_id):
    """일정 삭제 및 수정"""
    if request.method == "DELETE":
        try:
            user_id = request.GET.get("user_id", "anonymous")
            event = UserEvent.objects.get(id=event_id, user_id=user_id)
            
            # Google Calendar에서도 삭제 시도
            if event.google_event_id:
                try:
                    calendar_service = GoogleCalendarService()
                    calendar_service.delete_event(user_id, event.google_event_id)
                except Exception as cal_error:
                    print(f"Google Calendar 삭제 실패: {cal_error}")
            
            event.delete()
            
            return JsonResponse({"success": True, "message": "일정이 삭제되었습니다."})
            
        except UserEvent.DoesNotExist:
            return JsonResponse({"error": "Event not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    elif request.method == "PUT":
        try:
            user_id = request.GET.get("user_id", "anonymous")
            event = UserEvent.objects.get(id=event_id, user_id=user_id)
            
            data = json.loads(request.body)
            event.title = data.get("title", event.title)
            event.description = data.get("description", event.description)
            event.save()
            
            return JsonResponse({"success": True, "message": "일정이 수정되었습니다."})
            
        except UserEvent.DoesNotExist:
            return JsonResponse({"error": "Event not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "DELETE or PUT method required"}, status=400)


@csrf_exempt
def google_status(request):
    """구글 캘린더 연동 상태 확인"""
    user_id = request.GET.get("user_id", "anonymous")
    
    try:
        from .models import GoogleCalendarToken
        token_exists = GoogleCalendarToken.objects.filter(user_id=user_id).exists()
        return JsonResponse({"connected": token_exists})
    except Exception as e:
        print(f"Error checking Google status: {e}")
        return JsonResponse({"connected": False})


@csrf_exempt
def google_auth(request):
    """구글 캘린더 인증 URL 생성"""
    user_id = request.GET.get("user_id", "anonymous")
    
    try:
        auth_url = GoogleCalendarService.get_auth_url(user_id)
        return JsonResponse({"auth_url": auth_url})
    except Exception as e:
        print(f"Error generating auth URL: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def google_callback(request):
    """구글 캘린더 OAuth 콜백 처리"""
    code = request.GET.get("code")
    state = request.GET.get("state")  # user_id
    
    if not code or not state:
        return JsonResponse({"error": "Missing code or state"}, status=400)
    
    try:
        GoogleCalendarService.handle_callback(code, state)
        # 프론트엔드로 리다이렉트
        from django.shortcuts import redirect
        return redirect('http://localhost:3000/calendar?google_connected=true')
    except Exception as e:
        print(f"Error in Google callback: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def google_disconnect(request):
    """구글 캘린더 연동 해제"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id", "anonymous")
            
            from .models import GoogleCalendarToken
            GoogleCalendarToken.objects.filter(user_id=user_id).delete()
            
            return JsonResponse({"success": True, "message": "구글 캘린더 연동이 해제되었습니다."})
        except Exception as e:
            print(f"Error disconnecting Google Calendar: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST method required"}, status=400)


@csrf_exempt
def sync_to_google(request, event_id):
    """특정 일정을 구글 캘린더에 동기화"""
    if request.method == "POST":
        try:
            user_id = request.GET.get("user_id", "anonymous")
            
            # 일정 가져오기
            event = UserEvent.objects.get(id=event_id, user_id=user_id)
            
            # 이미 동기화된 경우
            if event.google_event_id:
                return JsonResponse({"success": True, "message": "이미 구글 캘린더에 동기화되어 있습니다."})
            
            # 구글 캘린더에 추가
            google_event_id = GoogleCalendarService.create_event(
                user_id=user_id,
                title=event.title,
                start_date=event.start_date,
                end_date=event.end_date,
                description=event.description
            )
            
            if google_event_id:
                event.google_event_id = google_event_id
                event.save()
                return JsonResponse({"success": True, "message": "구글 캘린더에 동기화되었습니다."})
            else:
                return JsonResponse({"error": "구글 캘린더 연동이 필요합니다."}, status=400)
                
        except UserEvent.DoesNotExist:
            return JsonResponse({"error": "일정을 찾을 수 없습니다."}, status=404)
        except Exception as e:
            print(f"Error syncing to Google: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST method required"}, status=400)
