/**
 * CareSlot — Floating Chat Popup
 * AI health assistant as a floating widget.
 */

import { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../services/api';
import {
  MessageCircle, X, Send, RotateCcw,
  AlertTriangle, Loader2, HeartPulse,
} from 'lucide-react';

export default function ChatPopup() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const messagesEnd = useRef(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await chatAPI.conversation(text, sessionId);
      const botMsg = {
        role: 'assistant',
        text: data.response || data.message || 'I received your message.',
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Sorry, I encountered an error. Please try again.', error: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const reset = () => {
    setMessages([]);
  };

  return (
    <>
      {/* FAB Button */}
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Open AI Chat">
          <MessageCircle size={24} />
          <span className="chat-fab-pulse" />
        </button>
      )}

      {/* Chat Window */}
      {open && (
        <div className="chat-popup">
          {/* Header */}
          <div className="chat-popup-header">
            <div className="chat-popup-header-left">
              <div className="chat-popup-logo">
                <HeartPulse size={16} />
              </div>
              <div>
                <h3>CareSlot AI</h3>
                <span className="chat-popup-status">
                  <span className="chat-popup-dot" />
                  Llama 3.2 · Online
                </span>
              </div>
            </div>
            <div className="chat-popup-actions">
              <button onClick={reset} title="Reset chat" className="chat-popup-reset">
                <RotateCcw size={14} />
              </button>
              <button onClick={() => setOpen(false)} title="Close" className="chat-popup-close-btn">
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="chat-popup-disclaimer">
            <AlertTriangle size={12} />
            <span>AI guidance only — not a medical diagnosis</span>
          </div>

          {/* Messages */}
          <div className="chat-popup-messages">
            {messages.length === 0 && (
              <div className="chat-popup-empty">
                <p>Hi! I'm your AI health assistant. Ask me about symptoms, conditions, or health queries.</p>
                <div className="chat-popup-suggestions">
                  {['I have a headache', 'What is PCOD?', 'Skin rash remedies'].map((s) => (
                    <button key={s} onClick={() => { setInput(s); }} className="chat-popup-chip">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chat-popup-msg ${msg.role === 'user' ? 'chat-popup-msg-user' : 'chat-popup-msg-bot'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="chat-popup-msg-avatar">
                    <HeartPulse size={12} />
                  </div>
                )}
                <div className={`chat-popup-msg-bubble ${msg.error ? 'chat-popup-msg-error' : ''}`}>
                  {msg.text}
                </div>
                {msg.role === 'user' && (
                  <div className="chat-popup-msg-avatar chat-popup-msg-avatar-user">U</div>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-popup-msg chat-popup-msg-bot">
                <div className="chat-popup-msg-avatar">
                  <HeartPulse size={12} />
                </div>
                <div className="chat-popup-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* Input */}
          <div className="chat-popup-input">
            <input
              type="text"
              placeholder="Ask about patient data..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
            />
            <button
              className="chat-popup-send"
              onClick={sendMessage}
              disabled={!input.trim() || loading}
            >
              {loading ? <Loader2 size={16} className="chat-popup-spinner" /> : <Send size={16} />}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
