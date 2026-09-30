import React, { useState, useEffect } from 'react';
import OutcomePanel from './OutcomePanel';
import { fetchConversationDetail, fetchConversations } from '../services/api';

export default function ConversationDetail({ conversationId = 'cv_0011', onBack }) {
  const [data, setData] = useState(null);
  const [availableList, setAvailableList] = useState([]);
  const [selectedId, setSelectedId] = useState(conversationId);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setSelectedId(conversationId);
  }, [conversationId]);

  useEffect(() => {
    fetchConversations().then((list) => {
      setAvailableList(list);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchConversationDetail(selectedId)
      .then((res) => {
        setData(res);
      })
      .catch((err) => {
        console.error('Error fetching detail:', err);
      })
      .finally(() => setLoading(false));
  }, [selectedId]);

  const getStatusBadge = () => {
    if (!data) return null;
    const state = data.terminal_state?.toUpperCase();
    const reason = data.escalation_reason?.toUpperCase().replace('_', ' ');

    if (state === 'ESCALATED') {
      return (
        <span className="badge badge-clinical" style={{ fontSize: '12px', padding: '6px 12px' }}>
          ESCALATED — {reason || 'HUMAN'}
        </span>
      );
    }
    if (state === 'BOOKED') {
      return (
        <span className="badge badge-booked" style={{ fontSize: '12px', padding: '6px 12px' }}>
          BOOKED
        </span>
      );
    }
    if (state === 'RESCHEDULED') {
      return (
        <span className="badge badge-rescheduled" style={{ fontSize: '12px', padding: '6px 12px' }}>
          RESCHEDULED
        </span>
      );
    }
    if (state === 'CANCELLED') {
      return (
        <span className="badge badge-cancelled" style={{ fontSize: '12px', padding: '6px 12px' }}>
          CANCELLED
        </span>
      );
    }
    if (state === 'REFUSED') {
      return (
        <span className="badge badge-refused" style={{ fontSize: '12px', padding: '6px 12px' }}>
          REFUSED — SECURITY
        </span>
      );
    }
    return (
      <span className="badge badge-abandoned" style={{ fontSize: '12px', padding: '6px 12px' }}>
        {state || 'ABANDONED'}
      </span>
    );
  };

  const formatToolArguments = (args) => {
    return Object.entries(args || {})
      .map(([k, v]) => `${k}="${v}"`)
      .join(', ');
  };

  return (
    <div style={{ flex: 1, padding: '32px 40px', overflowY: 'auto' }}>
      {/* Top Bar with Dropdown & Back Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={onBack}
            style={{
              padding: '6px 12px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              color: '#475569',
            }}
          >
            ← Back to Queue
          </button>

          {/* Conversation Selector */}
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            style={{
              padding: '6px 12px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600',
              color: '#0f172a',
              cursor: 'pointer',
            }}
          >
            {[
              'cv_0001', 'cv_0002', 'cv_0003', 'cv_0004', 'cv_0005',
              'cv_0006', 'cv_0007', 'cv_0008', 'cv_0009', 'cv_0010',
              'cv_0011', 'cv_0012', 'cv_0013', 'cv_0014', 'cv_0015',
              'adv_0001', 'adv_0002', 'adv_0003', 'adv_0004', 'adv_0005',
              'adv_0006', 'adv_0007', 'adv_0008'
            ].map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>

        <div>
          {getStatusBadge()}
        </div>
      </div>

      {/* Screen Title */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', letterSpacing: '-0.02em' }}>
          Conversation {selectedId}
        </h1>
        <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
          Sunrise Clinic, Dehradun — {data?.today || '2026-10-01'}, 11:42
        </p>
      </div>

      {/* Two Column Layout (Matching PDF Page 4 Screen 2) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.6fr 1fr',
        gap: '28px',
        alignItems: 'start',
      }}>
        {/* Left Column: Transcript and Tool Calls */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a', marginBottom: '20px' }}>
            Transcript and tool calls
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Interleaved caller turns and inline tool calls */}
            {data?.turns?.map((turn, idx) => {
              // Show tool call related to this turn or near end
              const relevantTool = data.tool_calls && data.tool_calls[idx];
              return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {/* Caller Utterance */}
                  <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: '700',
                      color: '#94a3b8',
                      minWidth: '55px',
                      letterSpacing: '0.05em',
                      textTransform: 'uppercase',
                      paddingTop: '2px',
                    }}>
                      CALLER
                    </span>
                    <div style={{ fontSize: '13px', color: '#1e293b', lineHeight: '1.5' }}>
                      {turn}
                    </div>
                  </div>

                  {/* Inline Tool Call Card if fired at this step */}
                  {relevantTool && (
                    <div style={{
                      marginLeft: '71px',
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: '12px',
                      color: '#0f172a',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          backgroundColor: '#0284c7',
                          color: '#ffffff',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '10px',
                          fontWeight: '700',
                        }}>
                          TOOL
                        </span>
                        <span style={{ fontWeight: '600', color: '#0369a1' }}>
                          {relevantTool.name}
                        </span>
                        <span style={{ color: '#475569' }}>
                          ({formatToolArguments(relevantTool.arguments)})
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Any remaining tool calls */}
            {data?.tool_calls?.length > (data?.turns?.length || 0) && (
              data.tool_calls.slice(data.turns.length).map((tc, idx) => (
                <div
                  key={`rem-${idx}`}
                  style={{
                    marginLeft: '71px',
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '12px',
                    color: '#0f172a',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      backgroundColor: '#0284c7',
                      color: '#ffffff',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: '700',
                    }}>
                      TOOL
                    </span>
                    <span style={{ fontWeight: '600', color: '#0369a1' }}>
                      {tc.name}
                    </span>
                    <span style={{ color: '#475569' }}>
                      ({formatToolArguments(tc.arguments)})
                    </span>
                  </div>
                </div>
              ))
            )}

            {/* Agent Final Reply */}
            <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', marginTop: '4px' }}>
              <span style={{
                fontSize: '11px',
                fontWeight: '700',
                color: '#0284c7',
                minWidth: '55px',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                paddingTop: '2px',
              }}>
                AGENT
              </span>
              <div style={{ fontSize: '13px', color: '#0f172a', lineHeight: '1.5', fontWeight: '500' }}>
                {data?.reply || '...'}
              </div>
            </div>

            {/* Bottom Callout Alert Box (Matching PDF Page 4) */}
            <div style={{
              marginTop: '16px',
              padding: '14px 18px',
              backgroundColor: data?.terminal_state === 'escalated' ? '#fef2f2' : (data?.terminal_state === 'booked' ? '#f0fdf4' : '#f8fafc'),
              border: `1px solid ${data?.terminal_state === 'escalated' ? '#fecaca' : (data?.terminal_state === 'booked' ? '#bbf7d0' : '#e2e8f0')}`,
              borderRadius: '8px',
              fontSize: '13px',
              color: data?.terminal_state === 'escalated' ? '#b91c1c' : (data?.terminal_state === 'booked' ? '#15803d' : '#475569'),
              fontWeight: '500',
            }}>
              {data?.terminal_state === 'escalated' && 'Booking flow abandoned. No appointment was created.'}
              {data?.terminal_state === 'booked' && `Appointment ${data.appointment_id} confirmed and recorded in clinic schedule.`}
              {data?.terminal_state === 'rescheduled' && `Appointment ${data.appointment_id} moved to new slot successfully.`}
              {data?.terminal_state === 'cancelled' && `Appointment ${data.appointment_id} cancelled and slot released.`}
              {data?.terminal_state === 'refused' && 'Request refused due to policy/security boundary enforcement.'}
              {data?.terminal_state === 'abandoned' && 'Conversation ended with no action taken and no human needed.'}
            </div>
          </div>
        </div>

        {/* Right Column: Outcome Panel */}
        <div>
          <OutcomePanel outcome={data} />
        </div>
      </div>
    </div>
  );
}
