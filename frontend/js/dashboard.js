/* MediScan AI - Dashboard Module
   Handles scan history fetching, display, and Chart.js visualizations */

let scanHistory = [];

// ─── Load Dashboard ──────────────────────────────────────────────────
async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/api/history`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await res.json();

        if (data.success) {
            scanHistory = data.history;
            const content = document.getElementById('app-content');
            content.innerHTML = renderDashboardPage(scanHistory);
            // Initialize charts after DOM is ready
            setTimeout(() => initDashboardCharts(scanHistory), 100);
        } else {
            showToast('Failed to load history.', 'error');
        }
    } catch (err) {
        showToast('Connection error loading dashboard.', 'error');
        // Render empty dashboard
        const content = document.getElementById('app-content');
        content.innerHTML = renderDashboardPage([]);
    }
}

// ─── Dashboard Charts ────────────────────────────────────────────────
function initDashboardCharts(history) {
    if (history.length === 0) return;

    // Chart defaults for dark theme
    Chart.defaults.color = '#9ba4c4';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';

    // Pie Chart - Results Distribution
    const pieCtx = document.getElementById('dashboard-pie-chart');
    if (pieCtx) {
        const normal = history.filter(s => s.prediction === 'Normal').length;
        const pneumonia = history.filter(s => s.prediction === 'Pneumonia').length;
        const tb = history.filter(s => s.prediction === 'Tuberculosis').length;

        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Normal', 'Pneumonia', 'Tuberculosis'],
                datasets: [{
                    data: [normal, pneumonia, tb],
                    backgroundColor: [
                        'rgba(46, 213, 115, 0.8)',
                        'rgba(255, 165, 2, 0.8)',
                        'rgba(255, 71, 87, 0.8)'
                    ],
                    borderColor: 'rgba(6, 10, 26, 1)',
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 16,
                            usePointStyle: true,
                            pointStyleWidth: 10,
                            font: { family: 'Inter', size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(13, 19, 51, 0.95)',
                        titleColor: '#e8eaf6',
                        bodyColor: '#9ba4c4',
                        borderColor: 'rgba(0, 212, 255, 0.3)',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                }
            }
        });
    }

    // Line Chart - Risk Score History
    const lineCtx = document.getElementById('dashboard-line-chart');
    if (lineCtx) {
        const reversed = [...history].reverse(); // chronological order
        const labels = reversed.map((s, i) => `Scan ${i + 1}`);
        const risks = reversed.map(s => s.risk_score);
        const confidences = reversed.map(s => s.confidence);

        new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Risk Score',
                        data: risks,
                        borderColor: 'rgba(255, 71, 87, 1)',
                        backgroundColor: 'rgba(255, 71, 87, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        pointBackgroundColor: 'rgba(255, 71, 87, 1)',
                        borderWidth: 2
                    },
                    {
                        label: 'Confidence',
                        data: confidences,
                        borderColor: 'rgba(0, 212, 255, 1)',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        pointBackgroundColor: 'rgba(0, 212, 255, 1)',
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 16,
                            usePointStyle: true,
                            font: { family: 'Inter', size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(13, 19, 51, 0.95)',
                        titleColor: '#e8eaf6',
                        bodyColor: '#9ba4c4',
                        borderColor: 'rgba(0, 212, 255, 0.3)',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + '%' },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

// ─── View Scan Detail ────────────────────────────────────────────────
async function viewScanDetail(scanId) {
    showLoading('Loading scan details...');
    try {
        const res = await fetch(`${API_BASE}/api/scan/${scanId}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await res.json();
        hideLoading();

        if (data.success) {
            const scan = data.scan;
            window.lastScanResult = {
                prediction: scan.prediction,
                risk_score: scan.risk_score,
                confidence: scan.confidence,
                insights: scan.insights,
                scan_url: scan.scan_url,
                heatmap_url: scan.heatmap_url,
                probabilities: {
                    Normal: scan.prediction === 'Normal' ? scan.confidence : (100 - scan.risk_score) * 0.8,
                    Pneumonia: scan.prediction === 'Pneumonia' ? scan.confidence : scan.risk_score * 0.5,
                    Tuberculosis: scan.prediction === 'Tuberculosis' ? scan.confidence : scan.risk_score * 0.3
                }
            };
            renderApp('result', window.lastScanResult);
        } else {
            showToast('Scan not found.', 'error');
        }
    } catch (err) {
        hideLoading();
        showToast('Failed to load scan details.', 'error');
    }
}
