import React, { useState, useEffect } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import './CalendarPage.css';
import { useTheme } from '../App';

function CalendarPage() {
  const { theme } = useTheme();
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedEvents, setSelectedEvents] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [googleConnected, setGoogleConnected] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [newEvent, setNewEvent] = useState({
    title: '',
    start_date: '',
    end_date: '',
    description: ''
  });

  useEffect(() => {
    fetchEvents();
    checkGoogleConnection();
    
    // 5초마다 일정 새로고침
    const interval = setInterval(fetchEvents, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkGoogleConnection = async () => {
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const response = await fetch(`http://localhost:8000/api/calendar/google/status/?user_id=${userId}`);
      const data = await response.json();
      setGoogleConnected(data.connected);
    } catch (error) {
      console.error('구글 연동 상태 확인 실패:', error);
    }
  };

  const handleGoogleAuth = async () => {
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const response = await fetch(`http://localhost:8000/api/calendar/google/auth/?user_id=${userId}`);
      const data = await response.json();
      window.location.href = data.auth_url;
    } catch (error) {
      console.error('구글 인증 실패:', error);
    }
  };

  const handleGoogleDisconnect = async () => {
    if (!window.confirm('구글 캘린더 연동을 해제하시겠습니까?')) {
      return;
    }
    
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const response = await fetch(`http://localhost:8000/api/calendar/google/disconnect/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      
      if (response.ok) {
        setGoogleConnected(false);
        alert('구글 캘린더 연동이 해제되었습니다.');
      }
    } catch (error) {
      console.error('구글 연동 해제 실패:', error);
    }
  };

  const handleSyncToGoogle = async (eventId) => {
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const response = await fetch(`http://localhost:8000/api/calendar/user-events/${eventId}/sync-google/?user_id=${userId}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (response.ok) {
        alert(data.message);
        fetchEvents(); // 일정 새로고침
      } else {
        alert(data.error || '구글 캘린더 동기화에 실패했습니다.');
      }
    } catch (error) {
      console.error('구글 동기화 실패:', error);
      alert('구글 캘린더 동기화 중 오류가 발생했습니다.');
    }
  };

  const handleEditEvent = async (eventId, updatedData) => {
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const response = await fetch(`http://localhost:8000/api/calendar/user-events/${eventId}/?user_id=${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          title: updatedData.title, 
          description: updatedData.description 
        })
      });
      
      if (response.ok) {
        setEditingEvent(null);
        fetchEvents();
      }
    } catch (error) {
      console.error('일정 수정 실패:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const response = await fetch(`http://localhost:8000/api/calendar/events/?user_id=${userId}`);
      const data = await response.json();
      setEvents(data.events || []);
    } catch (error) {
      console.error('일정 로드 실패:', error);
    }
  };

  const handleAddEvent = async (e) => {
    e.preventDefault();
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const response = await fetch('http://localhost:8000/api/calendar/user-events/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newEvent, user_id: userId })
      });
      
      if (response.ok) {
        setNewEvent({ title: '', start_date: '', end_date: '', description: '' });
        setShowAddForm(false);
        fetchEvents();
      }
    } catch (error) {
      console.error('일정 추가 실패:', error);
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!eventId || !eventId.startsWith('user_')) return;
    
    try {
      const userId = localStorage.getItem('user_id') || 'guest';
      const id = eventId.replace('user_', '');
      const response = await fetch(`http://localhost:8000/api/calendar/user-events/${id}/?user_id=${userId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        fetchEvents();
        setSelectedEvents(selectedEvents.filter(e => e.id !== eventId));
      }
    } catch (error) {
      console.error('일정 삭제 실패:', error);
    }
  };

  const handleDateChange = (date) => {
    setSelectedDate(date);
    
    // 로컬 날짜 문자열로 변환 (시간대 문제 해결)
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;
    
    const dayEvents = events.filter(event => 
      event && event.start && event.start.startsWith(dateStr)
    );
    setSelectedEvents(dayEvents);
  };

  const tileContent = ({ date }) => {
    // 로컬 날짜 문자열로 변환 (시간대 문제 해결)
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;
    
    const dayEvents = events.filter(event => 
      event && event.start && event.start.startsWith(dateStr)
    );
    
    if (dayEvents.length > 0) {
      return <div className="event-dot"></div>;
    }
    return null;
  };

  const bgColor = theme === 'dark' ? '#1a1a1a' : '#ffffff';
  const cardBg = theme === 'dark' ? '#2d2d2d' : '#f8f8f8';
  const textColor = theme === 'dark' ? '#e0e0e0' : '#1a1a1a';
  const cbnu_red = '#C8102E';

  return (
    <div className="calendar-page" style={{ backgroundColor: bgColor, color: textColor, minHeight: '100vh', padding: '20px' }}>
      <div className="calendar-header" style={{ marginBottom: '20px' }}>
        <h1 style={{ color: cbnu_red }}>📅 캘린더</h1>
        <div className="header-buttons">
          {!googleConnected ? (
            <button className="google-sync-btn" onClick={handleGoogleAuth} style={{ backgroundColor: cbnu_red, color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer', marginRight: '10px' }}>
              🔗 구글 캘린더 연동
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <span className="google-connected" style={{ color: cbnu_red }}>✅ 구글 캘린더 연동됨</span>
              <button className="google-disconnect-btn" onClick={handleGoogleDisconnect} style={{ backgroundColor: '#666', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.9em' }}>
                연동 해제
              </button>
            </div>
          )}
          <button className="add-event-btn" onClick={() => setShowAddForm(!showAddForm)} style={{ backgroundColor: cbnu_red, color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer' }}>
            ➕ 일정 추가
          </button>
        </div>
      </div>

      {showAddForm && (
        <div className="add-event-form" style={{ backgroundColor: cardBg, padding: '20px', borderRadius: '10px', marginBottom: '20px' }}>
          <h3 style={{ color: cbnu_red }}>개인 일정 추가</h3>
          <form onSubmit={handleAddEvent}>
            <input
              type="text"
              placeholder="일정 제목"
              value={newEvent.title}
              onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
              required
              style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor }}
            />
            <input
              type="date"
              value={newEvent.start_date}
              onChange={(e) => setNewEvent({...newEvent, start_date: e.target.value})}
              required
              style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor }}
            />
            <input
              type="date"
              placeholder="종료일 (선택)"
              value={newEvent.end_date}
              onChange={(e) => setNewEvent({...newEvent, end_date: e.target.value})}
              style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor }}
            />
            <textarea
              placeholder="설명 (선택)"
              value={newEvent.description}
              onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
              style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor, minHeight: '80px' }}
            />
            <div className="form-buttons">
              <button type="submit" style={{ backgroundColor: cbnu_red, color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer', marginRight: '10px' }}>추가</button>
              <button type="button" onClick={() => setShowAddForm(false)} style={{ backgroundColor: '#666', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer' }}>취소</button>
            </div>
          </form>
        </div>
      )}

      <div className="calendar-container" style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
        <div className="calendar-wrapper" style={{ flex: '1', minWidth: '300px', backgroundColor: cardBg, padding: '20px', borderRadius: '10px' }}>
          <Calendar
            onChange={handleDateChange}
            value={selectedDate}
            tileContent={tileContent}
            locale="ko-KR"
          />
        </div>

        <div className="events-list" style={{ flex: '1', minWidth: '300px', backgroundColor: cardBg, padding: '20px', borderRadius: '10px' }}>
          <h2 style={{ color: cbnu_red }}>{selectedDate.toLocaleDateString('ko-KR')} 일정</h2>
          {selectedEvents.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {selectedEvents.map(event => (
                <li key={event.id} className="event-item" style={{ backgroundColor: theme === 'dark' ? '#3a3a3a' : '#fff', padding: '15px', marginBottom: '10px', borderRadius: '8px', borderLeft: `4px solid ${cbnu_red}` }}>
                  {event.type === 'personal' && editingEvent === event.id ? (
                    <div>
                      <input
                        type="text"
                        value={newEvent.title}
                        onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
                        style={{ width: '100%', padding: '8px', marginBottom: '8px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor }}
                      />
                      <textarea
                        value={newEvent.description}
                        onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
                        style={{ width: '100%', padding: '8px', marginBottom: '8px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor, minHeight: '60px' }}
                      />
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button type="button" onClick={() => handleEditEvent(event.id.replace('user_', ''), newEvent)} style={{ backgroundColor: cbnu_red, color: '#fff', border: 'none', padding: '5px 12px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.85em' }}>저장</button>
                        <button type="button" onClick={() => setEditingEvent(null)} style={{ backgroundColor: '#666', color: '#fff', border: 'none', padding: '5px 12px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.85em' }}>취소</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="event-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <h3 style={{ margin: 0 }}>{event.title}</h3>
                        {event.type === 'personal' && (
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button 
                              onClick={() => handleSyncToGoogle(event.id.replace('user_', ''))}
                              disabled={!googleConnected}
                              style={{ 
                                backgroundColor: googleConnected ? '#4285f4' : '#ccc', 
                                color: '#fff', 
                                border: 'none', 
                                padding: '5px 10px', 
                                borderRadius: '5px', 
                                cursor: googleConnected ? 'pointer' : 'not-allowed', 
                                fontSize: '0.85em',
                                opacity: googleConnected ? 1 : 0.6
                              }}
                            >
                              Google
                            </button>
                            <button 
                              onClick={() => {
                                setEditingEvent(event.id);
                                setNewEvent({ title: event.title, description: event.description });
                              }}
                              style={{ backgroundColor: '#ffc107', color: '#000', border: 'none', padding: '5px 10px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.85em' }}
                            >
                              수정
                            </button>
                            <button 
                              onClick={() => handleDeleteEvent(event.id)}
                              style={{ backgroundColor: 'transparent', border: 'none', color: cbnu_red, cursor: 'pointer', fontSize: '1.2em' }}
                            >
                              🗑️
                            </button>
                          </div>
                        )}
                      </div>
                      <p>{event.description}</p>
                      {event.url && (
                        <a href={event.url} target="_blank" rel="noopener noreferrer">
                          자세히 보기 →
                        </a>
                      )}
                    </>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="no-events">이 날짜에 일정이 없습니다.</p>
          )}
        </div>
      </div>

      <div className="all-events">
        <h2>전체 일정 ({events.length}개)</h2>
        <div className="events-grid">
          {events.map(event => (
            <div key={event.id} className={`event-card ${event.type}`}>
              {editingEvent === event.id ? (
                <div>
                  <input
                    type="text"
                    value={newEvent.title}
                    onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
                    style={{ width: '100%', padding: '8px', marginBottom: '8px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor }}
                  />
                  <textarea
                    value={newEvent.description}
                    onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
                    style={{ width: '100%', padding: '8px', marginBottom: '8px', borderRadius: '5px', border: '1px solid #ddd', backgroundColor: bgColor, color: textColor, minHeight: '60px' }}
                  />
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button type="button" onClick={() => handleEditEvent(event.id.replace('user_', ''), newEvent)} style={{ backgroundColor: cbnu_red, color: '#fff', border: 'none', padding: '5px 12px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.85em' }}>저장</button>
                    <button type="button" onClick={() => setEditingEvent(null)} style={{ backgroundColor: '#666', color: '#fff', border: 'none', padding: '5px 12px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.85em' }}>취소</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="event-date">
                    {new Date(event.start).toLocaleDateString('ko-KR', {
                      month: 'long',
                      day: 'numeric'
                    })}
                  </div>
                  {event.type === 'academic' && (
                    <span className={`event-badge ${event.type}`}>학사</span>
                  )}
                  <h3>{event.title}</h3>
                  <p>{event.description}</p>
                  {event.type === 'personal' && (
                    <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                      <button 
                        onClick={() => handleSyncToGoogle(event.id.replace('user_', ''))}
                        disabled={!googleConnected}
                        style={{ 
                          backgroundColor: googleConnected ? '#4285f4' : '#ccc', 
                          color: '#fff', 
                          border: 'none', 
                          padding: '5px 12px', 
                          borderRadius: '5px', 
                          cursor: googleConnected ? 'pointer' : 'not-allowed', 
                          fontSize: '0.85em',
                          opacity: googleConnected ? 1 : 0.6
                        }}
                      >
                        Google
                      </button>
                      <button 
                        onClick={() => {
                          setEditingEvent(event.id);
                          setNewEvent({ title: event.title, description: event.description });
                        }}
                        style={{ backgroundColor: '#ffc107', color: '#000', border: 'none', padding: '5px 12px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.85em' }}
                      >
                        수정
                      </button>
                      <button 
                        onClick={() => handleDeleteEvent(event.id)}
                        style={{ backgroundColor: '#dc3545', color: '#fff', border: 'none', padding: '5px 12px', borderRadius: '5px', cursor: 'pointer', fontSize: '0.85em' }}
                      >
                        삭제
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CalendarPage;
