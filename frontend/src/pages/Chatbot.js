import React, { useState, useRef, useCallback } from "react";
import { useTheme } from "../App";

const Chatbot = () => {
  const { theme, toggleTheme } = useTheme();
  const messagesEndRef = useRef(null);
  
  const [chats, setChats] = useState(() => {
    const saved = localStorage.getItem('chatSessions');
    return saved ? JSON.parse(saved) : [
      { 
        id: 1, 
        name: "New Chatting", 
        sessionId: `session_${Date.now()}`, 
        messages: [{ sender: 'bot', text: "안녕하세요! 궁금하신 게 있을까요?" }]
      }
    ];
  });
  const [currentChatId, setCurrentChatId] = useState(() => {
    const saved = localStorage.getItem('currentChatId');
    return saved ? parseInt(saved) : 1;
  });
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingName, setEditingName] = useState("");

  // chats 변경 시 localStorage에 저장
  React.useEffect(() => {
    localStorage.setItem('chatSessions', JSON.stringify(chats));
  }, [chats]);

  // currentChatId 변경 시 localStorage에 저장
  React.useEffect(() => {
    localStorage.setItem('currentChatId', currentChatId.toString());
  }, [currentChatId]);

  const currentChat = chats.find(c => c.id === currentChatId);
  const messages = currentChat?.messages || [];

  const scrollToBottom = useCallback(() => {
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 0);
  }, []);

  const updateMessages = useCallback((message) => {
    setChats(prev => prev.map(chat => 
      chat.id === currentChatId ? { ...chat, messages: [...chat.messages, message] } : chat
    ));
    scrollToBottom();
  }, [currentChatId, scrollToBottom]);

  const handleDeleteChat = useCallback((chatId, e) => {
    e.stopPropagation();
    if (chats.length === 1) {
      alert("마지막 채팅은 삭제할 수 없습니다.");
      return;
    }
    setChats(prev => prev.filter(c => c.id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(chats.find(c => c.id !== chatId).id);
    }
  }, [chats, currentChatId]);

  const handleCreateNewChat = useCallback(() => {
    const chatNames = chats.map(c => c.name);
    let newChatName = "New Chatting";
    let index = 0;
    while (chatNames.includes(newChatName)) {
      index++;
      newChatName = `New Chatting(${index})`;
    }
    const newChat = {
      id: Date.now(),
      name: newChatName,
      sessionId: `session_${Date.now()}`,
      messages: [{ sender: 'bot', text: "안녕하세요! 궁금하신 게 있을까요?" }]
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setInputText("");
    scrollToBottom();
  }, [chats, scrollToBottom]);

  const handleSelectChat = useCallback((id) => {
    setCurrentChatId(id);
    setInputText("");
    scrollToBottom();
  }, [scrollToBottom]);

  const handleRenameChat = useCallback((chatId, newName) => {
    if (newName.trim()) {
      setChats(prev => prev.map(chat => 
        chat.id === chatId ? { ...chat, name: newName.trim() } : chat
      ));
    }
    setEditingChatId(null);
    setEditingName("");
  }, []);

  const handleSubmit = async (e) => {
    if(e) e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage = inputText.trim();
    setInputText("");
    updateMessages({ sender: "user", text: userMessage, timestamp: new Date() });
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat/message/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMessage,
          session_id: currentChat?.sessionId,
          user_id: "guest"
        }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      const botMessage = { 
        sender: "bot", 
        text: data.reply?.answer || data.reply || "응답을 받지 못했습니다.",
        timestamp: new Date(),
        eventAdded: data.event_added
      };
      updateMessages(botMessage);
    } catch (err) {
      console.error("Error:", err);
      updateMessages({ 
        sender: "bot", 
        text: "죄송합니다. 서버와 연결할 수 없습니다.",
        isError: true,
        timestamp: new Date()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = e => {
    if (e.key === "Enter" && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const formatBotMessage = (text) => {
    if (typeof text !== 'string') return text;
    text = text.replace(/<br\s*\/?>/gi, '\n');
    text = text.replace(/<답변>/gi, '');
    text = text.replace(/<출처>/gi, '\n📌 출처:');
    text = text.replace(/<strong>/gi, '');
    text = text.replace(/<\/strong>/gi, '');
    return text;
  };

  const convertUrlsToLinks = (text) => {
    if (typeof text !== 'string') return text;
    text = formatBotMessage(text);
    const urlRegex = /(https?:\/\/[^\s)]+)/g;
    const parts = text.split(urlRegex);
    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        let cleanUrl = part.replace(/;JSESSIONID=[A-Z0-9]+\?/g, '?');
        return (
          <a 
            key={index} 
            href={cleanUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: theme === 'dark' ? '#69b5ff' : '#0066cc', textDecoration: 'underline', wordBreak: 'break-all' }}
          >
            {cleanUrl}
          </a>
        );
      }
      return part;
    });
  };

  const bgColor = theme === 'dark' ? '#1a1a1a' : '#f5f5f5';
  const cardBg = theme === 'dark' ? '#2d2d2d' : '#ffffff';
  const textColor = theme === 'dark' ? '#e0e0e0' : '#333333';
  const borderColor = theme === 'dark' ? '#444444' : '#dddddd';
  const userBubbleBg = theme === 'dark' ? '#0084ff' : '#DCF8C6';
  const botBubbleBg = theme === 'dark' ? '#3a3a3a' : '#eeeeee';

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 56px)', backgroundColor: bgColor }}>
      
      {showSidebar && (
        <div style={{ 
          width: '250px', 
          backgroundColor: cardBg, 
          borderRight: `1px solid ${borderColor}`,
          display: 'flex',
          flexDirection: 'column',
          padding: '10px'
        }}>
          <button 
            onClick={handleCreateNewChat}
            style={{
              padding: '10px',
              marginBottom: '10px',
              backgroundColor: theme === 'dark' ? '#0084ff' : '#4CAF50',
              color: '#fff',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            + 새 채팅
          </button>

          <button 
            onClick={toggleTheme}
            style={{
              padding: '10px',
              marginBottom: '10px',
              backgroundColor: theme === 'dark' ? '#555' : '#ddd',
              color: textColor,
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            {theme === 'dark' ? '☀️ 라이트 모드' : '🌙 다크 모드'}
          </button>
          
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {chats.map(chat => (
              <div
                key={chat.id}
                onClick={() => handleSelectChat(chat.id)}
                style={{
                  padding: '10px',
                  marginBottom: '5px',
                  backgroundColor: chat.id === currentChatId ? (theme === 'dark' ? '#444' : '#e0e0e0') : 'transparent',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  color: textColor,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                {editingChatId === chat.id ? (
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onBlur={() => handleRenameChat(chat.id, editingName)}
                    onKeyPress={(e) => e.key === 'Enter' && handleRenameChat(chat.id, editingName)}
                    onClick={(e) => e.stopPropagation()}
                    autoFocus
                    style={{
                      flex: 1,
                      padding: '5px',
                      backgroundColor: theme === 'dark' ? '#555' : '#fff',
                      color: textColor,
                      border: '1px solid #ccc',
                      borderRadius: '3px'
                    }}
                  />
                ) : (
                  <span onDoubleClick={(e) => {
                    e.stopPropagation();
                    setEditingChatId(chat.id);
                    setEditingName(chat.name);
                  }}>{chat.name}</span>
                )}
                <button
                  onClick={(e) => handleDeleteChat(chat.id, e)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#ff4444',
                    cursor: 'pointer',
                    fontSize: '16px',
                    padding: '0 5px'
                  }}
                  title="삭제"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', maxWidth: '800px', margin: '0 auto', width: '100%' }}>
        
        <div style={{ 
          padding: '10px 20px', 
          backgroundColor: cardBg, 
          borderBottom: `1px solid ${borderColor}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <button 
            onClick={() => setShowSidebar(!showSidebar)}
            style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: textColor }}
          >
            ☰
          </button>
          <h3 style={{ margin: 0, color: textColor }}>💬 소왕이</h3>
          <div style={{ width: '40px' }}></div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', backgroundColor: bgColor }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ textAlign: msg.sender === "user" ? "right" : "left", margin: "10px 0" }}>
              <span style={{ 
                background: msg.sender === "user" ? userBubbleBg : (msg.isError ? '#dc3545' : botBubbleBg),
                color: msg.sender === "user" && theme === 'dark' ? '#fff' : (msg.isError ? '#fff' : textColor),
                padding: "10px 15px", 
                borderRadius: "15px",
                display: 'inline-block',
                maxWidth: '70%',
                wordWrap: 'break-word',
                whiteSpace: 'pre-wrap'
              }}>
                {msg.sender === "bot" && !msg.isError ? convertUrlsToLinks(msg.text) : msg.text}
              </span>
              {msg.eventAdded && (
                <div style={{ marginTop: '5px' }}>
                  <span style={{ 
                    backgroundColor: '#28a745', 
                    color: '#fff', 
                    padding: '3px 8px', 
                    borderRadius: '10px', 
                    fontSize: '0.85em' 
                  }}>
                    📅 일정이 캘린더에 추가되었습니다
                  </span>
                </div>
              )}
              <div style={{ marginTop: '3px' }}>
                <small style={{ color: theme === 'dark' ? '#999' : '#666' }}>
                  {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : ''}
                </small>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div style={{ textAlign: "left", margin: "10px 0" }}>
              <span style={{ 
                background: botBubbleBg, color: textColor, padding: "10px 15px", 
                borderRadius: "15px", display: 'inline-block', opacity: 0.7
              }}>
                답변 생성 중...
              </span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} style={{
          padding: '15px 20px',
          backgroundColor: cardBg,
          borderTop: `1px solid ${borderColor}`
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: '10px' }}>
            <textarea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isLoading ? "처리 중..." : "질문을 입력하세요... (Shift+Enter: 줄바꿈)"}
              disabled={isLoading}
              rows={2}
              style={{ 
                flex: 1, 
                padding: "10px",
                borderRadius: '5px',
                border: `1px solid ${borderColor}`,
                backgroundColor: bgColor,
                color: textColor,
                outline: 'none',
                resize: 'none',
                fontFamily: 'inherit'
              }}
            />
            <button 
              type="submit"
              disabled={!inputText.trim() || isLoading}
              style={{ 
                padding: "10px 20px",
                backgroundColor: (!inputText.trim() || isLoading) ? '#999' : (theme === 'dark' ? '#0084ff' : '#4CAF50'),
                color: '#fff',
                border: 'none',
                borderRadius: '5px',
                cursor: (!inputText.trim() || isLoading) ? 'default' : 'pointer',
                minWidth: '80px'
              }}
            >
              {isLoading ? '...' : '전송'}
            </button>
          </div>
          <div style={{ marginTop: '8px', textAlign: 'center' }}>
            <small style={{ color: theme === 'dark' ? '#999' : '#666' }}>
              💡 AI가 공지사항을 검색하고 분석하여 답변합니다.
            </small>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Chatbot;
