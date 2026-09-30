import React, { useState, useEffect } from 'react';
import { fetchStats, fetchHandoffs, resolveHandoff } from '../services/api';

export default function HandoffQueue({ onSelectConversation }) {
  const [stats, setStats] = useState({
    conversations_total: 37,
    completed_by_agent: 31,
    completed_percentage: 84,
    escalated_total: 6,
    escalated_open: 4,
    urgent_unresolved: 1,
  });
  const [handoffs, setHandoffs] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [s, h] = await Promise.all([fetchStats(), fetchHandoffs()]);
      setStats(s);
      setHandoffs(h);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (e, convId) => {
    e.stopPropagation();
    try {
      await resolveHandoff(convId);
      loadData();
    } catch (err) {
      console.error('Failed to resolve:', err);
    }
  };

  const getBadgeClass = (reason) => {
    switch (reason) {
      case 'clinical_urgent':
        return 'badge-clinical';
      case 'not_authorised':
        return 'badge-not-authorised';
      case 'ambiguous_patient':
        return 'badge-ambiguous';
      case 'medical_advice':
        return 'badge-medical-advice';
      default:
        return 'badge-out-of-scope';
    }
  };

  const formatReason = (reason) => {
    switch (reason) {
      case 'clinical_urgent':
        return 'CLINICAL';
      case 'not_authorised':
        return 'NOT AUTHORISED';
      case 'ambiguous_patient':
        return 'AMBIGUOUS PATIENT';
      case 'medical_advice':
        return 'MEDICAL ADVICE';
      default:
        return reason?.toUpperCase().replace('_', ' ') || 'ESCALATED';
    }
  };

  const openHandoffs = handoffs.filter((h) => !h.resolved);

  return (
    <div style={{ flex: 1, padding: '32px 40px', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', letterSpacing: '-0.02em' }}>
            Handoff Queue
          </h1>
          <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
            Sunrise Clinic, Dehradun — conversations the agent escalated
          </p>
        </div>
        <div style={{
          padding: '6px 14px',
          borderRadius: '20px',
          backgroundColor: '#eff6ff',
          color: '#1d4ed8',
          fontSize: '12px',
          fontWeight: '700',
          letterSpacing: '0.04em',
          border: '1px solid #bfdbfe',
        }}>
          {openHandoffs.length} OPEN
        </div>
      </div>

      {/* Counters Across Top */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '20px',
        marginBottom: '32px',
      }}>
        {/* Card 1 */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '20px 24px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Conversations
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#0f172a', marginTop: '8px' }}>
            {stats.conversations_total}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
            today
          </div>
        </div>

        {/* Card 2 */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '20px 24px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Completed By Agent
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#0f172a', marginTop: '8px' }}>
            {stats.completed_by_agent}
          </div>
          <div style={{ fontSize: '12px', color: '#16a34a', marginTop: '4px', fontWeight: '500' }}>
            {stats.completed_percentage}%
          </div>
        </div>

        {/* Card 3 */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '20px 24px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Escalated
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#0f172a', marginTop: '8px' }}>
            {stats.escalated_total}
          </div>
          <div style={{ fontSize: '12px', color: '#f59e0b', marginTop: '4px', fontWeight: '500' }}>
            {openHandoffs.length} still open
          </div>
        </div>

        {/* Card 4 */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          padding: '20px 24px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Urgent
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#dc2626', marginTop: '8px' }}>
            {stats.urgent_unresolved}
          </div>
          <div style={{ fontSize: '12px', color: '#dc2626', marginTop: '4px', fontWeight: '500' }}>
            clinical, unresolved
          </div>
        </div>
      </div>

      {/* Open Handoffs Table */}
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        border: '1px solid #e2e8f0',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
      }}>
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid #e2e8f0',
          fontSize: '14px',
          fontWeight: '700',
          color: '#0f172a',
        }}>
          Open handoffs
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <th style={{ padding: '14px 24px', fontWeight: '600' }}>Conversation</th>
              <th style={{ padding: '14px 24px', fontWeight: '600' }}>Caller Said</th>
              <th style={{ padding: '14px 24px', fontWeight: '600' }}>Reason</th>
              <th style={{ padding: '14px 24px', fontWeight: '600' }}>Time</th>
              <th style={{ padding: '14px 24px', fontWeight: '600', textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {openHandoffs.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ padding: '36px 24px', textAlign: 'center', color: '#94a3b8' }}>
                  No open handoffs currently. All escalated cases resolved.
                </td>
              </tr>
            ) : (
              openHandoffs.map((item) => (
                <tr
                  key={item.conversation_id}
                  onClick={() => onSelectConversation(item.conversation_id)}
                  style={{
                    borderBottom: '1px solid #f1f5f9',
                    cursor: 'pointer',
                    transition: 'background-color 0.15s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f8fafc')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td style={{ padding: '16px 24px', fontWeight: '600', color: '#0284c7' }} className="mono">
                    {item.conversation_id}
                  </td>
                  <td style={{ padding: '16px 24px', color: '#1e293b', maxWidth: '340px' }}>
                    "{item.caller_said}"
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <span className={`badge ${getBadgeClass(item.reason)}`}>
                      {formatReason(item.reason)}
                    </span>
                  </td>
                  <td style={{ padding: '16px 24px', color: '#64748b' }}>
                    {item.time_str || '11:42'}
                  </td>
                  <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                    <button
                      onClick={(e) => handleResolve(e, item.conversation_id)}
                      style={{
                        padding: '6px 14px',
                        backgroundColor: '#0284c7',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        transition: 'background-color 0.15s',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#0369a1')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#0284c7')}
                    >
                      Resolve
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
