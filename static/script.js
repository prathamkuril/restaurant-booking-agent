/**
 * Restaurant Booking Chat Interface
 * WebSocket-based real-time chat client
 */

// Generate unique session ID
const sessionId = generateSessionId();
let ws = null;
let isConnected = false;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const typingIndicator = document.getElementById('typing-indicator');
const quickActionButtons = document.querySelectorAll('.quick-action');

/**
 * Generate a unique session ID
 */
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

/**
 * Connect to WebSocket server
 */
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        isConnected = true;
        reconnectAttempts = 0;
        sendButton.disabled = false;
        messageInput.disabled = false;
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleServerMessage(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('Error connecting to server. Please refresh the page.', 'error');
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        isConnected = false;
        sendButton.disabled = true;
        messageInput.disabled = true;
        
        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Reconnecting... (attempt ${reconnectAttempts})`);
            setTimeout(connectWebSocket, 2000 * reconnectAttempts);
        } else {
            addMessage('Connection lost. Please refresh the page.', 'error');
        }
    };
}

/**
 * Handle messages from server
 */
function handleServerMessage(data) {
    switch (data.type) {
        case 'system':
            // System messages are already shown in HTML
            break;
        case 'typing':
            showTypingIndicator();
            break;
        case 'response':
            hideTypingIndicator();
            addMessage(data.content, 'assistant');
            break;
        case 'error':
            hideTypingIndicator();
            addMessage(data.content, 'error');
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

/**
 * Send message to server
 */
function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) return;
    if (!isConnected) {
        addMessage('Not connected to server. Please wait...', 'error');
        return;
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Send to server
    ws.send(JSON.stringify({ message }));
    
    // Clear input
    messageInput.value = '';
    messageInput.focus();
}

/**
 * Add message to chat
 */
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Parse and format content
    contentDiv.innerHTML = formatMessage(content);
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Format message content
 */
function formatMessage(content) {
    // Convert markdown-style formatting
    content = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>')
        .replace(/• /g, '▪ ');
    
    // Format booking references
    content = content.replace(/\b([A-Z]{3}\d{4})\b/g, '<strong class="booking-ref">$1</strong>');
    
    // Format dates and times
    content = content.replace(/\b(\d{4}-\d{2}-\d{2})\b/g, '<span class="date">$1</span>');
    content = content.replace(/\b(\d{2}:\d{2}(:\d{2})?)\b/g, '<span class="time">$1</span>');
    
    return content;
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

/**
 * Handle quick action buttons
 */
function handleQuickAction(event) {
    const message = event.target.dataset.message;
    if (message) {
        messageInput.value = message;
        sendMessage();
    }
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    // Send button click
    sendButton.addEventListener('click', sendMessage);
    
    // Enter key in input
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Quick action buttons
    quickActionButtons.forEach(button => {
        button.addEventListener('click', handleQuickAction);
    });
}

/**
 * Initialize application
 */
function initialize() {
    console.log('Initializing chat interface...');
    console.log('Session ID:', sessionId);
    
    initializeEventListeners();
    connectWebSocket();
    
    // Focus on input
    messageInput.focus();
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}

// Add custom styles for formatted content
const style = document.createElement('style');
style.textContent = `
    .booking-ref {
        background: #e3f2fd;
        padding: 2px 6px;
        border-radius: 4px;
        color: #1976d2;
        font-family: monospace;
    }
    
    .date {
        color: #388e3c;
        font-weight: 500;
    }
    
    .time {
        color: #f57c00;
        font-weight: 500;
    }
    
    .message-content code {
        background: #f5f5f5;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: monospace;
        font-size: 0.9em;
    }
`;
document.head.appendChild(style);