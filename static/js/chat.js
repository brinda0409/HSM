document.addEventListener('DOMContentLoaded', () => {
    const aiChatBox = document.getElementById('aiChatBox');
    const aiInput = document.getElementById('aiInput');
    const aiSendBtn = document.getElementById('aiSendBtn');
    const studentSelect = document.getElementById('studentSelect');
    const tenantSelect = document.getElementById('tenantSelect');
    const studentNameElem = document.getElementById('studentName');
    const cardStudentNameElem = document.getElementById('cardStudentName');
    const userAvatarElem = document.getElementById('userAvatar');
    const pricingModal = document.getElementById('pricingModal');

    // Initial load
    loadStudentVaultData();

    if (studentSelect) {
        studentSelect.addEventListener('change', () => {
            const selectedOption = studentSelect.options[studentSelect.selectedIndex].text;
            const name = selectedOption.split(' (')[0];
            studentNameElem.textContent = name;
            cardStudentNameElem.textContent = name;
            userAvatarElem.textContent = name.charAt(0);
            loadStudentVaultData();
        });
    }

    if (tenantSelect) {
        tenantSelect.addEventListener('change', () => {
            const tenantName = tenantSelect.options[tenantSelect.selectedIndex].text;
            addActivityFeedItem(`Switched HSM Tenant to: ${tenantName}`);
            loadStudentVaultData();
        });
    }

    if (aiInput) {
        aiInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    if (aiSendBtn) {
        aiSendBtn.addEventListener('click', sendChatMessage);
    }

    window.openPricingModal = () => {
        if (pricingModal) pricingModal.style.display = 'flex';
    };

    window.closePricingModal = () => {
        if (pricingModal) pricingModal.style.display = 'none';
    };

    window.sendQuickPrompt = (promptText) => {
        if (aiInput) {
            aiInput.value = promptText;
            sendChatMessage();
        }
    };

    window.resetDemoData = async () => {
        if (confirm("Reset and re-seed database with fresh sample records?")) {
            location.reload();
        }
    };

    async function sendChatMessage() {
        const text = aiInput.value.trim();
        if (!text) return;

        const studentId = parseInt(studentSelect.value, 10) || 1;
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Append User Message
        appendChatBubble('user', text, timeStr);
        aiInput.value = '';

        // Add Activity item
        addActivityFeedItem(`Submitted AI query: "${text.substring(0, 30)}..."`);

        // Typing indicator
        const typingElem = document.createElement('div');
        typingElem.className = 'chat-msg agent';
        typingElem.style.opacity = '0.7';
        typingElem.innerHTML = '⚡ <em>HSM AI Agents orchestrating response...</em>';
        aiChatBox.appendChild(typingElem);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    student_id: studentId
                })
            });

            const data = await response.json();
            typingElem.remove();

            if (data.success) {
                const agentsList = (data.agents_invoked || []).join(' + ') || 'Decision Agent';
                const meta = `⚡ Orchestrated via ${agentsList}`;
                appendChatBubble('agent', data.message, timeStr, meta);
                // Refresh vault cards after action
                loadStudentVaultData();
            } else {
                appendChatBubble('agent', `⚠️ Error: ${data.message || 'Processing error'}`, timeStr, 'System Error');
            }
        } catch (err) {
            typingElem.remove();
            appendChatBubble('agent', `❌ Network error connecting to HSM server.`, timeStr, 'Connection Error');
        }

        scrollToBottom();
    }

    function appendChatBubble(sender, text, timestamp, meta = null) {
        if (!aiChatBox) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${sender}`;

        if (meta) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'chat-meta';
            metaDiv.textContent = meta;
            msgDiv.appendChild(metaDiv);
        }

        const bodyDiv = document.createElement('div');
        bodyDiv.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        msgDiv.appendChild(bodyDiv);

        aiChatBox.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        if (aiChatBox) aiChatBox.scrollTop = aiChatBox.scrollHeight;
    }

    async function loadStudentVaultData() {
        const studentId = parseInt(studentSelect ? studentSelect.value : 1, 10) || 1;
        const listContainer = document.getElementById('complaintItemsList');
        if (!listContainer) return;

        listContainer.innerHTML = '<div style="font-size:0.8rem; color:#94a3b8;">Loading vault records...</div>';

        try {
            const res = await fetch(`/api/complaints?student_id=${studentId}`);
            const data = await res.json();

            if (data.success && data.data.complaints) {
                const complaints = data.data.complaints;
                document.getElementById('complaintsCnt').textContent = complaints.length || 0;

                listContainer.innerHTML = '';
                if (complaints.length === 0) {
                    listContainer.innerHTML = '<div style="font-size:0.8rem; color:#94a3b8;">No active complaints registered.</div>';
                    return;
                }

                complaints.forEach(c => {
                    const row = document.createElement('div');
                    row.className = 'item-row';
                    row.innerHTML = `
                        <div class="item-main">
                            <h5>${c.category} — ${c.priority} Priority</h5>
                            <p>${c.description}</p>
                            <div class="item-hash">Ref: ${c.complaint_id} | Status: ${c.status}</div>
                        </div>
                        <span class="item-status-icon">✓</span>
                    `;
                    listContainer.appendChild(row);
                });
            }
        } catch (e) {
            listContainer.innerHTML = '<div style="font-size:0.8rem; color:#ef4444;">Failed to load vault records.</div>';
        }
    }

    function addActivityFeedItem(actionText) {
        const feed = document.getElementById('activityFeed');
        if (!feed) return;

        const item = document.createElement('div');
        item.className = 'act-item';
        item.innerHTML = `
            <div class="act-check">✓</div>
            <div class="act-content">
                <p>${actionText}</p>
                <span class="act-time">Just now</span>
            </div>
        `;
        feed.insertBefore(item, feed.firstChild);
    }
});
