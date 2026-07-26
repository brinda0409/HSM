document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
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
        refreshBtn.addEventListener('click', loadAllDashboardData);
    }

    // Load initial dashboard data
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
        try {
            const res = await fetch('/api/dashboard/stats');
            const result = await res.json();
            if (result.success) {
                const s = result.data;
                document.getElementById('statComplaints').textContent = s.open_complaints;
                document.getElementById('statLeaves').textContent = s.pending_leaves;
                document.getElementById('statVisitors').textContent = s.today_visitors;
                document.getElementById('statOccupancy').textContent = `${s.occupancy_pct}%`;
            }
        } catch (e) {
            console.error('Error fetching stats:', e);
        }
    }

    async function fetchComplaints() {
        const tbody = document.getElementById('complaintsTableBody');
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">Loading complaints...</td></tr>';
        try {
            const res = await fetch('/api/complaints');
            const result = await res.json();
            if (result.success && result.data.complaints) {
                tbody.innerHTML = '';
                if (result.data.complaints.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No complaints found.</td></tr>';
                    return;
                }
                result.data.complaints.forEach(c => {
                    const tr = document.createElement('tr');
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
                            <select class="action-select" onchange="updateComplaintStatus('${c.complaint_id}', this.value)">
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
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#f87171;">Failed to load complaints.</td></tr>';
        }
    }

    async function fetchLeaves() {
        const tbody = document.getElementById('leavesTableBody');
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">Loading leave requests...</td></tr>';
        try {
            const res = await fetch('/api/leaves');
            const result = await res.json();
            if (result.success && result.data.leaves) {
                tbody.innerHTML = '';
                if (result.data.leaves.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No leave applications found.</td></tr>';
                    return;
                }
                result.data.leaves.forEach(l => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${l.leave_id}</strong></td>
                        <td>${l.student_name || 'Student #' + l.student_id}</td>
                        <td>${l.room_no || 'N/A'}</td>
                        <td>${l.leave_type}</td>
                        <td>${l.start_date}</td>
                        <td>${l.end_date}</td>
                        <td>${l.reason}</td>
                        <td><span class="badge badge-${(l.status || 'pending').toLowerCase()}">${l.status}</span></td>
                        <td>
                            ${l.status === 'Pending' ? `
                                <button class="btn-action btn-approve" onclick="updateLeaveStatus('${l.leave_id}', 'Approved')">Approve</button>
                                <button class="btn-action btn-reject" onclick="updateLeaveStatus('${l.leave_id}', 'Rejected')">Reject</button>
                            ` : `<span style="color:var(--text-sub); font-size:0.8rem;">Decided</span>`}
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#f87171;">Failed to load leave records.</td></tr>';
        }
    }

    async function fetchVisitors() {
        const tbody = document.getElementById('visitorsTableBody');
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">Loading visitors...</td></tr>';
        try {
            const res = await fetch('/api/visitors');
            const result = await res.json();
            if (result.success && result.data.visitors) {
                tbody.innerHTML = '';
                if (result.data.visitors.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No visitors logged.</td></tr>';
                    return;
                }
                result.data.visitors.forEach(v => {
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
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#f87171;">Failed to load visitors.</td></tr>';
        }
    }

    async function fetchRooms() {
        const tbody = document.getElementById('roomsTableBody');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Loading room occupancy...</td></tr>';
        try {
            const res = await fetch('/api/rooms');
            const result = await res.json();
            if (result.success && result.data.rooms) {
                tbody.innerHTML = '';
                result.data.rooms.forEach(r => {
                    const tr = document.createElement('tr');
                    const isFull = r.occupied_count >= r.capacity;
                    tr.innerHTML = `
                        <td><strong>${r.room_no}</strong></td>
                        <td>${r.block}</td>
                        <td>Floor ${r.floor}</td>
                        <td>${r.capacity} Beds</td>
                        <td>${r.occupied_count} / ${r.capacity}</td>
                        <td><span class="badge badge-${isFull ? 'rejected' : 'resolved'}">${isFull ? 'Fully Occupied' : 'Available'}</span></td>
                        <td><small style="color:var(--text-sub);">${r.amenities}</small></td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#f87171;">Failed to load rooms.</td></tr>';
        }
    }

    async function fetchAuditLogs() {
        const tbody = document.getElementById('logsTableBody');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Loading AI Agent Chat Audit Logs...</td></tr>';
        try {
            const res = await fetch('/api/students');
            // We can also query chat_logs table directly or via a service route.
            // Let's fetch chat_logs via a simple direct endpoint or read
            const logRes = await fetch('/api/chat_logs');
            if (logRes.ok) {
                const result = await logRes.json();
                if (result.success && result.data) {
                    tbody.innerHTML = '';
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
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-sub);">No audit logs captured yet. Interact with the chat interface to generate logs.</td></tr>';
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-sub);">No audit logs captured yet. Interact with the chat interface to generate logs.</td></tr>';
        }
    }

    // Global action helpers
    window.updateComplaintStatus = async (complaintId, status) => {
        if (!status) return;
        try {
            const res = await fetch(`/api/complaints/${complaintId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            const result = await res.json();
            if (result.success) {
                alert(`Complaint ${complaintId} status updated to ${status}.`);
                loadAllDashboardData();
            } else {
                alert(`Failed to update complaint: ${result.message}`);
            }
        } catch (e) {
            alert('Network error updating complaint status.');
        }
    };

    window.updateLeaveStatus = async (leaveId, status) => {
        try {
            const res = await fetch(`/api/leaves/${leaveId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            const result = await res.json();
            if (result.success) {
                alert(`Leave application ${leaveId} updated to ${status}.`);
                loadAllDashboardData();
            } else {
                alert(`Failed to update leave request: ${result.message}`);
            }
        } catch (e) {
            alert('Network error updating leave status.');
        }
    };
});
