import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Trash2, Tent, MessageSquare } from 'lucide-react';
import './ChatWidget.css';

const GENAI_API_URL = "http://127.0.0.1:8000/api/v1/chat/message";
const SERVICE_KEY = "dev-secret-key-123";

const TypingIndicator = () => (
  <div className="typing-indicator">
    <span className="dot dot-1" />
    <span className="dot dot-2" />
    <span className="dot dot-3" />
  </div>
);

export default function ChatWidget({ isOpen, onClose }) {
  const [sessionId] = useState(() => `web-${Math.random().toString(36).substring(2, 9)}`);
  
  const defaultBotMessage = {
    id: 'bot-welcome',
    text: "Halo kak! Selamat datang di Sabana Adventure Jombor 🏕️. Ada yang bisa dibantu seputar sewa tenda, alat outdoor, atau syarat pemesanan?",
    sender: 'bot'
  };

  const [messages, setMessages] = useState([defaultBotMessage]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const quickQuestions = [
    "Berapa harga sewa tenda dome 4P?",
    "Syarat & jaminan sewa apa saja?",
    "Sewa 3 hari dihitung berapa hari kak?",
    "Ada paket camping komplit nggak?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [isOpen, messages, isTyping]);

  const handleSendMessage = async (text) => {
    const cleanText = text.trim();
    if (!cleanText || isTyping) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      text: cleanText,
      sender: 'user'
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText("");
    setIsTyping(true);

    try {
      const response = await fetch(GENAI_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Service-Key': SERVICE_KEY,
        },
        body: JSON.stringify({
          channel: 'web_widget',
          message: cleanText,
          session_id: sessionId,
          reference_date: new Date().toISOString().split('T')[0],
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const botReply = {
        id: `bot-${Date.now()}`,
        text: data.reply_text || "Maaf kak, belum ada respon dari sistem.",
        sender: 'bot',
        sources: data.sources || [],
        intent: data.intent || null,
      };

      setMessages((prev) => [...prev, botReply]);
    } catch (error) {
      console.error("Gagal menghubungi layanan Gen AI:", error);
      const errorMsg = {
        id: `bot-err-${Date.now()}`,
        text: "Maaf kak, server Gen AI belum aktif atau ada kendala koneksi. Pastikan server FastAPI di port 8000 sudah berjalan ya!",
        sender: 'bot',
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSendMessage(inputText);
  };

  if (!isOpen) return null;

  return (
    <div className="chat-widget-container">
      {/* Header Widget */}
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="chat-avatar">
            <Tent size={22} />
          </div>
          <div>
            <div className="chat-title-row">
              <h3>Sabana AI Assistant</h3>
            </div>
            <div className="chat-status-row">
              <span className="online-badge" />
              <span className="status-text">Rental Alat Outdoor Jombor</span>
            </div>
          </div>
        </div>

        <div className="chat-header-actions">
          <button
            type="button"
            onClick={() => setMessages([defaultBotMessage])}
            className="icon-btn"
            title="Reset Chat"
          >
            <Trash2 size={18} />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="icon-btn close-btn"
            title="Tutup Chat"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Body Chat */}
      <div className="chat-body">
        <div className="chat-timestamp-badge">
          Hari ini &bull; Sabana Adventure Jombor
        </div>

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-row ${msg.sender === 'user' ? 'message-user' : 'message-bot'}`}
          >
            <div className={`message-bubble ${msg.isError ? 'bubble-error' : ''}`}>
              <div className="message-content">{msg.text}</div>

              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-container">
                  <span className="sources-label">Sumber:</span>
                  {msg.sources.map((src, idx) => (
                    <span key={idx} className="source-chip">{src}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="message-row message-bot">
            <TypingIndicator />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Footer / Input */}
      <div className="chat-footer">
        {/* Quick Questions */}
        <div className="quick-questions-scroll">
          {quickQuestions.map((q, idx) => (
            <button
              key={idx}
              type="button"
              className="quick-chip"
              onClick={() => handleSendMessage(q)}
              disabled={isTyping}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="chat-input-form">
          <div className="input-icon">
            <MessageSquare size={16} />
          </div>
          <input
            type="text"
            className="chat-text-input"
            placeholder="Tanya sewa tenda / format pemesanan..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isTyping}
          />
          <button
            type="submit"
            className="send-button"
            disabled={!inputText.trim() || isTyping}
            aria-label="Kirim Pesan"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
