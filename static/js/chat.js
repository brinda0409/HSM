/**
 * Smart Hostel Management System - Student Portal Client Logic
 * Features: Client-Side Caching, Skeleton Loaders, Optimistic UI Updates, Toasting
 */

// Client-Side In-Memory Cache with TTL (45s)
class ClientCache {
    constructor(ttlMs = 45000) {
        this.cache = new Map();
        this.ttlMs = ttlMs;
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        if (Date.now() > item.expiry) {
            this.cache.delete(key);
            return null;
        }
        return item.value;
    }

    set(key, value) {
        this.cache.set(key, {
            value,
            expiry: Date.now() + this.ttlMs
        });
    }

    invalidate(prefix = '') {
        if (!prefix) {
            this.cache.clear();
            return;
        }
        for (const key of this.cache.keys()) {
            if (key.startsWith(prefix)) {
                this.cache.delete(key);
            }
        }
    }
}

const apiCache = new ClientCache();

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'toast-error' : ''}`;
    toast.innerHTML = `
        <svg class="svg-icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.2s ease';
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    const aiChatBox = document.getElementById('aiChatBox');
    const aiInput = document.getElementById('aiInput');
    const aiSendBtn = document.getElementById('aiSendBtn');
    const studentSelect = document.getElementById('studentSelect');
    const tenantSelect = document.getElementById('tenantSelect');
    const studentNameElem = document.getElementById('studentName');
    const cardStudentNameElem = document.getElementById('cardStudentName');
    const userAvatarElem = document.getElementById('userAvatar');

    // Initial load
    loadStudentPortalData();

    if (studentSelect) {
        studentSelect.addEventListener('change', () => {
            const selectedOption = studentSelect.options[studentSelect.selectedIndex].text;
            const name = selectedOption.split(' (')[0];
            if (studentNameElem) studentNameElem.textContent = name;
            if (cardStudentNameElem) cardStudentNameElem.textContent = name;
            if (userAvatarElem) userAvatarElem.textContent = name.charAt(0);
            
            showToast(`Switched active profile to ${name}`, 'info');
            loadStudentPortalData();
        });
    }

    if (tenantSelect) {
        tenantSelect.addEventListener('change', () => {
            const tenantName = tenantSelect.options[tenantSelect.selectedIndex].text;
            addActivityFeedItem(`Switched Hostel Block to: ${tenantName}`);
            showToast(`Selected ${tenantName}`, 'info');
            loadStudentPortalData();
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

    window.sendQuickPrompt = (promptText) => {
        if (aiInput) {
            aiInput.value = promptText;
            sendChatMessage();
        }
    };

    window.resetDemoData = async () => {
        apiCache.invalidate();
        showToast("Refreshing database records...", "info");
        location.reload();
    };

    window.filterView = (viewType) => {
        showToast(`Filtered view: ${viewType}`, 'info');
    };

    window.focusAiConsole = () => {
        if (aiInput) aiInput.focus();
    };

    async function sendChatMessage() {
        const text = aiInput.value.trim();
        if (!text) return;

        const studentId = parseInt(studentSelect ? studentSelect.value : 1, 10) || 1;
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // 1. Optimistic UI Update in Chat Window
        appendChatBubble('user', text, timeStr);
        aiInput.value = '';

        // Add Activity Feed Item
        addActivityFeedItem(`Submitted query: "${text.substring(0, 28)}..."`);

        // 2. Check for Optimistic Complaints insertion if user says "light", "broken", "ac", "water", "pipe"
        const textLower = text.toLowerCase();
        let optimisticComplaintId = null;
        if (textLower.includes('broken') || textLower.includes('light') || textLower.includes('ac') || textLower.includes('leak')) {
            optimisticComplaintId = renderOptimisticComplaint(text);
        }

        // Display Skeleton / Thinking Indicator
        const typingElem = document.createElement('div');
        typingElem.className = 'chat-msg agent';
        typingElem.style.opacity = '0.85';
        typingElem.innerHTML = `
            <div class="chat-meta" style="display:inline-flex; align-items:center; gap:0.3rem;">
                <svg class="svg-icon icon-sm" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 15h.01M16 15h.01"/></svg>
                Processing...
            </div>
            <div style="margin-top:0.4rem;" class="skeleton-text skeleton-dark"></div>
        `;
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
                const meta = `Orchestrated via ${agentsList}`;
                appendChatBubble('agent', data.message, timeStr, meta);

                // Invalidate complaints cache & re-fetch to reflect changes
                apiCache.invalidate(`complaints_${studentId}`);
                loadStudentPortalData(true);
            } else {
                if (optimisticComplaintId) removeOptimisticComplaint(optimisticComplaintId);
                appendChatBubble('agent', `Warning: ${data.message || 'Unable to process request.'}`, timeStr, 'System Warning');
            }
        } catch (err) {
            typingElem.remove();
            if (optimisticComplaintId) removeOptimisticComplaint(optimisticComplaintId);
            appendChatBubble('agent', `Network error connecting to Hostel AI server.`, timeStr, 'Connection Error');
            showToast("Network error. Please check server connection.", "error");
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
            metaDiv.innerHTML = `
                <svg class="svg-icon icon-sm" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                <span>${meta}</span>
            `;
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

    async function loadStudentPortalData(skipSkeleton = false) {
        const studentId = parseInt(studentSelect ? studentSelect.value : 1, 10) || 1;
        const listContainer = document.getElementById('complaintItemsList');
        if (!listContainer) return;

        const cacheKey = `complaints_${studentId}`;
        const cachedData = apiCache.get(cacheKey);

        if (cachedData) {
            renderComplaintsList(cachedData.complaints);
            return;
        }

        // Show Skeleton Loaders before data arrives
        if (!skipSkeleton) {
            renderSkeletonList(listContainer);
        }

        try {
            const res = await fetch(`/api/complaints?student_id=${studentId}`);
            const data = await res.json();

            if (data.success && data.data.complaints) {
                apiCache.set(cacheKey, data.data);
                renderComplaintsList(data.data.complaints);
            }
        } catch (e) {
            listContainer.innerHTML = '<div style="font-size:0.8rem; color:#ef4444; padding:0.5rem;">Failed to load complaint records.</div>';
        }
    }

    function renderSkeletonList(container) {
        container.innerHTML = `
            <div class="skeleton-row skeleton"></div>
            <div class="skeleton-row skeleton"></div>
        `;
    }

    function renderComplaintsList(complaints) {
        const listContainer = document.getElementById('complaintItemsList');
        const complaintsCnt = document.getElementById('complaintsCnt');

        if (complaintsCnt) complaintsCnt.textContent = complaints.length || 0;
        if (!listContainer) return;

        listContainer.innerHTML = '';
        if (!complaints || complaints.length === 0) {
            listContainer.innerHTML = '<div style="font-size:0.8rem; color:#94a3b8; padding:0.5rem;">No active complaints registered.</div>';
            return;
        }

        complaints.forEach(c => {
            const row = document.createElement('div');
            row.className = 'item-row';
            row.id = `complaint-${c.complaint_id}`;
            row.innerHTML = `
                <div class="item-main">
                    <h5>${c.category} — ${c.priority} Priority</h5>
                    <p>${c.description}</p>
                    <div class="item-hash">Ref: ${c.complaint_id} | Status: ${c.status}</div>
                </div>
                <span class="badge-mint-tag">${c.status}</span>
            `;
            listContainer.appendChild(row);
        });
    }

    function renderOptimisticComplaint(description) {
        const listContainer = document.getElementById('complaintItemsList');
        if (!listContainer) return null;

        const optId = 'opt-' + Date.now();
        const row = document.createElement('div');
        row.className = 'item-row';
        row.id = `complaint-${optId}`;
        row.style.borderLeft = '3px solid var(--mint-accent)';
        row.innerHTML = `
            <div class="item-main">
                <h5>Maintenance Request (Syncing...)</h5>
                <p>${description}</p>
                <div class="item-hash">Ref: ${optId} | Status: Logging...</div>
            </div>
            <span class="badge-mint-tag" style="background:#fef3c7; color:#b45309;">SAVING</span>
        `;
        listContainer.insertBefore(row, listContainer.firstChild);

        const complaintsCnt = document.getElementById('complaintsCnt');
        if (complaintsCnt) {
            const current = parseInt(complaintsCnt.textContent, 10) || 0;
            complaintsCnt.textContent = current + 1;
        }
        return optId;
    }

    function removeOptimisticComplaint(optId) {
        const elem = document.getElementById(`complaint-${optId}`);
        if (elem) elem.remove();
    }

    function addActivityFeedItem(actionText) {
        const feed = document.getElementById('activityFeed');
        if (!feed) return;

        const item = document.createElement('div');
        item.className = 'act-item';
        item.innerHTML = `
            <div class="act-check">
                <svg class="svg-icon icon-sm" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <div class="act-content">
                <p>${actionText}</p>
                <span class="act-time">Just now</span>
            </div>
        `;
        feed.insertBefore(item, feed.firstChild);
    }
});
