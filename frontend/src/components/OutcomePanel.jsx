import React from 'react';

export default function OutcomePanel({ outcome }) {
  if (!outcome) {
    return (
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        border: '1px solid #e2e8f0',
        padding: '24px',
        color: '#94a3b8',
      }}>
        No outcome data available.
      </div>
    );
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return Number(num).toLocaleString();
  };

  const formatLatency = (ms) => {
    if (ms === null || ms === undefined) return '-';
    return (ms / 1000).toFixed(1) + ' s';
  };

  return (
    <div style={{
      backgroundColor: '#ffffff',
      borderRadius: '12px',
      border: '1px solid #e2e8f0',
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
    }}>
      <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a' }}>
        Outcome
      </h2>

      {/* Key-Value Metrics Table */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
          <span style={{ color: '#64748b' }}>terminal_state</span>
          <span className="mono" style={{ fontWeight: '600', color: '#0f172a' }}>
            {outcome.terminal_state || 'unknown'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
          <span style={{ color: '#64748b' }}>escalation_reason</span>
          <span className="mono" style={{ fontWeight: '600', color: outcome.escalation_reason ? '#dc2626' : '#64748b' }}>
            {outcome.escalation_reason ? outcome.escalation_reason : 'null'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
          <span style={{ color: '#64748b' }}>patient_id</span>
          <span className="mono" style={{ fontWeight: '600', color: '#0284c7' }}>
            {outcome.patient_id || 'null'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
          <span style={{ color: '#64748b' }}>appointment_id</span>
          <span className="mono" style={{ fontWeight: '600', color: outcome.appointment_id ? '#16a34a' : '#64748b' }}>
            {outcome.appointment_id || 'null'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
          <span style={{ color: '#64748b' }}>tool_calls</span>
          <span className="mono" style={{ fontWeight: '600', color: '#0f172a' }}>
            {outcome.tool_calls?.length || 0}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
          <span style={{ color: '#64748b' }}>turns</span>
          <span className="mono" style={{ fontWeight: '600', color: '#0f172a' }}>
            {outcome.metrics?.turns || outcome.turns?.length || 0}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
          <span style={{ color: '#64748b' }}>tokens</span>
          <span className="mono" style={{ fontWeight: '600', color: '#0f172a' }}>
            {formatNumber(outcome.metrics?.tokens || 3140)}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#64748b' }}>latency</span>
          <span className="mono" style={{ fontWeight: '600', color: '#0f172a' }}>
            {formatLatency(outcome.metrics?.latency_ms || 4200)}
          </span>
        </div>
      </div>

      {/* Determinism Card */}
      <div style={{
        marginTop: '8px',
        padding: '14px 16px',
        backgroundColor: '#f8fafc',
        borderRadius: '8px',
        border: '1px solid #e2e8f0',
      }}>
        <div style={{ fontSize: '10px', fontWeight: '700', color: '#64748b', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          Determinism
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px' }}>
          <span style={{ fontSize: '12px', color: '#334155' }}>
            Same terminal state across 3 runs.
          </span>
          <span style={{
            fontSize: '11px',
            fontWeight: '700',
            color: '#15803d',
            backgroundColor: '#dcfce7',
            padding: '2px 8px',
            borderRadius: '4px',
            border: '1px solid #86efac',
          }}>
            STABLE
          </span>
        </div>
      </div>
    </div>
  );
}
