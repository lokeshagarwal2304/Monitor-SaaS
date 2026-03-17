(function() {
    const API_URL = window.API_URL || window.location.origin;
    const token = localStorage.getItem('token');
    
    let currentReportData = null;
    let uptimeChart = null;
    let responseChart = null;
    let selectedMonitorIds = [];

    // Main Init
    async function init() {
        console.log("Reports System: Initializing...");
        if (!token) {
            console.error("No token found, redirecting to login.");
            window.location.href = '/';
            return;
        }

        try {
            await fetchMonitors();
            setupEventListeners();
            console.log("Reports loaded successfully.");
        } catch (err) {
            console.error("Reports load failed:", err);
            alert("Failed to initialize reports: " + err.message);
        }
    }

    async function fetchMonitors() {
        try {
            const res = await fetch(`${API_URL}/api/reports/monitors`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Server responded with " + res.status);
            const monitors = await res.json();
            
            if (!Array.isArray(monitors)) {
                throw new Error("Expected array of monitors, got " + typeof monitors);
            }
            
            renderMonitorChecklist(monitors);
        } catch (err) {
            console.error('Failed to fetch monitors:', err);
            const container = document.getElementById('monitor-checkboxes');
            if (container) container.innerHTML = `<div style="color:var(--accent-downtime); font-size:12px; padding:10px;">Error: ${err.message}</div>`;
        }
    }

    function renderMonitorChecklist(monitors) {
        const container = document.getElementById('monitor-checkboxes');
        if (!container) return;

        let html = `
            <label style="border-bottom: 1px solid var(--border-glass); margin-bottom: 8px; padding-bottom: 8px;">
                <input type="checkbox" id="check-all-monitors" checked>
                <span style="font-weight:800;">Select All</span>
            </label>
        `;

        html += monitors.map(m => `
            <label>
                <input type="checkbox" class="mon-cb" value="${m.id}" data-name="${m.name || m.url}" checked>
                <span>${m.name || m.url}</span>
            </label>
        `).join('');

        container.innerHTML = html;
        updateSelectedText();

        const checkAll = document.getElementById('check-all-monitors');
        const cbs = document.querySelectorAll('.mon-cb');

        checkAll.addEventListener('change', () => {
            cbs.forEach(cb => cb.checked = checkAll.checked);
            updateSelectedText();
        });

        cbs.forEach(cb => {
            cb.addEventListener('change', () => {
                checkAll.checked = Array.from(cbs).every(c => c.checked);
                updateSelectedText();
            });
        });
    }

    function updateSelectedText() {
        const cbs = document.querySelectorAll('.mon-cb:checked');
        const text = document.getElementById('selected-monitors-text');
        if (cbs.length === 0) text.innerText = 'None';
        else if (cbs.length === document.querySelectorAll('.mon-cb').length) text.innerText = 'All Monitors';
        else text.innerText = `${cbs.length} Selected`;
        
        selectedMonitorIds = Array.from(cbs).map(cb => cb.value);
    }

    function setupEventListeners() {
        const trigger = document.getElementById('monitor-select-trigger');
        const dropdown = document.getElementById('monitor-dropdown');
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('show');
        });
        document.addEventListener('click', () => dropdown.classList.remove('show'));
        dropdown.addEventListener('click', (e) => e.stopPropagation());

        document.getElementById('generate-btn').addEventListener('click', generateReport);
        document.getElementById('custom-range-btn').addEventListener('click', () => {
            document.getElementById('custom-modal').classList.add('flex');
        });
        document.getElementById('apply-custom-range').addEventListener('click', () => {
             document.getElementById('custom-modal').classList.remove('flex');
             generateReport();
        });
    }

    async function generateReport() {
        if (selectedMonitorIds.length === 0) {
            alert('Please select at least one monitor');
            return;
        }

        const btn = document.getElementById('generate-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = `<i data-lucide="loader" class="spin"></i> Generating...`;
        lucide.createIcons();
        btn.disabled = true;

        const days = document.getElementById('time-range-select').value;
        const ids = selectedMonitorIds.join(',');

        try {
            const res = await fetch(`${API_URL}/api/reports/dynamic?ids=${ids}&days=${days}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            currentReportData = data;
            showReportContent(data);
        } catch (err) {
            console.error('Report failed:', err);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
            lucide.createIcons();
        }
    }

    function showReportContent(data) {
        document.getElementById('report-empty').style.display = 'none';
        document.getElementById('report-content').style.display = 'flex';
        
        // Stats
        document.getElementById('val-uptime').innerText = `${data.uptime_percentage}%`;
        document.getElementById('val-response').innerText = `${data.average_response_time}ms`;
        document.getElementById('val-checks').innerText = data.total_checks.toLocaleString();
        
        const dm = data.total_downtime_minutes;
        document.getElementById('val-downtime').innerText = dm > 60 ? `${Math.floor(dm/60)}h ${Math.floor(dm%60)}m` : `${Math.floor(dm)}m ${Math.round((dm%1)*60)}s`;

        // Diffs
        updateDiff('diff-uptime', data.diffs.uptime, '%', true);
        updateDiff('diff-response', data.diffs.response, 'ms', false); // lower is better
        updateDiff('diff-checks', data.diffs.checks, '', true);
        updateDiff('diff-downtime', data.diffs.downtime, 'm', false);

        // Chart Labels
        const days = document.getElementById('time-range-select').value;
        document.getElementById('chart-period-uptime').innerText = `(Last ${days} Days)`;
        document.getElementById('chart-period-incidents').innerText = `(Last ${days} Days)`;
        document.getElementById('chart-uptime-pct').innerText = `${data.uptime_percentage}%`;

        renderCharts(data.trends);
        renderPerformanceTable(data.monitors_performance);
        renderIncidents(data.latest_incidents);
        lucide.createIcons();
    }

    function updateDiff(id, val, unit, higherBetter) {
        const el = document.getElementById(id);
        const isUp = val >= 0;
        const colorClass = (isUp === higherBetter) ? 'up' : 'down';
        const icon = isUp ? 'arrow-up-right' : 'arrow-down-right';
        
        el.className = `stat-diff ${colorClass}`;
        el.innerHTML = `<i data-lucide="${icon}" style="width:12px;"></i> ${Math.abs(val)}${unit}`;
    }

    function renderCharts(trends) {
        if (uptimeChart) uptimeChart.destroy();
        if (responseChart) responseChart.destroy();

        uptimeChart = new Chart(document.getElementById('uptime-chart'), {
            type: 'line',
            data: {
                labels: trends.dates,
                datasets: [{
                    data: trends.uptime,
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34,197,94,0.1)',
                    fill: true, tension: 0.4, pointRadius: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display:false } }, scales: { x: { display:false }, y: { display:false, min:0, max:100 } } }
        });

        responseChart = new Chart(document.getElementById('response-chart'), {
            type: 'line',
            data: {
                labels: trends.dates,
                datasets: [{
                    data: trends.response_time,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.1)',
                    fill: true, tension: 0.4, pointRadius: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display:false } }, scales: { x: { display:false }, y: { display:false } } }
        });
    }

    function renderPerformanceTable(monitors) {
        const tbody = document.getElementById('performance-body');
        tbody.innerHTML = monitors.map(m => `
            <tr>
                <td><div style="display:flex; align-items:center; gap:10px;"><i data-lucide="globe" style="width:14px; opacity:0.5;"></i> <b>${m.name}</b></div></td>
                <td><span class="status-badge ${m.status.toLowerCase() === 'up' ? 'up' : 'down'}"><span class="status-dot ${m.status.toLowerCase() === 'up' ? 'up' : 'down'}"></span>${m.status}</span></td>
                <td><b>${m.uptime_percentage}%</b></td>
                <td>${m.avg_response_time}ms</td>
                <td style="color:var(--text-dim);">${m.checks}</td>
                <td style="color:var(--accent-checks); font-weight:700;">${m.incidents}</td>
                <td><canvas id="spark-${m.id}" width="60" height="20"></canvas></td>
                <td>
                    <div style="display:flex; gap:8px; opacity:0.6;">
                        <i data-lucide="external-link" style="width:14px; cursor:pointer;"></i>
                        <i data-lucide="settings" style="width:14px; cursor:pointer;"></i>
                    </div>
                </td>
            </tr>
        `).join('');

        monitors.forEach(m => {
            new Chart(document.getElementById(`spark-${m.id}`), {
                type: 'line',
                data: { labels: m.trend.map((_, i) => i), datasets: [{ data: m.trend, borderColor: m.status === 'UP' ? '#22c55e' : '#ef4444', borderWidth: 1.5, fill: false, pointRadius: 0, tension: 0.4 }] },
                options: { responsive: false, plugins: { legend: { display:false }, tooltip: { enabled:false } }, scales: { x: { display:false }, y: { display:false } } }
            });
        });
    }

    function renderIncidents(incidents) {
        const list = document.getElementById('incidents-list');
        if (incidents.length === 0) {
            list.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-dim); font-size:12px;">No recent incidents found.</div>';
            return;
        }
        list.innerHTML = incidents.map(i => `
            <div class="incident-item">
                <div class="incident-icon ${i.resolved_at ? 'resolved' : ''}"><i data-lucide="${i.resolved_at ? 'check-circle' : 'alert-circle'}"></i></div>
                <div class="incident-body">
                    <div class="incident-name">${i.monitor_name}</div>
                    <div class="incident-meta">${i.resolved_at ? 'Resolved' : 'Ongoing'} • ${Math.round(i.duration_seconds/60)}m</div>
                    <div style="font-size:9px; opacity:0.3;">${new Date(i.started_at).toLocaleTimeString()}</div>
                </div>
            </div>
        `).join('');
    }

    async function downloadReport(format) {
        if (selectedMonitorIds.length === 0) {
            alert('Please select at least one monitor');
            return;
        }

        const days = document.getElementById('time-range-select').value;
        const ids = selectedMonitorIds.join(',');
        const endpoint = format === 'csv' ? 'export/csv' : 'export';
        const url = `${API_URL}/api/reports/${endpoint}?ids=${ids}&days=${days}`;

        try {
            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.status === 401) {
                alert('Session expired. Please login again.');
                window.location.href = '/';
                return;
            }

            if (!res.ok) throw new Error('Export failed');

            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = `MoniFy_Report_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (err) {
            console.error('Export error:', err);
            alert('Failed to export report: ' + err.message);
        }
    }

    window.reports = {
        exportPDF: () => downloadReport('pdf'),
        exportCSV: () => downloadReport('csv')
    };

    document.addEventListener('DOMContentLoaded', init);
})();
