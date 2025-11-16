import React, { useState } from "react";

const Chatbot = () => {
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState([]);
  const [pdfFile, setPdfFile] = useState(null);

  // 텍스트 전송
  const handleSubmit = async () => {
    if (!inputText.trim() && !pdfFile) return;

    // 텍스트 메시지 전송
    if (inputText.trim()) {
      setMessages(prev => [...prev, { sender: "user", text: inputText }]);

      try {
        const response = await fetch("/chat/api/chat/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: inputText }),
        });
        const data = await response.json();
        setMessages(prev => [...prev, { sender: "bot", text: data.reply }]);
        setInputText("");
      } catch (err) {
        console.error(err);
      }
    }

    // PDF 업로드 전송
    if (pdfFile) {
      setMessages(prev => [...prev, { sender: "user", text: `[PDF 선택] ${pdfFile.name}` }]);

      const formData = new FormData();
      formData.append("pdf", pdfFile);

      try {
        const response = await fetch("/chat/upload_pdf/", {
          method: "POST",
          body: formData,
        });
        const data = await response.json();
        setMessages(prev => [...prev, { sender: "bot", text: data.reply }]);
        setPdfFile(null);
      } catch (err) {
        console.error(err);
      }
    }
  };

  // 엔터로 텍스트 전송
  const handleKeyPress = e => {
    if (e.key === "Enter") handleSubmit();
  };

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "0 auto" }}>
      <h2>챗봇</h2>

      {/* 메시지 영역 */}
      <div style={{ minHeight: "300px", border: "1px solid #ccc", padding: "10px", marginBottom: "10px" }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ textAlign: msg.sender === "user" ? "right" : "left", margin: "5px 0" }}>
            <span style={{ background: msg.sender === "user" ? "#DCF8C6" : "#EEE", padding: "5px 10px", borderRadius: "10px" }}>
              {msg.text}
            </span>
          </div>
        ))}
      </div>

      {/* 입력창 + 전송 버튼 + PDF 업로드 */}
      <div style={{ display: "flex", alignItems: "center" }}>
        <input
          type="text"
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="메시지를 입력하거나 + 버튼으로 PDF 선택"
          style={{ flex: 1, padding: "8px" }}
        />

        {/* PDF 선택 버튼 */}
        <label htmlFor="pdf-upload" style={{ marginLeft: "5px", cursor: "pointer", fontSize: "20px" }}>+</label>
        <input
          id="pdf-upload"
          type="file"
          accept="application/pdf"
          style={{ display: "none" }}
          onChange={e => setPdfFile(e.target.files[0])}
        />

        {/* 전송 버튼 */}
        <button onClick={handleSubmit} style={{ padding: "8px 16px", marginLeft: "5px" }}>전송</button>
      </div>

      {/* 선택된 PDF 표시 */}
      {pdfFile && <p style={{ marginTop: "5px" }}>선택된 PDF: {pdfFile.name}</p>}
    </div>
  );
};

export default Chatbot;
