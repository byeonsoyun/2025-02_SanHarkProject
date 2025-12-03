import React, { useState, useEffect, useRef } from "react";
import { Container, Form, Button, Card, Badge, Spinner } from "react-bootstrap";

const Chatbot = () => {
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 메시지 전송
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage = inputText.trim();
    setInputText("");
    setMessages(prev => [...prev, { 
      sender: "user", 
      text: userMessage,
      timestamp: new Date()
    }]);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/message/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMessage,
          session_id: sessionId,
          user_id: "guest"
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMessages(prev => [...prev, { 
        sender: "bot", 
        text: data.reply,
        timestamp: new Date()
      }]);
    } catch (err) {
      console.error("Error:", err);
      setMessages(prev => [...prev, { 
        sender: "bot", 
        text: "죄송합니다. 서버와 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.",
        isError: true,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // 엔터로 전송
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // 채팅 초기화
  const handleClear = async () => {
    if (window.confirm("채팅 기록을 삭제하시겠습니까?")) {
      try {
        await fetch("http://localhost:8000/api/clear/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId }),
        });
        setMessages([]);
      } catch (err) {
        console.error("Clear error:", err);
      }
    }
  };

  // URL을 클릭 가능한 링크로 변환하는 함수
  const convertUrlsToLinks = (text) => {
    // <br> 태그 제거
    text = text.replace(/<br\s*\/?>/gi, '\n');
    
    // URL 패턴 매칭 (세션 ID 포함)
    const urlRegex = /(https?:\/\/[^\s)]+)/g;
    const parts = text.split(urlRegex);
    
    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        // URL에서 세션 ID만 제거 (쿼리 파라미터는 유지)
        let cleanUrl = part.replace(/;JSESSIONID=[A-Z0-9]+\?/g, '?');
        return (
          <a 
            key={index} 
            href={cleanUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: '#0066cc', textDecoration: 'underline', wordBreak: 'break-all' }}
          >
            {cleanUrl}
          </a>
        );
      }
      return part;
    });
  };

  return (
    <Container className="mt-4" style={{ maxWidth: "800px" }}>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2>💬 충북대 공지사항 챗봇</h2>
        <Button variant="outline-danger" size="sm" onClick={handleClear}>
          채팅 초기화
        </Button>
      </div>

      {/* 안내 메시지 */}
      {messages.length === 0 && (
        <Card className="mb-3 bg-light">
          <Card.Body>
            <Card.Title>👋 환영합니다!</Card.Title>
            <Card.Text>
              충북대학교 공지사항에 대해 무엇이든 물어보세요.
            </Card.Text>
            <div className="mt-2">
              <small className="text-muted">예시:</small>
              <ul className="mt-2 mb-0">
                <li><small>"기숙사 신청 방법 알려줘"</small></li>
                <li><small>"소프트웨어학과 졸업요건은 뭐야?"</small></li>
                <li><small>"장학금 관련 공지 찾아줘"</small></li>
              </ul>
            </div>
          </Card.Body>
        </Card>
      )}

      {/* 메시지 영역 */}
      <Card style={{ height: "500px", overflowY: "auto" }} className="mb-3">
        <Card.Body>
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`d-flex mb-3 ${msg.sender === "user" ? "justify-content-end" : "justify-content-start"}`}
            >
              <div style={{ maxWidth: "75%" }}>
                <div
                  className={`p-3 rounded ${
                    msg.sender === "user" 
                      ? "bg-primary text-white" 
                      : msg.isError 
                        ? "bg-danger text-white"
                        : "bg-light"
                  }`}
                  style={{ whiteSpace: "pre-wrap" }}
                >
                  {msg.sender === "bot" && !msg.isError 
                    ? convertUrlsToLinks(msg.text)
                    : msg.text
                  }
                </div>
                <div className="mt-1">
                  <small className="text-muted">
                    {msg.timestamp?.toLocaleTimeString('ko-KR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </small>
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="d-flex justify-content-start mb-3">
              <div className="bg-light p-3 rounded">
                <Spinner animation="border" size="sm" className="me-2" />
                답변 생성 중...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </Card.Body>
      </Card>

      {/* 입력 영역 */}
      <Form onSubmit={handleSubmit}>
        <div className="d-flex gap-2">
          <Form.Control
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="질문을 입력하세요... (Shift+Enter: 줄바꿈)"
            disabled={isLoading}
            as="textarea"
            rows={2}
            style={{ resize: "none" }}
          />
          <Button 
            type="submit" 
            variant="primary" 
            disabled={!inputText.trim() || isLoading}
            style={{ minWidth: "80px" }}
          >
            {isLoading ? <Spinner animation="border" size="sm" /> : "전송"}
          </Button>
        </div>
      </Form>

      <div className="mt-2 text-center">
        <small className="text-muted">
          💡 AI가 공지사항을 검색하고 분석하여 답변합니다.
        </small>
      </div>
    </Container>
  );
};

export default Chatbot;
