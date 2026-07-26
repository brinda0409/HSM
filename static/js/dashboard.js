/**
 * Smart Hostel Management System - Warden Administration Logic
 * Features: Skeleton Loaders, Client Caching, Optimistic UI Updates, SaaS Toasting
 */

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

const dashCache = new ClientCache();

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

function renderTableSkeleton(tbodyId, columnsCount = 9, rowsCount = 3) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    let html = '';
    for (let i = 0; i < rowsCount; i++) {
        html += `<tr><td colspan="${columnsCount}"><div class="skeleton-row skeleton"></div></td></tr>`;
    }
    tbody.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', () => {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const refreshBtn = document.getElementById('refreshBtn');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');

            btn.classList.add('active');
            const targetTab = btn.getAttribute('data-tab');
            document.getElementById(`tab-${targetTab}`).style.display = 'block';
        });
    });

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            dashCache.invalidate();
            showToast("Refreshed dashboard data", "info");
            loadAllDashboardData();
        });
    }

    // Load initial dashboard metrics
    loadAllDashboardData();

    async function loadAllDashboardData() {
        await Promise.all([
            fetchStats(),
            fetchComplaints(),
            fetchLeaves(),
            fetchVisitors(),
            fetchRooms(),
            fetchAuditLogs()
        ]);
    }

    async function fetchStats() {
        const cached = dashCache.get('stats');
        if (cached) {
            updateStatsUI(cached);
            return;
        }

        try {
            const res = await fetch('/api/dashboard/stats');
            const result = await res.json();
            if (result.success) {
                dashCache.set('stats', result.data);
                updateStatsUI(result.data);
            }
        } catch (e) {
            console.error('Error fetching stats:', e);
        }
    }

    function updateStatsUI(s) {
        document.getElementById('statComplaints').textContent = s.open_complaints;
        document.getElementById('statLeaves').textContent = s.pending_leaves;
        document.getElementById('statVisitors').textContent = s.today_visitors;
        document.getElementById('statOccupancy').textContent = `${s.occupancy_pct}%`;
    }

    async function fetchComplaints() {
        const tbody = document.getElementById('complaintsTableBody');
        const cached = dashCache.get('complaints');
        if (cached) {
            renderComplaintsTable(cached);
            return;
        }

        renderTableSkeleton('complaintsTableBody', 9, 3);
        try {
            const res = await fetch('/api/complaints');
            const result = await res.json();
            if (result.success && result.data.complaints) {
                dashCache.set('complaints', result.data.complaints);
                renderComplaintsTable(result.data.complaints);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load complaint records.</td></tr>';
        }
    }

    function renderComplaintsTable(complaints) {
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

    async function fetchLeaves() {
        const tbody = document.getElementById('leavesTableBody');
        const cached = dashCache.get('leaves');
        if (cached) {
            renderLeavesTable(cached);
            return;
        }

        renderTableSkeleton('leavesTableBody', 9, 3);
        try {
            const res = await fetch('/api/leaves');
            const result = await res.json();
            if (result.success && result.data.leaves) {
                dashCache.set('leaves', result.data.leaves);
                renderLeavesTable(result.data.leaves);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load leave records.</td></tr>';
        }
    }

    function renderLeavesTable(leaves) {
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

    async function fetchVisitors() {
        const tbody = document.getElementById('visitorsTableBody');
        const cached = dashCache.get('visitors');
        if (cached) {
            renderVisitorsTable(cached);
            return;
        }

        renderTableSkeleton('visitorsTableBody', 9, 3);
        try {
            const res = await fetch('/api/visitors');
            const result = await res.json();
            if (result.success && result.data.visitors) {
                dashCache.set('visitors', result.data.visitors);
                renderVisitorsTable(result.data.visitors);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load visitor logs.</td></tr>';
        }
    }

    function renderVisitorsTable(visitors) {
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

    async function fetchRooms() {
        const tbody = document.getElementById('roomsTableBody');
        const cached = dashCache.get('rooms');
        if (cached) {
            renderRoomsTable(cached);
            return;
        }

        renderTableSkeleton('roomsTableBody', 7, 3);
        try {
            const res = await fetch('/api/rooms');
            const result = await res.json();
            if (result.success && result.data.rooms) {
                dashCache.set('rooms', result.data.rooms);
                renderRoomsTable(result.data.rooms);
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#ef4444; padding:1rem;">Failed to load room data.</td></tr>';
        }
    }

    function renderRoomsTable(rooms) {
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

    async function fetchAuditLogs() {
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

    // 3. Optimistic Updates for Warden Actions
    window.updateComplaintStatus = async (complaintId, status) => {
        if (!status) return;

        // Optimistic DOM Update
        const tr = document.getElementById(`row-complaint-${complaintId}`);
        let oldStatusHTML = '';
        if (tr) {
            const statusCell = tr.children[6];
            oldStatusHTML = statusCell.innerHTML;
            statusCell.innerHTML = `<span class="badge badge-${status.toLowerCase().replace(' ', '-')}">${status} (Syncing...)</span>`;
        }

        dashCache.invalidate();
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
                loadAllDashboardData();
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
        // Optimistic DOM Update
        const tr = document.getElementById(`row-leave-${leaveId}`);
        let oldStatusCell = '', oldActionsCell = '';

        if (tr) {
            const statusCell = tr.querySelector('.leave-status-cell');
            const actionsCell = tr.querySelector('.leave-actions-cell');
            oldStatusCell = statusCell.innerHTML;
            oldActionsCell = actionsCell.innerHTML;

            statusCell.innerHTML = `<span class="badge badge-${status.toLowerCase()}">${status}</span>`;
            actionsCell.innerHTML = `<span style="color:var(--text-secondary); font-size:0.8rem;">Saved</span>`;

            // Update stats counter optimistically
            const statLeaves = document.getElementById('statLeaves');
            if (statLeaves) {
                const current = parseInt(statLeaves.textContent, 10) || 0;
                statLeaves.textContent = Math.max(0, current - 1);
            }
        }

        dashCache.invalidate();
        showToast(`Leave request ${leaveId} marked as ${status}`, 'info');

        try {
            const res = await fetch(`/api/leaves/${leaveId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            const result = await res.json();
            if (result.success) {
                loadAllDashboardData();
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
