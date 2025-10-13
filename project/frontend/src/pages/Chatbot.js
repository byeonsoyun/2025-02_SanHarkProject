import React, { useState, useEffect } from "react";

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [ws, setWs] = useState(null);

  useEffect(() => {
    const socket = new WebSocket("ws://127.0.0.1:8000/ws/chat/");
    socket.onopen = () => console.log("WebSocket 연결 성공");
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setMessages((prev) => [...prev, data.message]);
    };
    socket.onclose = () => console.log("WebSocket 연결 종료");

    setWs(socket);

    return () => socket.close();
  }, []);

  const sendMessage = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ message: input }));
      setInput("");
    } else {
      console.log("WebSocket 닫혀 있음");
    }
  };

  return (
    <div>
      <h1>Chatbot 테스트</h1>
      <div style={{ border: "1px solid gray", padding: "10px", marginBottom: "10px" }}>
        {messages.map((msg, idx) => (
          <div key={idx}>{msg}</div>
        ))}
      </div>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <button onClick={sendMessage}>전송</button>
    </div>
  );
};

export default Chatbot;
