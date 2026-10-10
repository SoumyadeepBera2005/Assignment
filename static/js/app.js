let currentSessionId = "session_" + Math.random().toString(36).substring(2, 9);
let isRecognizing = false;
let recognition = null;

// Initialize Speech Recognition if supported
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('user-input').value = transcript;
        sendMessage();
    };

    recognition.onend = function() {
        isRecognizing = false;
        document.getElementById('mic-btn').style.background = 'rgba(255, 255, 255, 0.05)';
    };

    recognition.onerror = function() {
        isRecognizing = false;
        document.getElementById('mic-btn').style.background = 'rgba(255, 255, 255, 0.05)';
    };
}

function toggleMic() {
    if (!recognition) {
        alert("Speech recognition is not supported in your browser.");
        return;
    }
    if (isRecognizing) {
        recognition.stop();
        isRecognizing = false;
        document.getElementById('mic-btn').style.background = 'rgba(255, 255, 255, 0.05)';
    } else {
        recognition.start();
        isRecognizing = true;
        document.getElementById('mic-btn').style.background = 'rgba(230, 0, 0, 0.8)';
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendQuick(text) {
    document.getElementById('user-input').value = text;
    sendMessage();
}

async function sendMessage() {
    const inputEl = document.getElementById('user-input');
    const utterance = inputEl.value.trim();
    if (!utterance) return;

    inputEl.value = '';

    // Append user message to chat history
    appendMessage('user', 'Customer', utterance);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                customer_utterance: utterance
            })
        });

        const data = await response.json();

        // Append assistant message
        appendMessage('assistant', 'Priya (AI Voice Agent)', data.agent_response);

        // Text To Speech Output
        speakAgentResponse(data.agent_response);

        // Update State & Checklist UI
        updateUI(data.state, data.action);

        // Update RAG Inspector
        if (data.rag_context_used) {
            document.getElementById('rag-inspector').innerText = data.rag_context_used;
        }

    } catch (err) {
        console.error("Error sending message:", err);
    }
}

function speakAgentResponse(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Stop ongoing speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.1; // Friendly female voice pitch
        window.speechSynthesis.speak(utterance);
    }
}

function appendMessage(role, sender, text) {
    const historyEl = document.getElementById('chat-history');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    msgDiv.innerHTML = `
        <div class="message-sender">${sender}</div>
        <div>${text}</div>
    `;

    historyEl.appendChild(msgDiv);
    historyEl.scrollTop = historyEl.scrollHeight;
}

function updateUI(state, action) {
    // 1. Update checklist items
    updateCheckitem("property_type", state.property_type);
    updateCheckitem("ownership", state.ownership);
    
    let docStr = state.documents === true ? "Original Available" : (state.documents === false ? "Unavailable" : null);
    updateCheckitem("documents", docStr);

    let amtStr = state.loan_amount ? `₹${(state.loan_amount / 100000).toFixed(0)} Lakh` : null;
    updateCheckitem("loan_amount", amtStr);

    let occStr = (state.occupation && state.income_mode) ? `${state.occupation} (${state.income_mode})` : null;
    updateCheckitem("occupation_and_income", occStr);

    let valStr = state.market_value ? `₹${(state.market_value / 100000).toFixed(0)} Lakh` : null;
    updateCheckitem("market_value", valStr);

    let tenureStr = state.tenure ? `${state.tenure} Years` : null;
    updateCheckitem("tenure", tenureStr);

    // 2. Count completed items
    const missingCount = state.unanswered_fields.length;
    const completedCount = 7 - missingCount;
    document.getElementById('completion-counter').innerText = `${completedCount} / 7`;

    // 3. Update Status Box
    const statusEl = document.getElementById('flow-status');
    if (action === "HANDOFF") {
        statusEl.innerText = "✅ SENIOR EXPERT HANDOFF";
        statusEl.style.color = "var(--success-green)";
    } else if (action === "DISQUALIFIED") {
        statusEl.innerText = "❌ DISQUALIFIED";
        statusEl.style.color = "var(--danger-red)";
    } else if (action === "TRANSFER") {
        statusEl.innerText = "🔄 TRANSFER SPECIALIST";
        statusEl.style.color = "var(--accent-blue)";
    } else if (action === "CALLBACK") {
        statusEl.innerText = "📅 CALLBACK SCHEDULED";
        statusEl.style.color = "var(--warning-orange)";
    } else {
        statusEl.innerText = "IN PROGRESS";
        statusEl.style.color = "var(--primary-gold)";
    }
}

function updateCheckitem(id, value) {
    const badgeEl = document.getElementById(`badge-${id}`);
    const valEl = document.getElementById(`val-${id}`);
    const itemEl = document.getElementById(`item-${id}`);

    if (value) {
        valEl.innerText = value;
        badgeEl.innerText = "Passed";
        badgeEl.className = "badge badge-passed";
        itemEl.className = "checklist-item passed";
    } else {
        badgeEl.innerText = "Pending";
        badgeEl.className = "badge badge-pending";
        itemEl.className = "checklist-item missing";
    }
}

async function resetConversation() {
    try {
        await fetch('/api/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId })
        });

        document.getElementById('chat-history').innerHTML = `
            <div class="message assistant">
                <div class="message-sender">Priya (AI Voice Agent)</div>
                Hello! I am Priya calling from Home Credit regarding your pre-approved Loan Against Property offer of up to ₹75 Lakh. Do you have a couple of minutes to discuss?
            </div>
        `;

        document.getElementById('flow-status').innerText = "IN PROGRESS";
        document.getElementById('flow-status').style.color = "var(--primary-gold)";
        document.getElementById('completion-counter').innerText = "0 / 7";

        ["property_type", "ownership", "documents", "loan_amount", "occupation_and_income", "market_value", "tenure"].forEach(id => {
            document.getElementById(`badge-${id}`).innerText = "Pending";
            document.getElementById(`badge-${id}`).className = "badge badge-pending";
            document.getElementById(`item-${id}`).className = "checklist-item missing";
        });

        document.getElementById('rag-inspector').innerText = "No product RAG query triggered yet.";

    } catch (err) {
        console.error("Error resetting session:", err);
    }
}

async function runTestMatrix() {
    const modal = document.getElementById('test-modal');
    const grid = document.getElementById('test-grid');
    const summary = document.getElementById('test-summary');

    modal.style.display = 'flex';
    summary.innerText = "Running 16 automated test matrix scenarios...";
    grid.innerHTML = '<div style="color: var(--text-secondary);">Executing tests...</div>';

    try {
        const response = await fetch('/api/run-tests', { method: 'POST' });
        const data = await response.json();

        summary.innerHTML = `
            <strong>Test Suite Summary:</strong> Total: ${data.total} | 
            <span style="color: var(--success-green);">Passed: ${data.passed}</span> | 
            <span style="color: var(--danger-red);">Failed: ${data.failures}</span>
        `;

        grid.innerHTML = '';
        data.results.forEach((t, i) => {
            const item = document.createElement('div');
            item.className = `test-item ${t.passed ? 'passed' : 'failed'}`;
            item.innerHTML = `
                <div>
                    <strong>Test ${i + 1}: ${t.name}</strong>
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">${t.description}</div>
                </div>
                <span class="badge ${t.passed ? 'badge-passed' : 'badge-disqualified'}">
                    ${t.passed ? 'PASSED' : 'FAILED'}
                </span>
            `;
            grid.appendChild(item);
        });

    } catch (err) {
        grid.innerHTML = '<div style="color: var(--danger-red);">Failed to run test matrix.</div>';
    }
}

function closeTestModal() {
    document.getElementById('test-modal').style.display = 'none';
}
