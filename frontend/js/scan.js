/* MediScan AI - Scan Upload & Analysis Module
   Handles drag/drop upload, preview, scan type selection, and API analysis calls */

let selectedFile = null;
let selectedScanType = 'chest_xray';

// ─── Scan Type Selection ─────────────────────────────────────────────
function selectScanType(card) {
    // Remove selected from all cards
    document.querySelectorAll('.scan-type-card').forEach(c => {
        c.classList.remove('selected');
    });
    // Add selected to clicked card
    card.classList.add('selected');
    selectedScanType = card.dataset.type;
}

// ─── Drag & Drop Handlers ────────────────────────────────────────────
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('upload-zone').classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('upload-zone').classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('upload-zone').classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// ─── File Selection ──────────────────────────────────────────────────
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function processFile(file) {
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        showToast('Invalid file type. Please upload PNG, JPG, or JPEG.', 'error');
        return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('File too large. Maximum size is 10MB.', 'error');
        return;
    }

    selectedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('upload-preview');
        const previewImg = document.getElementById('preview-image');
        const previewName = document.getElementById('preview-filename');
        const actions = document.getElementById('upload-actions');
        const zone = document.getElementById('upload-zone');

        previewImg.src = e.target.result;
        previewName.textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
        preview.classList.add('visible');
        actions.style.display = 'flex';
        zone.classList.add('has-file');

        // Hide the placeholder text
        const placeholder = document.getElementById('upload-placeholder');
        if (placeholder) placeholder.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// ─── Clear Upload ────────────────────────────────────────────────────
function clearUpload() {
    selectedFile = null;
    const preview = document.getElementById('upload-preview');
    const actions = document.getElementById('upload-actions');
    const zone = document.getElementById('upload-zone');
    const placeholder = document.getElementById('upload-placeholder');
    const fileInput = document.getElementById('scan-file-input');

    if (preview) preview.classList.remove('visible');
    if (actions) actions.style.display = 'none';
    if (zone) zone.classList.remove('has-file');
    if (placeholder) placeholder.style.display = 'block';
    if (fileInput) fileInput.value = '';
}

// ─── Analyze Scan ────────────────────────────────────────────────────
async function analyzeScan() {
    if (!selectedFile) {
        showToast('Please upload a scan image first.', 'error');
        return;
    }

    const scanTypeNames = {
        'chest_xray': 'Chest X-ray',
        'brain_tumor': 'Brain MRI',
        'skin_lesion': 'Skin Lesion',
        'retinal': 'Retinal OCT',
        'bone_fracture': 'Bone X-ray'
    };

    showLoading(`Analyzing ${scanTypeNames[selectedScanType] || 'scan'} with AI...`);

    const formData = new FormData();
    formData.append('scan', selectedFile);
    formData.append('scan_type', selectedScanType);

    try {
        const res = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getToken()}` },
            body: formData
        });
        const data = await res.json();
        hideLoading();

        if (data.success) {
            showToast('Analysis complete!', 'success');
            // Store last result for AI assistant context
            window.lastScanResult = data;
            // Render result page
            renderApp('result', data);
        } else {
            showToast(data.message || 'Analysis failed.', 'error');
        }
    } catch (err) {
        hideLoading();
        showToast('Connection error. Is the backend running?', 'error');
    }
}

// ─── Render Result with Charts ───────────────────────────────────────
function initProbabilityChart(probabilities) {
    const ctx = document.getElementById('probability-chart');
    if (!ctx) return;

    const labels = Object.keys(probabilities);
    const values = Object.values(probabilities);

    // Generate colors based on number of classes
    const colorPalettes = {
        2: [
            { bg: 'rgba(46, 213, 115, 0.7)', border: 'rgba(46, 213, 115, 1)' },
            { bg: 'rgba(255, 71, 87, 0.7)', border: 'rgba(255, 71, 87, 1)' }
        ],
        3: [
            { bg: 'rgba(46, 213, 115, 0.7)', border: 'rgba(46, 213, 115, 1)' },
            { bg: 'rgba(255, 165, 2, 0.7)', border: 'rgba(255, 165, 2, 1)' },
            { bg: 'rgba(255, 71, 87, 0.7)', border: 'rgba(255, 71, 87, 1)' }
        ],
        4: [
            { bg: 'rgba(46, 213, 115, 0.7)', border: 'rgba(46, 213, 115, 1)' },
            { bg: 'rgba(0, 212, 255, 0.7)', border: 'rgba(0, 212, 255, 1)' },
            { bg: 'rgba(255, 165, 2, 0.7)', border: 'rgba(255, 165, 2, 1)' },
            { bg: 'rgba(255, 71, 87, 0.7)', border: 'rgba(255, 71, 87, 1)' }
        ]
    };

    // Default: generate colors dynamically
    const palette = colorPalettes[labels.length] || labels.map((_, i) => {
        const hue = (i * 360 / labels.length + 120) % 360;
        return {
            bg: `hsla(${hue}, 70%, 55%, 0.7)`,
            border: `hsla(${hue}, 70%, 55%, 1)`
        };
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probability (%)',
                data: values,
                backgroundColor: palette.map(p => p.bg),
                borderColor: palette.map(p => p.border),
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
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
                    ticks: { color: '#5a6380', callback: v => v + '%' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                x: {
                    ticks: { color: '#9ba4c4' },
                    grid: { display: false }
                }
            }
        }
    });
}
