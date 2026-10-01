const form = document.querySelector('#chat-form');
const input = document.querySelector('#message-input');
const messages = document.querySelector('#messages');
const sendButton = document.querySelector('#send-button');
const newChat = document.querySelector('#new-chat');
const conversationList = document.querySelector('#conversation-list');
let sessionId = crypto.randomUUID();
let conversations = [];
let userId = localStorage.getItem('mint-chat-user-id');
if (!userId) {
  userId = crypto.randomUUID();
  localStorage.setItem('mint-chat-user-id', userId);
}

function renderConversations(items) {
  conversations = items;
  conversationList.replaceChildren();
  if (items.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'history-empty';
    empty.textContent = 'No conversations yet';
    conversationList.appendChild(empty);
    return;
  }

  for (const conversation of items) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'conversation-item';
    button.classList.toggle('active', conversation.session_id === sessionId);
    button.textContent = conversation.title;
    button.addEventListener('click', () => openConversation(conversation.session_id));
    conversationList.appendChild(button);
  }
}

async function refreshConversations() {
  try {
    const params = new URLSearchParams({user_id: userId});
    const response = await fetch(`/api/conversations?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not load conversations.');
    renderConversations(data);
  } catch (error) {
    const empty = document.createElement('p');
    empty.className = 'history-empty';
    empty.textContent = error.message;
    conversationList.replaceChildren(empty);
  }
}

async function openConversation(conversationId) {
  if (sendButton.disabled) return;
  try {
    const params = new URLSearchParams({user_id: userId});
    const response = await fetch(`/api/conversations/${encodeURIComponent(conversationId)}/messages?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not open conversation.');
    sessionId = data.session_id;
    messages.replaceChildren();
    for (const message of data.messages) addMessage(message.role, message.content);
    renderConversations(conversations);
  } catch (error) {
    messages.replaceChildren();
    addMessage('assistant', error.message);
  }
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
  renderConversations(conversations);
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
  } finally {
    sendButton.disabled = false;
    input.focus();
    refreshConversations();
  }
}

form.addEventListener('submit', sendMessage);
newChat.addEventListener('click', resetChat);
document.querySelectorAll('[data-prompt]').forEach((button) => button.addEventListener('click', () => { input.value = button.dataset.prompt; input.focus(); }));
input.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
refreshConversations();