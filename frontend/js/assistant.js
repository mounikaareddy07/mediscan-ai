/* MediScan AI - AI Assistant Module
   Chat interface for explaining scan results and health guidance */

let assistantOpen = false;
let chatMessages = [];

// ─── Toggle Assistant Panel ──────────────────────────────────────────
function toggleAssistant() {
    const panel = document.getElementById('assistant-panel');
    if (!panel) return;

    assistantOpen = !assistantOpen;
    if (assistantOpen) {
        panel.classList.add('open');
        // Send welcome message if first open
        if (chatMessages.length === 0) {
            addBotMessage("Hello! 👋 I'm MediScan AI Assistant. I can help you understand your scan results, explain medical conditions, and provide health guidance.\n\nTry asking me:\n• \"Explain my scan result\"\n• \"What is pneumonia?\"\n• \"What precautions should I take?\"");
        }
    } else {
        panel.classList.remove('open');
    }
}

// ─── Send Message ────────────────────────────────────────────────────
async function sendAssistantMessage() {
    const input = document.getElementById('assistant-input');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    // Add user message to chat
    addUserMessage(message);
    input.value = '';

    // Build scan context from last result
    const scanContext = window.lastScanResult ? {
        prediction: window.lastScanResult.prediction,
        risk_score: window.lastScanResult.risk_score,
        confidence: window.lastScanResult.confidence
    } : null;

    try {
        const res = await fetch(`${API_BASE}/api/assistant`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message, scan_context: scanContext })
        });
        const data = await res.json();

        if (data.success) {
            addBotMessage(data.response);
        } else {
            addBotMessage("Sorry, I couldn't process that. Please try again.");
        }
    } catch (err) {
        addBotMessage("Connection error. Please make sure the backend server is running.");
    }
}

// ─── Chat Message Helpers ────────────────────────────────────────────
function addUserMessage(text) {
    chatMessages.push({ type: 'user', text });
    appendChatBubble('user', text);
}

function addBotMessage(text) {
    chatMessages.push({ type: 'bot', text });
    appendChatBubble('bot', text);
}

function appendChatBubble(type, text) {
    const container = document.getElementById('assistant-messages');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = type === 'bot' ? '🤖' : '👤';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    // Simple markdown-like formatting
    bubble.innerHTML = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    container.appendChild(msgDiv);

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// ─── Handle Enter Key ────────────────────────────────────────────────
function handleAssistantKeypress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendAssistantMessage();
    }
}

// ─── Quick Suggestion Click ──────────────────────────────────────────
function askSuggestion(text) {
    const input = document.getElementById('assistant-input');
    if (input) {
        input.value = text;
        sendAssistantMessage();
    }
}

// ─── Render Assistant Panel HTML ─────────────────────────────────────
function getAssistantPanelHTML() {
    return `
    <div id="assistant-panel" class="assistant-panel">
        <div class="assistant-header">
            <div class="assistant-header-left">
                <div class="assistant-avatar">🤖</div>
                <div>
                    <h3>AI Assistant</h3>
                    <p>Online • Ready to help</p>
                </div>
            </div>
            <button class="assistant-close" onclick="toggleAssistant()">✕</button>
        </div>
        <div class="assistant-messages" id="assistant-messages"></div>
        <div class="chat-suggestions">
            <button class="suggestion-chip" onclick="askSuggestion('Explain my scan result')">Explain result</button>
            <button class="suggestion-chip" onclick="askSuggestion('What is pneumonia?')">About Pneumonia</button>
            <button class="suggestion-chip" onclick="askSuggestion('What precautions should I take?')">Precautions</button>
            <button class="suggestion-chip" onclick="askSuggestion('How does the AI work?')">How AI works</button>
        </div>
        <div class="assistant-input-area">
            <input type="text" class="assistant-input" id="assistant-input"
                   placeholder="Ask me anything..." onkeypress="handleAssistantKeypress(event)">
            <button class="assistant-send-btn" onclick="sendAssistantMessage()">➤</button>
        </div>
    </div>
    <button class="assistant-toggle visible" id="assistant-toggle" onclick="toggleAssistant()">💬</button>`;
}
