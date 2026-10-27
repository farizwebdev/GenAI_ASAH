// @ts-nocheck
"use client";
import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Trash2, Bot, Tent, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- CONFIG KONTAK & API GEN AI SABANA ADVENTURE ---
const GENAI_API_URL = process.env.NEXT_PUBLIC_GENAI_API_URL || "http://127.0.0.1:8000/api/v1/chat/message";
const SERVICE_KEY = process.env.NEXT_PUBLIC_SERVICE_KEY || "dev-secret-key-123";

// --- KOMPONEN KECIL: TYPING INDICATOR ---
const TypingIndicator = () => (
  <div className="flex space-x-1.5 p-3 bg-emerald-50 border border-emerald-100 rounded-2xl rounded-tl-none w-fit items-center shadow-xs">
    <span className="w-2 h-2 bg-emerald-500 rounded-full block animate-bounce" style={{ animationDelay: '0ms' }} />
    <span className="w-2 h-2 bg-emerald-500 rounded-full block animate-bounce" style={{ animationDelay: '150ms' }} />
    <span className="w-2 h-2 bg-emerald-500 rounded-full block animate-bounce" style={{ animationDelay: '300ms' }} />
  </div>
);

interface ChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
}

interface MessageItem {
  id: string | number;
  text: string;
  sender: 'user' | 'bot';
  sources?: string[];
  intent?: string;
  isError?: boolean;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({ isOpen, onClose }) => {
  const [sessionId] = useState(() => `web-${Math.random().toString(36).substring(2, 9)}`);
  
  // --- STATE BOT CHAT SABANA ADVENTURE ---
  const defaultBotMessage: MessageItem = {
    id: 'bot-welcome',
    text: "Halo kak! Selamat datang di Sabana Adventure Jombor 🏕️. Mau tanya seputar sewa tenda, alat outdoor, atau syarat pemesanan?",
    sender: 'bot'
  };

  const [botMessages, setBotMessages] = useState<MessageItem[]>([defaultBotMessage]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Rekomendasi Pertanyaan Cepat Toko Outdoor
  const quickQuestions = [
    "Berapa harga sewa tenda dome 4P?",
    "Syarat & jaminan sewa apa saja?",
    "Sewa 3 hari dihitung berapa hari kak?",
    "Ada paket camping komplit nggak?"
  ];

  // Auto scroll ke pesan terbaru
  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(() => scrollToBottom("instant"), 50);
    return () => clearTimeout(timer);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    scrollToBottom("smooth");
  }, [botMessages.length, isTyping]);

  // Handler kirim pesan langsung ke Layanan Gen AI FastAPI
  const handleSendBot = async (text: string) => {
    const cleanText = text.trim();
    if (!cleanText || isTyping) return;

    const userMsg: MessageItem = {
      id: `user-${Date.now()}`,
      text: cleanText,
      sender: 'user'
    };

    setBotMessages((prev) => [...prev, userMsg]);
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
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      const botReply: MessageItem = {
        id: `bot-${Date.now()}`,
        text: data.reply_text || "Maaf kak, belum ada respon dari sistem.",
        sender: 'bot',
        sources: data.sources || [],
        intent: data.intent || null,
      };

      setBotMessages((prev) => [...prev, botReply]);
    } catch (error) {
      console.error("Gagal menghubungi layanan Gen AI:", error);
      const errorMsg: MessageItem = {
        id: `bot-err-${Date.now()}`,
        text: "Maaf kak, terjadi kendala saat menghubungi asisten AI toko. Silakan pastikan server backend aktif atau hubungi admin WhatsApp di 0812-3456-7890 ya!",
        sender: 'bot',
        isError: true,
      };
      setBotMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const onFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendBot(inputText);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 16, scale: 0.98, transition: { duration: 0.15, ease: "easeOut" } }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          style={{ willChange: "transform, opacity" }}
          className="fixed bottom-4 right-4 z-[60] w-[92vw] sm:w-[390px] h-[580px] max-h-[85vh] bg-white rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-emerald-100"
        >
          {/* --- HEADER OUTDOOR MODERN --- */}
          <div className="bg-gradient-to-r from-emerald-800 via-emerald-700 to-teal-700 p-4 text-white shadow-md z-10">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-white/15 rounded-2xl backdrop-blur-sm border border-white/20">
                  <Tent size={22} className="text-emerald-200" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <h3 className="font-bold text-sm sm:text-base tracking-tight">Sabana AI Assistant</h3>
                    <Sparkles size={14} className="text-amber-300" />
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                    <span className="text-xs text-emerald-100 font-medium">Rental Alat Outdoor Jombor</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                {/* Reset percakapan */}
                <button
                  type="button"
                  onClick={() => setBotMessages([defaultBotMessage])}
                  className="p-2 hover:bg-white/15 active:scale-95 rounded-full transition text-white/80 hover:text-white"
                  title="Hapus Riwayat Chat"
                >
                  <Trash2 size={18} />
                </button>
                {/* Tutup widget */}
                <button
                  type="button"
                  onClick={onClose}
                  className="p-2 hover:bg-white/15 active:scale-90 rounded-full transition text-white"
                  aria-label="Tutup Chat"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
          </div>

