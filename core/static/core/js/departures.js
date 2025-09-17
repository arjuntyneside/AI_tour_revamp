// Status filter functionality
function filterByStatus(status) {
    const currentUrl = new URL(window.location);
    if (status) {
        currentUrl.searchParams.set('status', status);
    } else {
        currentUrl.searchParams.delete('status');
    }
    window.location.href = currentUrl.toString();
}

// Modal functionality - Enhanced version
function showRecommendationDetails(insightTitle, recTitle, recDescription, recAction, recImpact, recTimeline, implementationSteps, expectedOutcome) {
    const modal = document.getElementById('recommendationModal');
    const modalContent = document.getElementById('modalContent');
    
    let stepsHtml = '';
    if (implementationSteps && implementationSteps.length > 0) {
        stepsHtml = '<div class="implementation-steps"><h5>Implementation Steps:</h5><ol>';
        implementationSteps.forEach(step => {
            stepsHtml += '<li>' + step + '</li>';
        });
        stepsHtml += '</ol></div>';
    }
    
    const content = `
        <div class="recommendation-details">
            <div class="rec-header">
                <h3>${recTitle}</h3>
                <div class="rec-meta-badges">
                    <span class="impact-badge impact-${recImpact.toLowerCase()}">${recImpact} Impact</span>
                    <span class="timeline-badge">${recTimeline}</span>
                </div>
            </div>
            
            <div class="rec-section">
                <h4>📋 Description</h4>
                <p>${recDescription}</p>
            </div>
            
            <div class="rec-section">
                <h4>⚡ Action Required</h4>
                <p>${recAction}</p>
            </div>
            
            ${stepsHtml}
            
            <div class="rec-section">
                <h4>📊 Expected Outcome</h4>
                <p>${expectedOutcome}</p>
            </div>
            
            <div class="rec-section">
                <h4>🔗 Related Insight</h4>
                <p>This recommendation is part of: <strong>${insightTitle}</strong></p>
            </div>
        </div>
        
        <div class="modal-actions">
            <button class="btn btn-primary" onclick="closeModal()">Got it!</button>
            <button class="btn btn-outline" onclick="closeModal()">Dismiss</button>
        </div>
    `;
    
    modalContent.innerHTML = content;
    modal.style.display = 'block';
}

// Close modal functionality
function closeModal() {
    const modal = document.getElementById('recommendationModal');
    modal.style.display = 'none';
}

// AI Chat functionality
function toggleAIChat() {
    const content = document.getElementById('aiChatContent');
    const btn = document.querySelector('.btn-ai');
    const btnText = btn.querySelector('.btn-text');
    const btnIcon = btn.querySelector('.btn-icon');
    
    if (content.style.display === 'none') {
        // Show AI chat
        content.style.display = 'block';
        btnText.textContent = 'Hide Assistant';
        btnIcon.textContent = '👁️';
        showWelcomeMessage();
        
        // Focus on input
        setTimeout(() => {
            document.getElementById('chatInput').focus();
        }, 100);
        
    } else {
        // Hide AI chat
        content.style.display = 'none';
        btnText.textContent = 'Open AI Chat';
        btnIcon.textContent = '📋';
    }
}

function showWelcomeMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="message ai-message">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="message-text">
                    <p>Hello! I'm your AI financial assistant. I can analyze your tour and departure performance, provide insights, and answer questions about your finances.</p>
                    <p><strong>Try asking me:</strong></p>
                    <ul>
                        <li>Analyze my tour financial performance</li>
                        <li>Which departures are most profitable?</li>
                        <li>What pricing strategies should I consider?</li>
                        <li>How can I improve my breakeven points?</li>
                    </ul>
                </div>
                <div class="message-time">Just now</div>
            </div>
        </div>
    `;
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function sendSuggestion(text) {
    document.getElementById('chatInput').value = text;
    sendChatMessage();
}

function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message
    addMessage(message, 'user');
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to AI (AJAX call)
    fetch('/ai-chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        if (data.success) {
            addMessage(data.response, 'ai');
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'ai');
        }
    })
    .catch(error => {
        hideTypingIndicator();
        addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'ai');
        console.error('Error:', error);
    });
}

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = sender === 'ai' ? '🤖' : '👤';
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${formatMessage(text)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatMessage(text) {
    // Convert line breaks to <br> tags
    return text.replace(/\n/g, '<br>');
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message';
    typingDiv.id = 'typingIndicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                AI is thinking
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Rule-based insights functionality
function toggleRuleBasedInsights() {
    const content = document.getElementById('ruleBasedInsightsContent');
    const btn = document.querySelector('.btn-insights');
    const btnText = btn.querySelector('.btn-text');
    const btnIcon = btn.querySelector('.btn-icon-img');
    
    if (content.style.display === 'none') {
        // Show rule-based insights
        content.style.display = 'block';
        btnText.textContent = 'Hide Analysis';
        // Change the icon to an eye icon (we'll use a simple approach)
        btnIcon.style.filter = 'brightness(0) invert(1)';
    } else {
        // Hide rule-based insights
        content.style.display = 'none';
        btnText.textContent = 'View Analysis';
        // Reset the icon
        btnIcon.style.filter = 'brightness(0) invert(1)';
    }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Close modal with X button
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.onclick = closeModal;
    }
    
    // Modal click outside to close
    window.onclick = function(event) {
        const modal = document.getElementById('recommendationModal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    }
});