import React from 'react';

export default function Sidebar({ activeScreen, setActiveScreen, openCount = 4 }) {
  return (
    <aside style={{
      width: '72px',
      backgroundColor: '#ffffff',
      borderRight: '1px solid #e2e8f0',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '20px 0',
      gap: '24px',
      flexShrink: 0,
      height: '100vh',
    }}>
      {/* Brand Icon */}
      <div style={{
        width: '42px',
        height: '42px',
        borderRadius: '10px',
        backgroundColor: '#0284c7',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#ffffff',
        fontWeight: '700',
        fontSize: '20px',
        boxShadow: '0 4px 6px -1px rgba(2, 132, 199, 0.2)',
      }}>
        +
      </div>

      {/* Nav Icons */}
      <nav style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        alignItems: 'center',
        width: '100%',
      }}>
        {/* Handoff Queue Tab */}
        <button
          onClick={() => setActiveScreen('queue')}
          title="Handoff Queue"
          style={{
            position: 'relative',
            width: '46px',
            height: '46px',
            borderRadius: '10px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeScreen === 'queue' ? '#e0f2fe' : 'transparent',
            color: activeScreen === 'queue' ? '#0284c7' : '#64748b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
          {openCount > 0 && (
            <span style={{
              position: 'absolute',
              top: '4px',
              right: '4px',
              backgroundColor: '#ef4444',
              color: '#ffffff',
              fontSize: '10px',
              fontWeight: '700',
              borderRadius: '9999px',
              minWidth: '16px',
              height: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 4px',
            }}>
              {openCount}
            </span>
          )}
        </button>

        {/* Conversation Detail Tab */}
        <button
          onClick={() => setActiveScreen('detail')}
          title="Conversation Detail"
          style={{
            width: '46px',
            height: '46px',
            borderRadius: '10px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeScreen === 'detail' ? '#e0f2fe' : 'transparent',
            color: activeScreen === 'detail' ? '#0284c7' : '#64748b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>

        {/* Calendar / Schedule Icon */}
        <button
          onClick={() => setActiveScreen('queue')}
          title="Clinic Calendar"
          style={{
            width: '46px',
            height: '46px',
            borderRadius: '10px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: 'transparent',
            color: '#94a3b8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </button>
      </nav>

      {/* Bottom Status / Hex Icon */}
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', alignItems: 'center' }}>
        <div style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          backgroundColor: '#22c55e',
          boxShadow: '0 0 8px #22c55e',
        }} title="System Online & Deterministic" />
      </div>
    </aside>
  );
}
