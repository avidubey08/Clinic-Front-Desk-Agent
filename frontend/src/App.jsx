import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import HandoffQueue from './components/HandoffQueue';
import ConversationDetail from './components/ConversationDetail';
import LiveChatModal from './components/LiveChatModal';

export default function App() {
  const [activeScreen, setActiveScreen] = useState('queue');
  const [selectedConversationId, setSelectedConversationId] = useState('cv_4471');
  const [isLiveChatOpen, setIsLiveChatOpen] = useState(false);

  const handleSelectConversation = (id) => {
    setSelectedConversationId(id);
    setActiveScreen('detail');
  };

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', backgroundColor: '#f8fafc', position: 'relative' }}>
      {/* Persistent Shared Sidebar across both screens */}
      <Sidebar
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
      />

      {/* Screen 1: Handoff Queue */}
      {activeScreen === 'queue' && (
        <HandoffQueue onSelectConversation={handleSelectConversation} />
      )}

      {/* Screen 2: Conversation Detail */}
      {activeScreen === 'detail' && (
        <ConversationDetail
          conversationId={selectedConversationId}
          onBack={() => setActiveScreen('queue')}
        />
      )}

      {/* Floating Action Button: Talk to AI Receptionist */}
      <button
        onClick={() => setIsLiveChatOpen(true)}
        style={{
          position: 'fixed',
          bottom: '28px',
          right: '36px',
          padding: '12px 20px',
          borderRadius: '50px',
          backgroundColor: '#0284c7',
          color: '#ffffff',
          border: 'none',
          boxShadow: '0 10px 15px -3px rgba(2, 132, 199, 0.4)',
          fontSize: '13px',
          fontWeight: '700',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          transition: 'transform 0.15s, background-color 0.15s',
          zIndex: 100,
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.04)')}
        onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
      >
        <span>📞</span>
        <span>Talk to AI Receptionist</span>
      </button>

      {/* Live Interactive Chat Simulator Modal */}
      <LiveChatModal
        isOpen={isLiveChatOpen}
        onClose={() => setIsLiveChatOpen(false)}
      />
    </div>
  );
}
