/**
 * Smart Hostel Management System - Unified SPA Engine
 * Provides single-link frontend navigation between Student and Warden views with caching,
 * skeleton loaders, optimistic rendering, SVG icons, and toasts.
 */

// Client-Side Cache Layer (45s TTL)
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
        this.cache.set(key, { value, expiry: Date.now() + this.ttlMs });
    }

    invalidate(prefix = '') {
        if (!prefix) {
            this.cache.clear();
            return;
        }
        for (const key of this.cache.keys()) {
            if (key.startsWith(prefix)) this.cache.delete(key);
        }
    }
}

const appCache = new ClientCache();

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
    const viewStudent = document.getElementById('viewStudent');
    const viewWarden = document.getElementById('viewWarden');
    const btnModeStudent = document.getElementById('btnModeStudent');
    const btnModeWarden = document.getElementById('btnModeWarden');

    const aiChatBox = document.getElementById('aiChatBox');
    const aiInput = document.getElementById('aiInput');
    const aiSendBtn = document.getElementById('aiSendBtn');
    const studentSelect = document.getElementById('studentSelect');
    const tenantSelect = document.getElementById('tenantSelect');
    const refreshBtn = document.getElementById('refreshBtn');

    // Initial Session Check
    checkAuthSession();

    async function checkAuthSession() {
        try {
            const res = await fetch('/api/me');
            const data = await res.json();
            if (data.success && data.user) {
                const u = data.user;
                const studentNavGroup = document.getElementById('sidebarStudentNavGroup');
                const wardenNavGroup = document.getElementById('sidebarWardenNavGroup');
                const roleSwitcher = document.getElementById('topbarRoleSwitcher');
                const studentSelectWrap = document.getElementById('studentSelectWrap');

                if (u.role === 'warden') {
                    // Strictly isolate Warden view: Hide student navigation
                    if (studentNavGroup) studentNavGroup.style.display = 'none';
                    if (wardenNavGroup) wardenNavGroup.style.display = 'block';
                    if (roleSwitcher) roleSwitcher.style.display = 'none';
                    if (studentSelectWrap) studentSelectWrap.style.display = 'none';

                    document.getElementById('topAuthText').textContent = `WARDEN: ${u.name.toUpperCase()}`;
                    switchMainView('warden');
                } else if (u.role === 'student') {
                    // Strictly isolate Student view: Hide warden navigation
                    if (studentNavGroup) studentNavGroup.style.display = 'block';
                    if (wardenNavGroup) wardenNavGroup.style.display = 'none';
                    if (roleSwitcher) roleSwitcher.style.display = 'none';
                    if (studentSelectWrap) studentSelectWrap.style.display = 'none';

                    if (studentSelect) studentSelect.value = u.id;
                    const nameElem = document.getElementById('studentName');
                    const cardNameElem = document.getElementById('cardStudentName');
                    const avatarElem = document.getElementById('userAvatar');
                    const topAuthText = document.getElementById('topAuthText');

                    if (nameElem) nameElem.textContent = u.name;
                    if (cardNameElem) cardNameElem.textContent = u.name;
                    if (avatarElem) avatarElem.textContent = u.name.charAt(0);
                    if (topAuthText) topAuthText.textContent = `RESIDENT: ${u.name.toUpperCase()}`;

                    switchMainView('student');
                }
            }
        } catch (e) {
            console.error('Session check error:', e);
        }
    }

    // 1. Single-Link View Switching Engine
    window.switchMainView = (mode, targetTab = null, linkElem = null) => {
        // Update sidebar active link state
        if (linkElem) {
            document.querySelectorAll('.sidebar-nav .nav-link').forEach(l => l.classList.remove('active'));
            linkElem.classList.add('active');
        }

        if (mode === 'student') {
            viewStudent.style.display = 'block';
            viewWarden.style.display = 'none';
            btnModeStudent.classList.add('active');
            btnModeWarden.classList.remove('active');

            document.getElementById('studentSelectWrap').style.display = 'block';
            document.getElementById('topAuthText').textContent = 'STUDENT AUTHENTICATED';

            // Sidebar Profile
            const profileBox = document.getElementById('sidebarProfileBox');
            profileBox.style.background = 'var(--mint-light-bg)';
            profileBox.style.borderColor = '#a7f3d0';
            document.getElementById('sidebarProfileTitle').style.color = 'var(--mint-pill-text)';
            document.getElementById('sidebarProfileTitle').textContent = 'STUDENT PORTAL';
            document.getElementById('sidebarProfileSub').textContent = 'Active Resident';

            loadStudentPortalData();

            if (targetTab === 'complaints') {
                const compElem = document.getElementById('complaintItemsList');
                if (compElem) compElem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else if (targetTab === 'chat') {
                if (aiInput) aiInput.focus();
            }
        } else {
            viewStudent.style.display = 'none';
            viewWarden.style.display = 'block';
            btnModeStudent.classList.remove('active');
            btnModeWarden.classList.add('active');

            document.getElementById('studentSelectWrap').style.display = 'none';
            document.getElementById('topAuthText').textContent = 'WARDEN AUTHENTICATED';

            // Sidebar Profile
            const profileBox = document.getElementById('sidebarProfileBox');
            profileBox.style.background = '#eff6ff';
            profileBox.style.borderColor = '#bfdbfe';
            document.getElementById('sidebarProfileTitle').style.color = '#1d4ed8';
            document.getElementById('sidebarProfileTitle').textContent = 'WARDEN PORTAL';
            document.getElementById('sidebarProfileSub').textContent = 'Administrator';

            if (targetTab) switchWardenTab(targetTab);
            else switchWardenTab('complaints');

            loadWardenDashboardData();
        }
    };

    window.switchWardenTab = (tabName) => {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.style.display = 'none');

        const activeBtn = Array.from(tabBtns).find(b => b.getAttribute('data-tab') === tabName);
        if (activeBtn) activeBtn.classList.add('active');
        const targetContent = document.getElementById(`tab-${tabName}`);
        if (targetContent) targetContent.style.display = 'block';

        // Also update matching sidebar nav link active state
        const sideLink = document.getElementById(`nav-warden-${tabName}`);
        if (sideLink) {
            document.querySelectorAll('.sidebar-nav .nav-link').forEach(l => l.classList.remove('active'));
            sideLink.classList.add('active');
        }
    };

    // Global Refresh
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            appCache.invalidate();
            showToast("Refreshed system data", "info");
            const isWarden = btnModeWarden.classList.contains('active');
            if (isWarden) loadWardenDashboardData();
            else loadStudentPortalData(true);
        });
    }

    if (studentSelect) {
        studentSelect.addEventListener('change', () => {
            const selectedOption = studentSelect.options[studentSelect.selectedIndex].text;
            const name = selectedOption.split(' (')[0];
            const nameElem = document.getElementById('studentName');
            const cardNameElem = document.getElementById('cardStudentName');
            const avatarElem = document.getElementById('userAvatar');

            if (nameElem) nameElem.textContent = name;
            if (cardNameElem) cardNameElem.textContent = name;
            if (avatarElem) avatarElem.textContent = name.charAt(0);

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
        appCache.invalidate();
        showToast("Re-initializing database records...", "info");
        location.reload();
    };

    window.focusAiConsole = () => {
        switchMainView('student');
        if (aiInput) aiInput.focus();
    };

    // -------------------------------------------------------------
    // STUDENT PORTAL ENGINE
    // -------------------------------------------------------------
    async function loadStudentPortalData(skipSkeleton = false) {
        const sId = parseInt(studentSelect ? studentSelect.value : 1, 10) || 1;
        const listContainer = document.getElementById('complaintItemsList');
        if (!listContainer) return;

        const cacheKey = `complaints_${sId}`;
        const cached = appCache.get(cacheKey);

        if (cached) {
            renderStudentComplaints(cached.complaints);
            return;
        }

        if (!skipSkeleton) {
            listContainer.innerHTML = `
                <div class="skeleton-row skeleton"></div>
                <div class="skeleton-row skeleton"></div>
            `;
        }

        try {
            const res = await fetch(`/api/complaints?student_id=${sId}`);
            const data = await res.json();
            if (data.success && data.data.complaints) {
                appCache.set(cacheKey, data.data);
                renderStudentComplaints(data.data.complaints);
            }
        } catch (e) {
            listContainer.innerHTML = '<div style="font-size:0.8rem; color:#ef4444; padding:0.5rem;">Failed to load complaint records.</div>';
        }
    }

    function renderStudentComplaints(complaints) {
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

    async function sendChatMessage() {
        const text = aiInput.value.trim();
        if (!text) return;

        const sId = parseInt(studentSelect ? studentSelect.value : 1, 10) || 1;
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Optimistic UI updates
        appendChatBubble('user', text, timeStr);
        aiInput.value = '';
        addActivityFeedItem(`Submitted query: "${text.substring(0, 28)}..."`);

        const textLower = text.toLowerCase();
        let optId = null;
        if (textLower.includes('broken') || textLower.includes('light') || textLower.includes('ac') || textLower.includes('leak')) {
            optId = renderOptimisticStudentComplaint(text);
        }

        const typingElem = document.createElement('div');
        typingElem.className = 'chat-msg agent';
        typingElem.style.opacity = '0.85';
        typingElem.innerHTML = `
            <div class="chat-meta" style="display:inline-flex; align-items:center; gap:0.3rem;">
                <svg class="svg-icon icon-sm" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 15h.01M16 15h.01"/></svg>
                Processing AI Response...
            </div>
            <div style="margin-top:0.4rem;" class="skeleton-text skeleton-dark"></div>
        `;
        aiChatBox.appendChild(typingElem);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, student_id: sId })
            });

            const data = await response.json();
            typingElem.remove();

            if (data.success) {
                const agentsList = (data.agents_invoked || []).join(' + ') || 'Decision Agent';
                appendChatBubble('agent', data.message, timeStr, `Orchestrated via ${agentsList}`);
                appCache.invalidate(`complaints_${sId}`);
                loadStudentPortalData(true);
            } else {
                if (optId) removeOptimisticStudentComplaint(optId);
                appendChatBubble('agent', `Warning: ${data.message || 'Unable to process request.'}`, timeStr, 'System Warning');
            }
        } catch (err) {
            typingElem.remove();
            if (optId) removeOptimisticStudentComplaint(optId);
            appendChatBubble('agent', `Network error connecting to Hostel AI server.`, timeStr, 'Connection Error');
            showToast("Network error connecting to server", "error");
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

    function renderOptimisticStudentComplaint(desc) {
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
                <p>${desc}</p>
                <div class="item-hash">Ref: ${optId} | Status: Logging...</div>
            </div>
            <span class="badge-mint-tag" style="background:#fef3c7; color:#b45309;">SAVING</span>
        `;
        listContainer.insertBefore(row, listContainer.firstChild);

        const complaintsCnt = document.getElementById('complaintsCnt');
        if (complaintsCnt) {
            const cur = parseInt(complaintsCnt.textContent, 10) || 0;
            complaintsCnt.textContent = cur + 1;
        }
        return optId;
    }

    function removeOptimisticStudentComplaint(optId) {
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

    // -------------------------------------------------------------
    // WARDEN ADMIN ENGINE
    // -------------------------------------------------------------
    async function loadWardenDashboardData() {
        await Promise.all([
            fetchWardenStats(),
            fetchWardenComplaints(),
            fetchWardenLeaves(),
            fetchWardenVisitors(),
            fetchWardenRooms(),
            fetchWardenAuditLogs()
        ]);
    }

    async function fetchWardenStats() {
        const cached = appCache.get('warden_stats');
        if (cached) {
            updateWardenStatsUI(cached);
            return;
        }

        try {
            const res = await fetch('/api/dashboard/stats');
            const result = await res.json();
            if (result.success) {
                appCache.set('warden_stats', result.data);
                updateWardenStatsUI(result.data);
            }
        } catch (e) {
            console.error('Error fetching warden stats:', e);
        }
    }

    function updateWardenStatsUI(s) {
        document.getElementById('statComplaints').textContent = s.open_complaints;
        document.getElementById('statLeaves').textContent = s.pending_leaves;
        document.getElementById('statVisitors').textContent = s.today_visitors;
        document.getElementById('statOccupancy').textContent = `${s.occupancy_pct}%`;
    }

    function renderTableSkeleton(tbodyId, cols = 9, rows = 3) {
        const tbody = document.getElementById(tbodyId);
        if (!tbody) return;
        let html = '';
        for (let i = 0; i < rows; i++) {
            html += `<tr><td colspan="${cols}"><div class="skeleton-row skeleton"></div></td></tr>`;
        }
        tbody.innerHTML = html;
    }

    async function fetchWardenComplaints() {
        const tbody = document.getElementById('complaintsTableBody');
        const cached = appCache.get('warden_complaints');
        if (cached) {
            renderWardenComplaintsTable(cached);
            return;
        }

        renderTableSkeleton('complaintsTableBody', 9, 3);
        try {
            const res = await fetch('/api/complaints');
            const result = await res.json();
            if (result.success && result.data.complaints) {
                appCache.set('warden_complaints', result.data.complaints);
                renderWardenComplaintsTable(result.data.complaints);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load complaint records.</td></tr>';
        }
    }

    function renderWardenComplaintsTable(complaints) {
        const tbody = document.getElementById('complaintsTableBody');
        tbody.innerHTML = '';
        if (complaints.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#94a3b8; padding:1rem;">No complaints registered.</td></tr>';
            return;
        }
        complaints.forEach(c => {
            const tr = document.createElement('tr');
            tr.id = `row-complaint-${c.complaint_id}`;
            tr.innerHTML = `
                <td><strong>${c.complaint_id}</strong></td>
                <td>${c.student_name || 'Student #' + c.student_id}</td>
                <td>${c.room_no || 'N/A'}</td>
                <td><span class="badge badge-priority-medium">${c.category}</span></td>
                <td>${c.description}</td>
                <td><span class="badge badge-priority-${(c.priority || 'medium').toLowerCase()}">${c.priority}</span></td>
                <td><span class="badge badge-${(c.status || 'open').toLowerCase().replace(' ', '-')}">${c.status}</span></td>
                <td>${c.created_at}</td>
                <td>
                    <select class="action-select" onchange="updateComplaintStatus('${c.complaint_id}', this.value)" data-tooltip="Update complaint status">
                        <option value="" disabled selected>Change Status</option>
                        <option value="Open" ${c.status === 'Open' ? 'disabled' : ''}>Open</option>
                        <option value="In Progress" ${c.status === 'In Progress' ? 'disabled' : ''}>In Progress</option>
                        <option value="Resolved" ${c.status === 'Resolved' ? 'disabled' : ''}>Resolved</option>
                        <option value="Closed" ${c.status === 'Closed' ? 'disabled' : ''}>Closed</option>
                    </select>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function fetchWardenLeaves() {
        const tbody = document.getElementById('leavesTableBody');
        const cached = appCache.get('warden_leaves');
        if (cached) {
            renderWardenLeavesTable(cached);
            return;
        }

        renderTableSkeleton('leavesTableBody', 9, 3);
        try {
            const res = await fetch('/api/leaves');
            const result = await res.json();
            if (result.success && result.data.leaves) {
                appCache.set('warden_leaves', result.data.leaves);
                renderWardenLeavesTable(result.data.leaves);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load leave records.</td></tr>';
        }
    }

    function renderWardenLeavesTable(leaves) {
        const tbody = document.getElementById('leavesTableBody');
        tbody.innerHTML = '';
        if (leaves.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#94a3b8; padding:1rem;">No leave applications found.</td></tr>';
            return;
        }
        leaves.forEach(l => {
            const tr = document.createElement('tr');
            tr.id = `row-leave-${l.leave_id}`;
            tr.innerHTML = `
                <td><strong>${l.leave_id}</strong></td>
                <td>${l.student_name || 'Student #' + l.student_id}</td>
                <td>${l.room_no || 'N/A'}</td>
                <td>${l.leave_type}</td>
                <td>${l.start_date}</td>
                <td>${l.end_date}</td>
                <td>${l.reason}</td>
                <td class="leave-status-cell"><span class="badge badge-${(l.status || 'pending').toLowerCase()}">${l.status}</span></td>
                <td class="leave-actions-cell">
                    ${l.status === 'Pending' ? `
                        <button class="btn-action btn-approve" onclick="updateLeaveStatus('${l.leave_id}', 'Approved')" data-tooltip="Approve student leave application">Approve</button>
                        <button class="btn-action btn-reject" onclick="updateLeaveStatus('${l.leave_id}', 'Rejected')" data-tooltip="Reject student leave application">Reject</button>
                    ` : `<span style="color:var(--text-secondary); font-size:0.8rem;">Decided</span>`}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function fetchWardenVisitors() {
        const tbody = document.getElementById('visitorsTableBody');
        const cached = appCache.get('warden_visitors');
        if (cached) {
            renderWardenVisitorsTable(cached);
            return;
        }

        renderTableSkeleton('visitorsTableBody', 9, 3);
        try {
            const res = await fetch('/api/visitors');
            const result = await res.json();
            if (result.success && result.data.visitors) {
                appCache.set('warden_visitors', result.data.visitors);
                renderWardenVisitorsTable(result.data.visitors);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load visitor logs.</td></tr>';
        }
    }

    function renderWardenVisitorsTable(visitors) {
        const tbody = document.getElementById('visitorsTableBody');
        tbody.innerHTML = '';
        if (visitors.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#94a3b8; padding:1rem;">No visitor logs found.</td></tr>';
            return;
        }
        visitors.forEach(v => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${v.visitor_id}</td>
                <td><strong>${v.name}</strong></td>
                <td>${v.contact}</td>
                <td>${v.student_name || 'Student #' + v.student_id}</td>
                <td>${v.room_no || 'N/A'}</td>
                <td>${v.visit_date}</td>
                <td>${v.visit_time}</td>
                <td>${v.purpose}</td>
                <td><span class="badge badge-approved">${v.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function fetchWardenRooms() {
        const tbody = document.getElementById('roomsTableBody');
        const cached = appCache.get('warden_rooms');
        if (cached) {
            renderWardenRoomsTable(cached);
            return;
        }

        renderTableSkeleton('roomsTableBody', 7, 3);
        try {
            const res = await fetch('/api/rooms');
            const result = await res.json();
            if (result.success && result.data.rooms) {
                appCache.set('warden_rooms', result.data.rooms);
                renderWardenRoomsTable(result.data.rooms);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load room data.</td></tr>';
        }
    }

    function renderWardenRoomsTable(rooms) {
        const tbody = document.getElementById('roomsTableBody');
        tbody.innerHTML = '';
        rooms.forEach(r => {
            const tr = document.createElement('tr');
            const isFull = r.occupied_count >= r.capacity;
            tr.innerHTML = `
                <td><strong>${r.room_no}</strong></td>
                <td>${r.block}</td>
                <td>Floor ${r.floor}</td>
                <td>${r.capacity} Beds</td>
                <td>${r.occupied_count} / ${r.capacity}</td>
                <td><span class="badge badge-${isFull ? 'rejected' : 'resolved'}">${isFull ? 'Fully Occupied' : 'Available'}</span></td>
                <td><small style="color:var(--text-secondary);">${r.amenities}</small></td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function fetchWardenAuditLogs() {
        const tbody = document.getElementById('logsTableBody');
        renderTableSkeleton('logsTableBody', 7, 3);
        try {
            const logRes = await fetch('/api/chat_logs');
            if (logRes.ok) {
                const result = await logRes.json();
                if (result.success && result.data) {
                    tbody.innerHTML = '';
                    if (result.data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:1rem;">No AI chat logs recorded yet.</td></tr>';
                        return;
                    }
                    result.data.forEach(l => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>#${l.log_id}</td>
                            <td>Student #${l.student_id}</td>
                            <td>"${l.message}"</td>
                            <td><span class="badge badge-priority-medium">${l.detected_intent}</span></td>
                            <td><span class="badge badge-approved">${l.agent_invoked}</span></td>
                            <td><small>${l.response}</small></td>
                            <td>${l.timestamp}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } else {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:1rem;">No audit logs captured yet. Interact with the chat interface to generate logs.</td></tr>';
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:1rem;">No audit logs captured yet. Interact with the chat interface to generate logs.</td></tr>';
        }
    }

    // Optimistic Action Handlers for Warden Actions
    window.updateComplaintStatus = async (complaintId, status) => {
        if (!status) return;

        const tr = document.getElementById(`row-complaint-${complaintId}`);
        let oldStatusHTML = '';
        if (tr) {
            const statusCell = tr.children[6];
            oldStatusHTML = statusCell.innerHTML;
            statusCell.innerHTML = `<span class="badge badge-${status.toLowerCase().replace(' ', '-')}">${status} (Syncing...)</span>`;
        }

        appCache.invalidate();
        showToast(`Updating complaint ${complaintId} to ${status}...`, 'info');

        try {
            const res = await fetch(`/api/complaints/${complaintId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            const result = await res.json();
            if (result.success) {
                showToast(`Complaint ${complaintId} status set to ${status}`, 'info');
                loadWardenDashboardData();
            } else {
                if (tr) tr.children[6].innerHTML = oldStatusHTML;
                showToast(`Failed to update complaint: ${result.message}`, 'error');
            }
        } catch (e) {
            if (tr) tr.children[6].innerHTML = oldStatusHTML;
            showToast('Network error updating complaint status', 'error');
        }
    };

    window.updateLeaveStatus = async (leaveId, status) => {
        const tr = document.getElementById(`row-leave-${leaveId}`);
        let oldStatusCell = '', oldActionsCell = '';

        if (tr) {
            const statusCell = tr.querySelector('.leave-status-cell');
            const actionsCell = tr.querySelector('.leave-actions-cell');
            oldStatusCell = statusCell.innerHTML;
            oldActionsCell = actionsCell.innerHTML;

            statusCell.innerHTML = `<span class="badge badge-${status.toLowerCase()}">${status}</span>`;
            actionsCell.innerHTML = `<span style="color:var(--text-secondary); font-size:0.8rem;">Decided</span>`;

            const statLeaves = document.getElementById('statLeaves');
            if (statLeaves) {
                const current = parseInt(statLeaves.textContent, 10) || 0;
                statLeaves.textContent = Math.max(0, current - 1);
            }
        }

        appCache.invalidate();
        showToast(`Leave request ${leaveId} marked as ${status}`, 'info');

        try {
            const res = await fetch(`/api/leaves/${leaveId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            const result = await res.json();
            if (result.success) {
                loadWardenDashboardData();
            } else {
                if (tr) {
                    tr.querySelector('.leave-status-cell').innerHTML = oldStatusCell;
                    tr.querySelector('.leave-actions-cell').innerHTML = oldActionsCell;
                }
                showToast(`Failed to update leave request: ${result.message}`, 'error');
            }
        } catch (e) {
            if (tr) {
                tr.querySelector('.leave-status-cell').innerHTML = oldStatusCell;
                tr.querySelector('.leave-actions-cell').innerHTML = oldActionsCell;
            }
            showToast('Network error updating leave status', 'error');
        }
    };
});
