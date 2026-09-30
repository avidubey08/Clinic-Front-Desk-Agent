import React, { useState } from 'react';
import { API_BASE } from '../services/api';

export default function LiveChatModal({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    { sender: 'agent', text: 'Namaste! Sunrise Clinic Dehradun mein aapka swagat hai. Main front desk agent hoon. Main aapki kya madad kar sakti hoon?' }
  ]);
  const [inputText, setInputText] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  if (!isOpen) return null;

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;

    const userMsg = inputText.trim();
    setInputText('');
    setMessages((prev) => [...prev, { sender: 'caller', text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: 'live_test_call',
          today: '2026-10-01',
          message: userMsg,
          history: history,
        }),
      });
      const data = await res.json();
      setLastResult(data);
      setHistory(data.turns || [...history, userMsg]);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: data.reply,
          toolCalls: data.tool_calls,
          state: data.terminal_state,
          reason: data.escalation_reason,
          appointmentId: data.appointment_id,
        },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { sender: 'agent', text: 'Kshama karein, network error aayi hai. Kripya dobara try karein.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([
      { sender: 'agent', text: 'Namaste! Sunrise Clinic Dehradun mein aapka swagat hai. Main front desk agent hoon. Main aapki kya madad kar sakti hoon?' }
    ]);
    setHistory([]);
    setLastResult(null);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      backdropFilter: 'blur(3px)',
    }}>
      <div style={{
        width: '560px',
        maxHeight: '85vh',
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid #e2e8f0',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          backgroundColor: '#0284c7',
          color: '#ffffff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: '700' }}>
              Live Receptionist Simulator
            </h3>
            <p style={{ fontSize: '11px', opacity: 0.9, marginTop: '2px' }}>
              Talk in Hindi, English or Hinglish • Today: 2026-10-01 (Thu)
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleReset}
              style={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11px',
                cursor: 'pointer',
                fontWeight: '600',
              }}
            >
              Reset Call
            </button>
            <button
              onClick={onClose}
              style={{
                backgroundColor: 'transparent',
                color: '#fff',
                border: 'none',
                fontSize: '18px',
                cursor: 'pointer',
                fontWeight: '700',
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Quick Example Prompt Pills */}
        <div style={{
          padding: '10px 16px',
          backgroundColor: '#f8fafc',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: '11px', color: '#64748b', alignSelf: 'center', fontWeight: '600' }}>
            Try:
          </span>
          <button
            onClick={() => setInputText('Dr. Rao ke saath 3 tareekh subah ka appointment chahiye.')}
            style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', backgroundColor: '#fff', cursor: 'pointer' }}
          >
            Booking
          </button>
          <button
            onClick={() => setInputText('Waise abhi seene mein tez dard ho raha hai...')}
            style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', border: '1px solid #fca5a5', backgroundColor: '#fee2e2', color: '#b91c1c', cursor: 'pointer', fontWeight: '600' }}
          >
            Emergency Test
          </button>
          <button
            onClick={() => setInputText('Sharma ji ke liye appointment chahiye.')}
            style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', border: '1px solid #fcd34d', backgroundColor: '#fef3c7', color: '#b45309', cursor: 'pointer' }}
          >
            Ambiguous Name
          </button>
          <button
            onClick={() => setInputText('Crocin kitni goli lu aur kitni der mein asar hoga?')}
            style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', border: '1px solid #f9a8d4', backgroundColor: '#fce7f3', color: '#be185d', cursor: 'pointer' }}
          >
            Medical Advice
          </button>
        </div>

        {/* Chat Message Stream */}
        <div style={{
          flex: 1,
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          minHeight: '340px',
          backgroundColor: '#f8fafc',
        }}>
          {messages.map((m, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: m.sender === 'caller' ? 'flex-end' : 'flex-start',
              }}
            >
              <span style={{ fontSize: '10px', color: '#94a3b8', fontWeight: '700', marginBottom: '4px', textTransform: 'uppercase' }}>
                {m.sender === 'caller' ? 'You (Caller)' : 'AI Receptionist'}
              </span>
              <div style={{
                maxWidth: '85%',
                padding: '10px 14px',
                borderRadius: '12px',
                fontSize: '13px',
                lineHeight: '1.4',
                backgroundColor: m.sender === 'caller' ? '#0284c7' : '#ffffff',
                color: m.sender === 'caller' ? '#ffffff' : '#0f172a',
                border: m.sender === 'caller' ? 'none' : '1px solid #e2e8f0',
                boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
              }}>
                {m.text}
              </div>

              {/* Show tool calls underneath if any */}
              {m.toolCalls && m.toolCalls.length > 0 && (
                <div style={{
                  marginTop: '6px',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}>
                  {m.toolCalls.map((tc, tidx) => (
                    <div
                      key={tidx}
                      style={{
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        backgroundColor: '#f1f5f9',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        color: '#0369a1',
                      }}
                    >
                      ⚡ Tool: <strong>{tc.name}</strong>({JSON.stringify(tc.arguments)})
                    </div>
                  ))}
                </div>
              )}

              {/* Terminal badge if reached */}
              {m.state && (
                <div style={{ marginTop: '4px' }}>
                  <span style={{
                    fontSize: '10px',
                    fontWeight: '700',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: m.state === 'escalated' ? '#fee2e2' : '#dcfce7',
                    color: m.state === 'escalated' ? '#b91c1c' : '#15803d',
                  }}>
                    {m.state.toUpperCase()} {m.reason ? `(${m.reason})` : ''}
                  </span>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ color: '#64748b', fontSize: '12px', fontStyle: 'italic' }}>
              Receptionist is typing...
            </div>
          )}
        </div>

        {/* Input Form */}
        <form
          onSubmit={handleSend}
          style={{
            padding: '14px 16px',
            backgroundColor: '#ffffff',
            borderTop: '1px solid #e2e8f0',
            display: 'flex',
            gap: '10px',
          }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your message in Hindi, Hinglish or English..."
            disabled={loading}
            style={{
              flex: 1,
              padding: '10px 14px',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              fontSize: '13px',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            disabled={loading || !inputText.trim()}
            style={{
              padding: '10px 18px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: '600',
              fontSize: '13px',
              cursor: loading ? 'default' : 'pointer',
              opacity: loading || !inputText.trim() ? 0.6 : 1,
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
