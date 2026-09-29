const form = document.querySelector('#chat-form');
const input = document.querySelector('#message-input');
const messages = document.querySelector('#messages');
const sendButton = document.querySelector('#send-button');
const newChat = document.querySelector('#new-chat');
let sessionId = crypto.randomUUID();
let userId = localStorage.getItem('mint-chat-user-id');
if (!userId) {
  userId = crypto.randomUUID();
  localStorage.setItem('mint-chat-user-id', userId);
}

function addMessage(role, text) {
  document.querySelector('.welcome-message')?.remove();
  const message = document.createElement('div');
  message.className = `message ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = text;
  message.appendChild(bubble);
  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
  return message;
}

function resetChat() {
  sessionId = crypto.randomUUID();
  messages.innerHTML = '<div class="welcome-message"><div class="welcome-icon">✦</div><h2>What’s on your mind?</h2><p>Ask a question, explore an idea, or get help with your next task.</p></div>';
}

async function sendMessage(event) {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || sendButton.disabled) return;
  addMessage('user', message);
  input.value = '';
  sendButton.disabled = true;
  const loading = addMessage('assistant', 'Thinking…');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message, session_id: sessionId, user_id: userId}) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
    sessionId = data.session_id;
    loading.querySelector('.message-bubble').textContent = data.reply;
  } catch (error) {
    loading.querySelector('.message-bubble').textContent = error.message;
  } finally { sendButton.disabled = false; input.focus(); }
}

form.addEventListener('submit', sendMessage);
newChat.addEventListener('click', resetChat);
document.querySelectorAll('[data-prompt]').forEach((button) => button.addEventListener('click', () => { input.value = button.dataset.prompt; input.focus(); }));
input.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });