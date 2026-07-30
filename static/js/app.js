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
        const urlParams = new URLSearchParams(window.location.search);
        const paramRole = urlParams.get('role');
        const sessionRole = sessionStorage.getItem('shms_role');

        let u = null;

        try {
            const res = await fetch('/api/me');
            const data = await res.json();
            if (data.success && data.user && !data.is_demo) {
                u = data.user;
            }
        } catch (e) {
            console.error('Session check error:', e);
        }

        // Fallback to localStorage saved user if session is demo or empty
        if (!u) {
            const stored = localStorage.getItem('shms_user');
            if (stored) {
                try { u = JSON.parse(stored); } catch(err){}
            }
        }

        const isWarden = (paramRole === 'warden') || (sessionRole === 'warden') || (u && u.role === 'warden');

        const studentNavGroup = document.getElementById('sidebarStudentNavGroup');
        const wardenNavGroup = document.getElementById('sidebarWardenNavGroup');
        const roleSwitcher = document.getElementById('topbarRoleSwitcher');
        const studentSelectWrap = document.getElementById('studentSelectWrap');

        if (isWarden) {
            // Strictly isolate Warden view: Hide student navigation
            if (studentNavGroup) studentNavGroup.style.display = 'none';
            if (wardenNavGroup) wardenNavGroup.style.display = 'block';
            if (roleSwitcher) roleSwitcher.style.display = 'none';
            if (studentSelectWrap) studentSelectWrap.style.display = 'none';

            const topAuthText = document.getElementById('topAuthText');
            const name = (u && u.name) ? u.name.toUpperCase() : 'DR. ROBERT VANCE';
            if (topAuthText) topAuthText.textContent = `WARDEN: ${name}`;
            switchMainView('warden');
        } else {
            // Student View
            const sId = (u && u.id) ? u.id : 1;
            window.currentStudentId = sId;
            if (studentNavGroup) studentNavGroup.style.display = 'block';
            if (wardenNavGroup) wardenNavGroup.style.display = 'none';
            if (roleSwitcher) roleSwitcher.style.display = 'none';
            if (studentSelectWrap) studentSelectWrap.style.display = 'none';

            if (studentSelect) studentSelect.value = sId;
            const nameElem = document.getElementById('studentName');
            const cardNameElem = document.getElementById('cardStudentName');
            const avatarElem = document.getElementById('userAvatar');
            const topAuthText = document.getElementById('topAuthText');

            const sName = (u && u.name) ? u.name : 'Alex Johnson';
            if (nameElem) nameElem.textContent = sName;
            if (cardNameElem) cardNameElem.textContent = sName;
            if (avatarElem) avatarElem.textContent = sName.charAt(0);
            if (topAuthText) topAuthText.textContent = `RESIDENT: ${sName.toUpperCase()}`;

            switchMainView('student');
        }
    }

    function getStudentId() {
        return window.currentStudentId || parseInt(studentSelect ? studentSelect.value : 1, 10) || 1;
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

            const floatWidget = document.getElementById('wardenChatFloatingWidget');
            if (floatWidget) floatWidget.style.display = 'none';

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

            const floatWidget = document.getElementById('wardenChatFloatingWidget');
            if (floatWidget) floatWidget.style.display = 'block';

            document.getElementById('studentSelectWrap').style.display = 'none';
            document.getElementById('topAuthText').textContent = 'WARDEN AUTHENTICATED';

            // Sidebar Profile
            const profileBox = document.getElementById('sidebarProfileBox');
            profileBox.style.background = '#eff6ff';
            profileBox.style.borderColor = '#bfdbfe';
            document.getElementById('sidebarProfileTitle').style.color = '#1d4ed8';
            document.getElementById('sidebarProfileTitle').textContent = 'WARDEN PORTAL';
            document.getElementById('sidebarProfileSub').textContent = 'Administrator';

            appCache.invalidate(); // Invalidate cache so Warden always sees live student requests!
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
        const sId = getStudentId();
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

        const sId = getStudentId();
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
            fetchWardenAuditLogs(),
            fetchWardenStudents()
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
        if (!tbody) return;
        tbody.innerHTML = '';
        if (visitors.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color:#94a3b8; padding:1rem;">No visitor logs found.</td></tr>';
            return;
        }
        visitors.forEach(v => {
            const tr = document.createElement('tr');
            tr.id = `row-visitor-${v.visitor_id}`;
            const statusStr = v.status || 'Pending';
            let badgeStyle = 'badge-priority-low';
            if (statusStr === 'Approved') badgeStyle = 'badge-approved';
            else if (statusStr === 'Rejected') badgeStyle = 'badge-rejected';
            else if (statusStr === 'Pending') badgeStyle = 'badge-priority-medium';

            const actionsHtml = statusStr === 'Pending' ? `
                <button class="btn-action btn-approve" onclick="updateVisitorStatus(${v.visitor_id}, 'Approved')" data-tooltip="Approve visitor pass">Approve</button>
                <button class="btn-action btn-reject" onclick="updateVisitorStatus(${v.visitor_id}, 'Rejected')" data-tooltip="Reject visitor pass">Reject</button>
            ` : `<span style="color:var(--text-secondary); font-size:0.8rem;">Decided</span>`;

            tr.innerHTML = `
                <td>#${v.visitor_id}</td>
                <td><strong>${v.name}</strong></td>
                <td>${v.contact}</td>
                <td>${v.student_name || 'Student #' + v.student_id}</td>
                <td>${v.room_no || 'N/A'}</td>
                <td>${v.visit_date}</td>
                <td>${v.visit_time}</td>
                <td>${v.purpose}</td>
                <td><span class="badge ${badgeStyle}">${statusStr}</span></td>
                <td>${actionsHtml}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    window.updateVisitorStatus = async (visitorId, status) => {
        try {
            const res = await fetch(`/api/visitors/${visitorId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            const result = await res.json();
            if (result.success) {
                showToast(`Visitor pass #${visitorId} updated to ${status}`, 'success');
                appCache.invalidate();
                fetchWardenVisitors();
                loadWardenDashboardData();
            } else {
                showToast(`Error: ${result.message}`, 'error');
            }
        } catch (e) {
            showToast('Network error updating visitor status', 'error');
        }
    };


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

    // ==================== REPORT GENERATOR & PDF DOWNLOAD ====================
    window.openReportModal = () => {
        const modal = document.getElementById('reportModal');
        if (modal) {
            modal.style.display = 'flex';
            window.setReportDateShortcut('30days');
        }
    };

    window.closeReportModal = () => {
        const modal = document.getElementById('reportModal');
        if (modal) {
            modal.style.display = 'none';
        }
    };

    window.setReportDateShortcut = (range) => {
        const today = new Date();
        const formatDate = (d) => {
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };

        const startInput = document.getElementById('reportStartDate');
        const endInput = document.getElementById('reportEndDate');

        if (!startInput || !endInput) return;

        // Update active shortcut button UI
        document.querySelectorAll('#reportModal .btn-shortcut').forEach(btn => btn.classList.remove('active'));
        if (window.event && window.event.target && window.event.target.classList && window.event.target.classList.contains('btn-shortcut')) {
            window.event.target.classList.add('active');
        }

        if (range === 'today') {
            const todayStr = formatDate(today);
            startInput.value = todayStr;
            endInput.value = todayStr;
        } else if (range === '7days') {
            const startDate = new Date();
            startDate.setDate(today.getDate() - 7);
            startInput.value = formatDate(startDate);
            endInput.value = formatDate(today);
        } else if (range === '30days') {
            const startDate = new Date();
            startDate.setDate(today.getDate() - 30);
            startInput.value = formatDate(startDate);
            endInput.value = formatDate(today);
        } else if (range === 'month') {
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            startInput.value = formatDate(firstDay);
            endInput.value = formatDate(today);
        } else if (range === 'all') {
            startInput.value = '2020-01-01';
            endInput.value = formatDate(today);
        }
    };

    window.downloadPdfReport = async () => {
        const startDate = document.getElementById('reportStartDate').value;
        const endDate = document.getElementById('reportEndDate').value;
        const category = document.getElementById('reportCategory').value;

        if (!startDate || !endDate) {
            showToast('Please select both Start Date and End Date.', 'warning');
            return;
        }

        if (startDate > endDate) {
            showToast('Start Date cannot be after End Date.', 'warning');
            return;
        }

        const btn = document.getElementById('btnDownloadPdf');
        const btnText = document.getElementById('btnDownloadPdfText');
        const originalText = btnText ? btnText.textContent : 'Download PDF';

        if (btn) btn.disabled = true;
        if (btnText) btnText.textContent = 'Generating PDF...';

        showToast('Preparing your PDF report...', 'info');

        try {
            const url = `/api/reports/download-pdf?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&category=${encodeURIComponent(category)}`;
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = `SmartHostel_Report_${startDate}_to_${endDate}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();

            showToast('PDF Report downloaded successfully!', 'success');
            closeReportModal();
        } catch (error) {
            console.error('PDF Download Error:', error);
            showToast(`Failed to generate PDF report: ${error.message}`, 'error');
        } finally {
            if (btn) btn.disabled = false;
            if (btnText) btnText.textContent = originalText;
        }
    };

    // ==================== STUDENT DIRECTORY & CSV BULK IMPORT ====================
    let allWardenStudents = [];

    async function fetchWardenStudents() {
        const tbody = document.getElementById('studentsTableBody');
        if (!tbody) return;

        const cached = appCache.get('warden_students');
        if (cached) {
            allWardenStudents = cached;
            renderWardenStudentsTable(allWardenStudents);
            return;
        }

        renderTableSkeleton('studentsTableBody', 7, 3);
        try {
            const res = await fetch('/api/students');
            const result = await res.json();
            if (result.success && result.data) {
                allWardenStudents = result.data;
                appCache.set('warden_students', allWardenStudents);
                renderWardenStudentsTable(allWardenStudents);
            }
        } catch (e) {
            console.error('Error fetching students:', e);
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load student directory.</td></tr>';
        }
    }
    function renderWardenStudentsTable(students) {
        const tbody = document.getElementById('studentsTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!students || students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#94a3b8; padding:1.2rem;">No student records found. Click "+ Add Student" or "Upload CSV Dataset" to import.</td></tr>';
            return;
        }

        students.forEach(s => {
            const tr = document.createElement('tr');
            tr.id = `row-student-${s.student_id}`;
            const roomDisplay = s.room_no ? `<span class="badge badge-approved">Room ${s.room_no} (${s.block || 'Block A'})</span>` : `<span class="badge badge-priority-low">Unallocated</span>`;
            const statusStr = s.status || 'Active';
            const isSuspended = statusStr === 'Suspended';
            const statusBadge = isSuspended ? 
                `<span class="badge badge-rejected" style="background:#fef2f2; color:#dc2626; border:1px solid #fca5a5;">Suspended</span>` : 
                `<span class="badge badge-approved" style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0;">Active</span>`;

            const safeName = (s.name || '').replace(/'/g, "\\'");
            
            const suspendBtn = isSuspended ?
                `<button type="button" class="btn-action" onclick="toggleStudentStatus(${s.student_id}, 'Active')" style="background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0;" data-tooltip="Reactivate student account">Activate</button>` :
                `<button type="button" class="btn-action" onclick="toggleStudentStatus(${s.student_id}, 'Suspended')" style="background: #fffbeb; color: #d97706; border: 1px solid #fde68a;" data-tooltip="Suspend student account">Suspend</button>`;

            tr.innerHTML = `
                <td>#${s.student_id}</td>
                <td><span class="badge badge-in-progress">${s.roll_no}</span></td>
                <td><strong>${s.name}</strong></td>
                <td>${s.email}</td>
                <td>${s.contact}</td>
                <td>${roomDisplay}</td>
                <td>${statusBadge}</td>
                <td>
                    <div style="display: flex; gap: 0.4rem;">
                        ${suspendBtn}
                        <button type="button" class="btn-action" onclick="openEditStudentModal(${s.student_id})" style="background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe;" data-tooltip="Manage student room/status">Manage</button>
                        <button type="button" class="btn-action btn-reject" onclick="confirmDeleteStudent(${s.student_id}, '${safeName}')" data-tooltip="Remove student record">Remove</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    window.toggleStudentStatus = async (studentId, newStatus) => {
        try {
            const res = await fetch(`/api/students/${studentId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            const result = await res.json();
            if (result.success) {
                showToast(`Student status updated to ${newStatus}`, 'info');
                appCache.invalidate();
                fetchWardenStudents();
            } else {
                showToast(`Failed: ${result.message}`, 'error');
            }
        } catch (e) {
            showToast('Network error updating student status', 'error');
        }
    };

    window.filterStudentsTable = () => {
        const query = (document.getElementById('studentSearchInput')?.value || '').toLowerCase();
        if (!query) {
            renderWardenStudentsTable(allWardenStudents);
            return;
        }
        const filtered = allWardenStudents.filter(s => 
            (s.name || '').toLowerCase().includes(query) ||
            (s.roll_no || '').toLowerCase().includes(query) ||
            (s.email || '').toLowerCase().includes(query) ||
            (s.contact || '').toLowerCase().includes(query) ||
            (s.room_no || '').toLowerCase().includes(query)
        );
        renderWardenStudentsTable(filtered);
    };

    async function populateStudentRoomOptions(selectedRoomId = null) {
        const select = document.getElementById('studentRoomSelect');
        if (!select) return;
        select.innerHTML = '<option value="">-- No Room Allocated --</option>';

        try {
            const res = await fetch('/api/rooms');
            const result = await res.json();
            if (result.success && result.data && result.data.rooms) {
                result.data.rooms.forEach(r => {
                    const opt = document.createElement('option');
                    opt.value = r.room_id;
                    opt.textContent = `Room ${r.room_no} (${r.block} - ${r.occupied_count}/${r.capacity} Occupied)`;
                    if (selectedRoomId && parseInt(selectedRoomId, 10) === r.room_id) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            }
        } catch (e) {
            console.error('Error populating room options:', e);
        }
    }

    function setPersonalFieldsReadonly(readonly = false) {
        ['studentNameInput', 'studentRollInput', 'studentContactInput', 'studentEmailInput'].forEach(id => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.readOnly = readonly;
                elem.style.background = readonly ? '#f1f5f9' : '#ffffff';
                elem.style.cursor = readonly ? 'not-allowed' : 'text';
            }
        });
    }

    window.openAddStudentModal = () => {
        document.getElementById('studentForm').reset();
        document.getElementById('studentEditId').value = '';
        document.getElementById('studentModalTitle').textContent = 'Add New Student';
        document.getElementById('btnSaveStudent').textContent = 'Save Student';
        const removeBtn = document.getElementById('btnRemoveStudent');
        if (removeBtn) removeBtn.style.display = 'none';

        setPersonalFieldsReadonly(false);
        const statusSelect = document.getElementById('studentStatusSelect');
        if (statusSelect) statusSelect.value = 'Active';

        populateStudentRoomOptions();
        const modal = document.getElementById('studentModal');
        if (modal) modal.style.display = 'flex';
    };

    window.openEditStudentModal = async (studentId) => {
        try {
            const res = await fetch(`/api/students/${studentId}`);
            const result = await res.json();
            if (result.success && result.data) {
                const s = result.data;
                document.getElementById('studentEditId').value = s.student_id;
                document.getElementById('studentNameInput').value = s.name;
                document.getElementById('studentRollInput').value = s.roll_no;
                document.getElementById('studentContactInput').value = s.contact;
                document.getElementById('studentEmailInput').value = s.email;
                
                const statusSelect = document.getElementById('studentStatusSelect');
                if (statusSelect) statusSelect.value = s.status || 'Active';

                setPersonalFieldsReadonly(true);

                await populateStudentRoomOptions(s.room_id);

                document.getElementById('studentModalTitle').textContent = `Manage Student: ${s.name} (Read-Only Info)`;
                document.getElementById('btnSaveStudent').textContent = 'Save Status & Room';

                const removeBtn = document.getElementById('btnRemoveStudent');
                if (removeBtn) removeBtn.style.display = 'block';

                const modal = document.getElementById('studentModal');
                if (modal) modal.style.display = 'flex';
            }
        } catch (e) {
            showToast('Failed to fetch student details', 'error');
        }
    };

    window.closeStudentModal = () => {
        const modal = document.getElementById('studentModal');
        if (modal) modal.style.display = 'none';
    };

    window.confirmDeleteStudentFromModal = () => {
        const studentId = document.getElementById('studentEditId').value;
        const name = document.getElementById('studentNameInput').value;
        if (studentId) {
            closeStudentModal();
            confirmDeleteStudent(studentId, name);
        }
    };

    window.saveStudentForm = async (event) => {
        event.preventDefault();
        const editId = document.getElementById('studentEditId').value;
        const name = document.getElementById('studentNameInput').value.trim();
        const roll_no = document.getElementById('studentRollInput').value.trim();
        const contact = document.getElementById('studentContactInput').value.trim();
        const email = document.getElementById('studentEmailInput').value.trim();
        const room_id = document.getElementById('studentRoomSelect').value;
        const statusSelect = document.getElementById('studentStatusSelect');
        const status = statusSelect ? statusSelect.value : 'Active';

        const payload = { name, roll_no, contact, email, room_id, status };
        const url = editId ? `/api/students/${editId}` : '/api/students';
        const method = editId ? 'PUT' : 'POST';

        const saveBtn = document.getElementById('btnSaveStudent');
        if (saveBtn) saveBtn.disabled = true;

        try {
            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await res.json();
            if (result.success) {
                showToast(editId ? 'Student status & room allocation updated!' : 'New student created successfully!', 'success');
                appCache.invalidate();
                closeStudentModal();
                loadWardenDashboardData();
                fetchWardenStudents();
            } else {
                showToast(`Error: ${result.message}`, 'error');
            }
        } catch (e) {
            showToast('Network error saving student record', 'error');
        } finally {
            if (saveBtn) saveBtn.disabled = false;
        }
    };

    window.confirmDeleteStudent = async (studentId, name) => {

        if (!confirm(`Are you sure you want to delete student "${name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const res = await fetch(`/api/students/${studentId}`, { method: 'DELETE' });
            const result = await res.json();
            if (result.success) {
                showToast(`Student "${name}" deleted.`, 'info');
                appCache.invalidate();
                loadWardenDashboardData();
                fetchWardenStudents();
            } else {
                showToast(`Failed to delete student: ${result.message}`, 'error');
            }
        } catch (e) {
            showToast('Network error deleting student', 'error');
        }
    };

    window.openCsvUploadModal = () => {
        document.getElementById('csvForm').reset();
        document.getElementById('csvFileStatus').textContent = 'Supports .csv files with roll_no, name, email, contact, room_no';
        const modal = document.getElementById('csvUploadModal');
        if (modal) modal.style.display = 'flex';
    };

    window.closeCsvUploadModal = () => {
        const modal = document.getElementById('csvUploadModal');
        if (modal) modal.style.display = 'none';
    };

    window.onCsvFileSelected = (input) => {
        const statusElem = document.getElementById('csvFileStatus');
        if (input.files && input.files[0]) {
            const file = input.files[0];
            statusElem.innerHTML = `<strong style="color:#059669;">Selected File:</strong> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        } else {
            statusElem.textContent = 'Supports .csv files with roll_no, name, email, contact, room_no';
        }
    };

    window.handleCsvUpload = async (event) => {
        event.preventDefault();
        const fileInput = document.getElementById('csvFileInput');
        if (!fileInput.files || !fileInput.files[0]) {
            showToast('Please select a CSV file to upload.', 'warning');
            return;
        }

        const submitBtn = document.getElementById('btnSubmitCsv');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Uploading & Processing...</span>';
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch('/api/students/upload-csv', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();
            if (result.success) {
                showToast(result.message, 'success');
                appCache.invalidate();
                closeCsvUploadModal();
                loadWardenDashboardData();
                fetchWardenStudents();
                populateTopbarStudentSelect();
            } else {
                showToast(`CSV Upload Error: ${result.message}`, 'error');
            }
        } catch (e) {
            showToast('Network error uploading CSV file', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Process & Upload Dataset</span>';
            }
        }
    };

    // ==================== DYNAMIC TOPBAR STUDENT SELECTOR ====================
    async function populateTopbarStudentSelect() {
        const select = document.getElementById('studentSelect');
        if (!select) return;
        const currentVal = select.value;

        try {
            const res = await fetch('/api/students');
            const result = await res.json();
            if (result.success && result.data && result.data.length > 0) {
                select.innerHTML = '';
                result.data.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s.student_id;
                    const roomInfo = s.room_no ? `Room ${s.room_no}` : 'Unassigned';
                    opt.textContent = `${s.name} (${s.roll_no} - ${roomInfo})`;
                    select.appendChild(opt);
                });
                if (currentVal && Array.from(select.options).some(o => o.value == currentVal)) {
                    select.value = currentVal;
                }
            }
        } catch (e) {
            console.error('Error populating topbar student select:', e);
        }
    }

    // Call on page load
    populateTopbarStudentSelect();

    // ==================== STUDENT LEAVE APPLICATION MODAL ====================
    window.openStudentLeaveModal = () => {
        const form = document.getElementById('studentLeaveForm');
        if (form) form.reset();
        
        const todayStr = new Date().toISOString().split('T')[0];
        const startInput = document.getElementById('leaveStartDate');
        const endInput = document.getElementById('leaveEndDate');

        if (startInput) startInput.value = todayStr;
        if (endInput) {
            const tmr = new Date();
            tmr.setDate(tmr.getDate() + 2);
            endInput.value = tmr.toISOString().split('T')[0];
        }

        const modal = document.getElementById('studentLeaveModal');
        if (modal) modal.style.display = 'flex';
    };

    window.closeStudentLeaveModal = () => {
        const modal = document.getElementById('studentLeaveModal');
        if (modal) modal.style.display = 'none';
    };

    window.submitStudentLeaveForm = async (event) => {
        event.preventDefault();
        const sId = getStudentId();

        const leave_type = document.getElementById('leaveTypeSelect').value;

        const start_date = document.getElementById('leaveStartDate').value;
        const end_date = document.getElementById('leaveEndDate').value;
        const reason = document.getElementById('leaveReasonInput').value.trim();

        if (start_date > end_date) {
            showToast('Start Date cannot be after End Date.', 'warning');
            return;
        }

        const btn = document.getElementById('btnSubmitLeave');
        if (btn) btn.disabled = true;

        try {
            const res = await fetch('/api/leaves', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: sId,
                    leave_type: leave_type,
                    start_date: start_date,
                    end_date: end_date,
                    reason: reason
                })
            });
            const result = await res.json();
            if (result.success) {
                const leaveId = result.data ? result.data.leave_id : 'Pending';
                showToast(`Leave application submitted successfully! (${leaveId})`, 'success');
                appCache.invalidate(); // Invalidate cache so Warden View immediately sees new leave!
                closeStudentLeaveModal();
                loadStudentPortalData(true);
            } else {
                showToast(`Failed to submit leave: ${result.message}`, 'error');
            }
        } catch (e) {
            showToast('Network error submitting leave request', 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    };

    // ==================== WARDEN FLOATING AI CHATBOT WIDGET ====================
    window.toggleWardenChatWidget = () => {
        const drawer = document.getElementById('wardenChatDrawer');
        if (!drawer) return;
        if (drawer.style.display === 'none' || drawer.style.display === '') {
            drawer.style.display = 'flex';
            const input = document.getElementById('wardenAiInput');
            if (input) input.focus();
        } else {
            drawer.style.display = 'none';
        }
    };

    window.sendWardenQuickPrompt = (promptText) => {
        const input = document.getElementById('wardenAiInput');
        const tabInput = document.getElementById('tabWardenAiInput');
        if (input) input.value = promptText;
        if (tabInput) tabInput.value = promptText;

        if (input) window.sendWardenChatMessage();
        if (tabInput) window.sendTabWardenChatMessage();
    };

    window.sendTabWardenChatMessage = async () => {
        const input = document.getElementById('tabWardenAiInput');
        const chatBox = document.getElementById('tabWardenAiChatBox');
        if (!input || !chatBox) return;

        const text = input.value.trim();
        if (!text) return;

        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const uBubble = document.createElement('div');
        uBubble.className = 'chat-msg user';
        uBubble.style.cssText = 'background: rgba(5, 150, 105, 0.25); color: white; border: 1px solid rgba(5, 150, 105, 0.4); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; margin-bottom: 0.5rem;';
        uBubble.textContent = text;
        chatBox.appendChild(uBubble);

        input.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;

        const typingElem = document.createElement('div');
        typingElem.className = 'chat-msg agent';
        typingElem.style.cssText = 'background: rgba(30, 41, 59, 0.8); color: #f8fafc; border: 1px solid rgba(255,255,255,0.1); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; margin-bottom: 0.5rem; opacity: 0.85;';
        typingElem.innerHTML = `
            <div style="color: #34d399; font-weight: 800; font-size: 0.68rem;">Warden Copilot Executing...</div>
            <div style="margin-top:0.3rem;" class="skeleton-text skeleton-dark"></div>
        `;
        chatBox.appendChild(typingElem);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    student_id: 1,
                    role: 'warden'
                })
            });
            const data = await res.json();
            typingElem.remove();

            const aBubble = document.createElement('div');
            aBubble.className = 'chat-msg agent';
            aBubble.style.cssText = 'background: rgba(30, 41, 59, 0.85); color: #f8fafc; border: 1px solid rgba(255,255,255,0.1); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; margin-bottom: 0.5rem;';

            if (data.success) {
                const agents = (data.agents_invoked || []).join(' + ') || 'Decision Agent';
                aBubble.innerHTML = `
                    <div style="color: #34d399; font-weight: 800; font-size: 0.68rem; margin-bottom: 0.2rem;">⚡ Action Executed via ${agents}</div>
                    <div>${data.message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}</div>
                `;
                showToast('Warden Command Executed!', 'success');
                appCache.invalidate();
                loadWardenDashboardData();
            } else {
                aBubble.innerHTML = `<div style="color: #ef4444; font-weight:700;">Notice: ${data.message}</div>`;
            }
            chatBox.appendChild(aBubble);
        } catch (e) {
            typingElem.remove();
            showToast('Network error executing warden command', 'error');
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    window.sendWardenChatMessage = async () => {
        const input = document.getElementById('wardenAiInput');
        const chatBox = document.getElementById('wardenAiChatBox');
        if (!input || !chatBox) return;

        const text = input.value.trim();
        if (!text) return;

        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // User message bubble
        const uBubble = document.createElement('div');
        uBubble.className = 'chat-msg user';
        uBubble.style.cssText = 'background: rgba(5, 150, 105, 0.25); color: white; border: 1px solid rgba(5, 150, 105, 0.4); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; margin-bottom: 0.5rem;';
        uBubble.textContent = text;
        chatBox.appendChild(uBubble);

        input.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;

        // Thinking indicator
        const typingElem = document.createElement('div');
        typingElem.className = 'chat-msg agent';
        typingElem.style.cssText = 'background: rgba(30, 41, 59, 0.8); color: #f8fafc; border: 1px solid rgba(255,255,255,0.1); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; margin-bottom: 0.5rem; opacity: 0.85;';
        typingElem.innerHTML = `
            <div style="color: #34d399; font-weight: 800; font-size: 0.68rem;">Warden Copilot Executing...</div>
            <div style="margin-top:0.3rem;" class="skeleton-text skeleton-dark"></div>
        `;
        chatBox.appendChild(typingElem);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    student_id: 1,
                    role: 'warden'
                })
            });
            const data = await res.json();
            typingElem.remove();

            const aBubble = document.createElement('div');
            aBubble.className = 'chat-msg agent';
            aBubble.style.cssText = 'background: rgba(30, 41, 59, 0.85); color: #f8fafc; border: 1px solid rgba(255,255,255,0.1); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; margin-bottom: 0.5rem;';

            if (data.success) {
                const agents = (data.agents_invoked || []).join(' + ') || 'Decision Agent';
                aBubble.innerHTML = `
                    <div style="color: #34d399; font-weight: 800; font-size: 0.68rem; margin-bottom: 0.2rem;">⚡ Action Executed via ${agents}</div>
                    <div>${data.message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}</div>
                `;
                showToast('Warden Command Executed!', 'success');
                appCache.invalidate();
                loadWardenDashboardData();
            } else {
                aBubble.innerHTML = `<div style="color: #ef4444; font-weight:700;">Notice: ${data.message}</div>`;
            }
            chatBox.appendChild(aBubble);
        } catch (e) {
            typingElem.remove();
            showToast('Network error executing warden command', 'error');
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    };
});



