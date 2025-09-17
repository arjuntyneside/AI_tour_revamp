// Departures-specific JavaScript extracted from departures.html
// AI Chat functionality
let aiChatOpen = false;

function toggleAIChat() {
    const chatContent = document.getElementById('aiChatContent');
    const btn = document.querySelector('.btn-ai .btn-text');
    
    if (aiChatOpen) {
        chatContent.style.display = 'none';
        btn.textContent = 'Open AI Chat';
        aiChatOpen = false;
    } else {
        chatContent.style.display = 'block';
        btn.textContent = 'Close AI Chat';
        aiChatOpen = true;
        
        // Add welcome message if chat is empty
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages.children.length === 0) {
            addWelcomeMessage();
        }
    }
}

function addWelcomeMessage() {
    const chatMessages = document.getElementById('chatMessages');
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'message ai-message';
    welcomeDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="ai-avatar">🤖</span>
                <span class="sender">AI Assistant</span>
            </div>
            <div class="message-text">
                Hello! I'm your AI Financial Assistant. I can help you analyze your tour performance, 
                identify profitable opportunities, and provide insights on pricing strategies. 
                What would you like to know about your financial data?
            </div>
        </div>
    `;
    chatMessages.appendChild(welcomeDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    input.value = '';
    
    // Simulate AI response (in real implementation, this would call your AI service)
    setTimeout(() => {
        const response = generateAIResponse(message);
        addMessage(response, 'ai');
    }, 1000);
}

function addMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = sender === 'ai' ? '🤖' : '👤';
    const senderName = sender === 'ai' ? 'AI Assistant' : 'You';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="ai-avatar">${avatar}</span>
                <span class="sender">${senderName}</span>
            </div>
            <div class="message-text">${text}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function generateAIResponse(userMessage) {
    // Simple response generation based on keywords
    const message = userMessage.toLowerCase();
    
    // Get data from window object if available
    const data = window.departuresData || {};
    
    if (message.includes('profit') || message.includes('profitable')) {
        return `Based on your data, I can see that ${data.profitable_count || 0} out of ${data.total_departures || 0} departures are profitable. The average profit margin is ${data.overall_roi || 0}%. Would you like me to analyze specific departures or suggest pricing optimizations?`;
    } else if (message.includes('pricing') || message.includes('price')) {
        return `I can help you optimize pricing strategies. Your current average price per person is $${data.average_price_per_person || 0}. Consider dynamic pricing based on demand and seasonality. Would you like specific recommendations for your tours?`;
    } else if (message.includes('breakeven') || message.includes('break even')) {
        return `Breakeven analysis shows that ${data.breakeven_achieved_count || 0} departures have reached their breakeven point. For departures below breakeven, consider adjusting pricing or reducing costs. Would you like detailed breakeven analysis for specific tours?`;
    } else if (message.includes('revenue') || message.includes('income')) {
        return `Your total revenue across all departures is $${data.total_revenue || 0}. The revenue per departure averages $${data.average_revenue_per_departure || 0}. Would you like me to analyze revenue trends or suggest ways to increase revenue?`;
    } else {
        return "I can help you analyze various aspects of your tour business including profitability, pricing strategies, breakeven analysis, and revenue optimization. What specific area would you like to explore?";
    }
}

function sendSuggestion(suggestion) {
    document.getElementById('chatInput').value = suggestion;
    sendChatMessage();
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

// Rule-based insights functionality
let insightsOpen = false;

function toggleRuleBasedInsights() {
    const insightsContent = document.getElementById('ruleBasedInsightsContent');
    const btn = document.querySelector('.btn-insights .btn-text');
    
    if (insightsOpen) {
        insightsContent.style.display = 'none';
        btn.textContent = 'View Analysis';
        insightsOpen = false;
    } else {
        insightsContent.style.display = 'block';
        btn.textContent = 'Hide Analysis';
        insightsOpen = true;
    }
}

// Status filtering functionality
function filterByStatus(status) {
    const rows = document.querySelectorAll('.departure-row');
    
    rows.forEach(row => {
        if (!status || row.classList.contains(`status-${status}`)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Modal functionality
function openRecommendationModal(content) {
    const modal = document.getElementById('recommendationModal');
    const modalContent = document.getElementById('modalContent');
    
    modalContent.innerHTML = content;
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('recommendationModal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('recommendationModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Close modal when clicking the X
document.addEventListener('DOMContentLoaded', function() {
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.onclick = closeModal;
    }
});