          {/* --- BODY CHAT --- */}
          <div className="flex-1 overflow-y-auto p-4 bg-slate-50/70 space-y-3.5">
            <div className="text-center text-[11px] font-medium text-slate-400 my-1">
              Hari ini &bull; Sabana Adventure Jombor
            </div>

            {botMessages.map((msg) => (
              <div
                key={msg.id}
                className={`w-full flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[88%] p-3.5 text-sm leading-relaxed shadow-xs ${
                    msg.sender === 'user'
                      ? 'bg-emerald-700 text-white rounded-2xl rounded-tr-xs'
                      : msg.isError
                      ? 'bg-red-50 border border-red-200 text-red-700 rounded-2xl rounded-tl-xs'
                      : 'bg-white text-slate-700 border border-slate-200/80 rounded-2xl rounded-tl-xs'
                  }`}
                >
                  <div className="whitespace-pre-line">{msg.text}</div>

                  {/* Tampilkan Sumber Dokumen Katalog jika ada */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center gap-1.5 flex-wrap text-[10px] text-slate-400">
                      <span className="font-semibold text-emerald-700">Sumber:</span>
                      {msg.sources.map((src, idx) => (
                        <span key={idx} className="bg-emerald-50 text-emerald-800 px-1.5 py-0.5 rounded font-mono">
                          {src}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <TypingIndicator />
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* --- FOOTER: QUICK REPLIES + INPUT --- */}
          <div className="bg-white border-t border-slate-100 p-3">
            {/* Quick Suggestions */}
            <div className="flex gap-2 overflow-x-auto pb-2.5 mb-1 scrollbar-none">
              {quickQuestions.map((q, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleSendBot(q)}
                  disabled={isTyping}
                  className="shrink-0 px-3 py-1.5 bg-slate-50 border border-slate-200 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 active:scale-95 text-xs font-medium rounded-full text-slate-600 transition-all cursor-pointer disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Input Form */}
            <form onSubmit={onFormSubmit} className="flex items-center gap-2 bg-slate-100 rounded-full px-2 py-1.5 border border-transparent focus-within:border-emerald-300 focus-within:bg-white transition-all w-full">
              <input
                type="text"
                maxLength={200}
                className="flex-1 bg-transparent border-none outline-none text-sm text-slate-700 placeholder:text-slate-400 pl-3"
                placeholder="Tanya sewa tenda / ketik format sewa..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isTyping}
              />
              <button
                type="submit"
                disabled={!inputText.trim() || isTyping}
                className={`p-2.5 rounded-full text-white transition-all shadow-sm touch-manipulation ${
                  !inputText.trim() || isTyping
                    ? 'bg-slate-300 cursor-not-allowed'
                    : 'bg-emerald-700 hover:bg-emerald-800 hover:scale-105 active:scale-95 cursor-pointer'
                }`}
                aria-label="Kirim Pesan"
              >
                <Send size={16} className={!inputText.trim() ? "" : "ml-0.5"} />
              </button>
            </form>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ChatWidget;