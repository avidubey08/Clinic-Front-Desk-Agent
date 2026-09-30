export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchHandoffs() {
  const res = await fetch(`${API_BASE}/api/handoffs`);
  if (!res.ok) throw new Error('Failed to fetch handoffs');
  return res.json();
}

export async function resolveHandoff(conversationId) {
  const res = await fetch(`${API_BASE}/api/handoffs/${conversationId}/resolve`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to resolve handoff');
  return res.json();
}

export async function fetchConversations() {
  const res = await fetch(`${API_BASE}/api/conversations`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function fetchConversationDetail(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}`);
  if (!res.ok) throw new Error('Failed to fetch conversation detail');
  return res.json();
}

export async function runAgentConversation(payload) {
  const res = await fetch(`${API_BASE}/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to run agent conversation');
  return res.json();
}
