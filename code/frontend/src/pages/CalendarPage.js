import React, { useState, useEffect } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import './CalendarPage.css';

function CalendarPage() {
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedEvents, setSelectedEvents] = useState([]);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/calendar/events/');
      const data = await response.json();
      setEvents(data.events || []);
    } catch (error) {
      console.error('일정 로드 실패:', error);
    }
  };

  const handleDateChange = (date) => {
    setSelectedDate(date);
    
    const dateStr = date.toISOString().split('T')[0];
    const dayEvents = events.filter(event => 
      event.start.startsWith(dateStr)
    );
    setSelectedEvents(dayEvents);
  };

  const tileContent = ({ date }) => {
    const dateStr = date.toISOString().split('T')[0];
    const dayEvents = events.filter(event => 
      event.start.startsWith(dateStr)
    );
    
    if (dayEvents.length > 0) {
      return <div className="event-dot"></div>;
    }
    return null;
  };

  return (
    <div className="calendar-page">
      <div className="calendar-header">
        <h1>📅 학사일정</h1>
        <button onClick={() => window.location.href = '/'}>
          채팅으로 돌아가기
        </button>
      </div>

      <div className="calendar-container">
        <div className="calendar-wrapper">
          <Calendar
            onChange={handleDateChange}
            value={selectedDate}
            tileContent={tileContent}
            locale="ko-KR"
          />
        </div>

        <div className="events-list">
          <h2>{selectedDate.toLocaleDateString('ko-KR')} 일정</h2>
          {selectedEvents.length > 0 ? (
            <ul>
              {selectedEvents.map(event => (
                <li key={event.id} className="event-item">
                  <h3>{event.title}</h3>
                  <p>{event.description}</p>
                  {event.url && (
                    <a href={event.url} target="_blank" rel="noopener noreferrer">
                      자세히 보기 →
                    </a>
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
        <h2>전체 학사일정 ({events.length}개)</h2>
        <div className="events-grid">
          {events.map(event => (
            <div key={event.id} className="event-card">
              <div className="event-date">
                {new Date(event.start).toLocaleDateString('ko-KR', {
                  month: 'long',
                  day: 'numeric'
                })}
              </div>
              <h3>{event.title}</h3>
              <p>{event.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CalendarPage;
