/**
 * CareSlot — AI Chat Page
 * Full chatbot UI with symptom analysis and multi-turn conversation.
 */

import { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../../services/api';
import {
  Send, Bot, User, Loader2, AlertTriangle, Sparkles,
  RotateCcw, ClipboardList, Shield, Stethoscope,
} from 'lucide-react';

const SUGGESTIONS = [
  'I have a persistent headache and mild fever',
  'Experiencing chest tightness and shortness of breath',
  'Skin rash that appeared 3 days ago with itching',
  'Irregular periods with fatigue and weight gain',
];

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [mode, setMode] = useState('chat'); // 'chat' or 'symptom'
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMsg = (role, content, meta = null) => {
    setMessages((prev) => [...prev, { role, content, meta, ts: Date.now() }]);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    addMsg('user', text);
    setInput('');
    setLoading(true);

    try {
      if (mode === 'symptom') {
        const res = await chatAPI.analyzeSymptoms(text);
        addMsg('ai', res.prediction, {
          type: 'symptom-result',
          risk_level: res.risk_level,
          precautions: res.precautions,
          home_remedies: res.home_remedies,
          recommended_specialist: res.recommended_specialist,
          next_steps: res.next_steps,
          disclaimer: res.disclaimer,
        });
        if (res.session_id) setSessionId(res.session_id);
      } else {
        const res = await chatAPI.conversation(text, sessionId);
        addMsg('ai', res.response, {
          type: 'chat',
          risk_level: res.risk_level,
          recommended_specialist: res.recommended_specialist,
        });
        if (res.session_id) setSessionId(res.session_id);
      }
    } catch (err) {
      addMsg('ai', `Sorry, I couldn't process that. ${err.message}`, { type: 'error' });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSuggestion = (text) => {
    setInput(text);
    setMode('symptom');
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const resetChat = () => {
    setMessages([]);
    setSessionId(null);
    setInput('');
  };

  const riskColors = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626',
  };

  return (
    <div className="chat-page">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-header-icon">
            <Bot size={22} />
          </div>
          <div>
            <h1>AI Health Assistant</h1>
            <p>Powered by RAG + Llama 3.1</p>
          </div>
        </div>
        <div className="chat-header-actions">
          <div className="chat-mode-toggle">
            <button
              className={`chat-mode-btn ${mode === 'chat' ? 'chat-mode-active' : ''}`}
              onClick={() => setMode('chat')}
            >
              <Sparkles size={14} /> Chat
            </button>
            <button
              className={`chat-mode-btn ${mode === 'symptom' ? 'chat-mode-active' : ''}`}
              onClick={() => setMode('symptom')}
            >
              <Stethoscope size={14} /> Symptom Analysis
            </button>
          </div>
          <button className="chat-reset-btn" onClick={resetChat} title="New conversation">
            <RotateCcw size={16} />
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="chat-disclaimer">
        <Shield size={14} />
        <span>This AI provides preliminary guidance only. Always consult a qualified healthcare professional.</span>
      </div>

      {/* Messages area */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">
              <Bot size={40} strokeWidth={1.2} />
            </div>
            <h2>How can I help you today?</h2>
            <p>Describe your symptoms or ask any health-related question.</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chat-suggestion-chip" onClick={() => handleSuggestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble chat-bubble-${msg.role}`}>
            <div className="chat-bubble-avatar">
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className="chat-bubble-body">
              <p className="chat-bubble-text">{msg.content}</p>

              {/* Symptom analysis result card */}
              {msg.meta?.type === 'symptom-result' && (
                <div className="chat-result-card">
                  {msg.meta.risk_level && (
                    <div className="chat-risk-badge" style={{ background: `${riskColors[msg.meta.risk_level]}18`, color: riskColors[msg.meta.risk_level], borderColor: `${riskColors[msg.meta.risk_level]}40` }}>
                      <AlertTriangle size={14} />
                      Risk: {msg.meta.risk_level.toUpperCase()}
                    </div>
                  )}
                  {msg.meta.recommended_specialist && (
                    <div className="chat-specialist">
                      <Stethoscope size={14} />
                      <span>Recommended: <strong>{msg.meta.recommended_specialist}</strong></span>
                    </div>
                  )}
                  {msg.meta.precautions?.length > 0 && (
                    <div className="chat-result-section">
                      <h4><ClipboardList size={14} /> Precautions</h4>
                      <ul>{msg.meta.precautions.map((p, j) => <li key={j}>{p}</li>)}</ul>
                    </div>
                  )}
                  {msg.meta.home_remedies?.length > 0 && (
                    <div className="chat-result-section">
                      <h4>🏠 Home Remedies</h4>
                      <ul>{msg.meta.home_remedies.map((r, j) => <li key={j}>{r}</li>)}</ul>
                    </div>
                  )}
                  {msg.meta.next_steps?.length > 0 && (
                    <div className="chat-result-section">
                      <h4>➡️ Next Steps</h4>
                      <ul>{msg.meta.next_steps.map((s, j) => <li key={j}>{s}</li>)}</ul>
                    </div>
                  )}
                  {msg.meta.disclaimer && (
                    <p className="chat-result-disclaimer">{msg.meta.disclaimer}</p>
                  )}
                </div>
              )}

              {msg.meta?.type === 'chat' && msg.meta.risk_level && (
                <div className="chat-risk-badge" style={{ background: `${riskColors[msg.meta.risk_level]}18`, color: riskColors[msg.meta.risk_level], borderColor: `${riskColors[msg.meta.risk_level]}40` }}>
                  <AlertTriangle size={14} />
                  Risk: {msg.meta.risk_level.toUpperCase()}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-bubble chat-bubble-ai">
            <div className="chat-bubble-avatar"><Bot size={16} /></div>
            <div className="chat-bubble-body">
              <div className="chat-typing">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-bar">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={mode === 'symptom' ? 'Describe your symptoms...' : 'Type your message...'}
          disabled={loading}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || loading}
          aria-label="Send"
        >
          {loading ? <Loader2 size={18} className="auth-spinner" /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}
