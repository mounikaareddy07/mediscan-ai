/* MediScan AI - Pages Module
   All page HTML templates as JavaScript functions */

// ─── Landing Page ────────────────────────────────────────────────────
function renderLandingPage() {
    return `
    <section class="landing-hero">
        <div class="hero-bg-grid"></div>
        <div class="hero-float">🫁</div>
        <div class="hero-float">🔬</div>
        <div class="hero-float">🧬</div>
        <div class="hero-content">
            <div class="hero-badge">
                <span class="hero-badge-dot"></span>
                AI-Powered Medical Imaging
            </div>
            <h1 class="hero-title">
                Intelligent Disease<br>
                <span class="hero-title-gradient">Detection with AI</span>
            </h1>
            <p class="hero-subtitle">
                MediScan AI uses advanced deep learning to detect diseases from chest X-rays, 
                brain MRIs, skin images, retinal scans, and bone X-rays — delivering faster, 
                more accurate diagnosis to assist healthcare professionals.
            </p>
            <div class="hero-actions">
                <button class="btn btn-primary btn-lg" onclick="navigateTo('signup')">
                    Get Started Free →
                </button>
                <button class="btn btn-secondary btn-lg" onclick="navigateTo('login')">
                    Sign In
                </button>
            </div>
                <div class="hero-stats">
                <div class="hero-stat">
                    <div class="hero-stat-value">95%+</div>
                    <div class="hero-stat-label">Detection Accuracy</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-value">&lt;5s</div>
                    <div class="hero-stat-label">Analysis Time</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-value">5</div>
                    <div class="hero-stat-label">Scan Types</div>
                </div>
            </div>
        </div>
    </section>

    <section class="features-section">
        <div class="text-center">
            <span class="section-label">✦ Core Features</span>
            <h2 class="section-title">Why Choose MediScan AI?</h2>
            <p class="section-desc" style="margin-left:auto;margin-right:auto;">
                Our platform combines cutting-edge AI with medical expertise to provide reliable screening.
            </p>
        </div>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <h3 class="feature-title">Deep Learning CNN</h3>
                <p class="feature-desc">Advanced Convolutional Neural Network trained on thousands of medical images for accurate pattern recognition.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3 class="feature-title">Instant Results</h3>
                <p class="feature-desc">Get AI-powered analysis in under 5 seconds. No waiting, no delays — just fast, reliable screening.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔥</div>
                <h3 class="feature-title">Grad-CAM Heatmaps</h3>
                <p class="feature-desc">Visual heatmap overlays highlight exactly where the AI detected abnormalities in the scan.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h3 class="feature-title">AI Assistant</h3>
                <p class="feature-desc">Built-in AI chatbot explains results in plain language and suggests next medical steps.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 class="feature-title">Visual Analytics</h3>
                <p class="feature-desc">Interactive charts and graphs display disease probabilities, scan history trends, and risk analysis.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔒</div>
                <h3 class="feature-title">Secure & Private</h3>
                <p class="feature-desc">All data encrypted with password hashing. Your medical information stays private and protected.</p>
            </div>
        </div>
    </section>`;
}

// ─── Login Page ──────────────────────────────────────────────────────
function renderLoginPage() {
    return `
    <div class="auth-page">
        <div class="auth-card">
            <div class="auth-header">
                <div class="auth-icon">🔐</div>
                <h1 class="auth-title">Welcome Back</h1>
                <p class="auth-subtitle">Sign in to your MediScan AI account</p>
            </div>
            <div id="login-message" class="form-message"></div>
            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label class="form-label" for="login-identifier">Username or Email</label>
                    <input type="text" id="login-identifier" class="form-input" placeholder="Enter username or email" required>
                    <div id="login-identifier-error" class="form-error"></div>
                </div>
                <div class="form-group">
                    <label class="form-label" for="login-password">Password</label>
                    <input type="password" id="login-password" class="form-input" placeholder="Enter your password" required>
                    <div id="login-password-error" class="form-error"></div>
                </div>
                <div class="form-checkbox">
                    <input type="checkbox" id="remember-me">
                    <label for="remember-me">Remember me</label>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%" id="login-btn">
                    Sign In
                </button>
            </form>
            <div class="auth-footer">
                Don't have an account? <span class="link" onclick="navigateTo('signup')">Create one</span>
            </div>
        </div>
    </div>`;
}

// ─── Signup Page ─────────────────────────────────────────────────────
function renderSignupPage() {
    return `
    <div class="auth-page">
        <div class="auth-card">
            <div class="auth-header">
                <div class="auth-icon">✨</div>
                <h1 class="auth-title">Create Account</h1>
                <p class="auth-subtitle">Join MediScan AI for intelligent diagnostics</p>
            </div>
            <div id="signup-message" class="form-message"></div>
            <form id="signup-form" onsubmit="handleSignup(event)">
                <div class="form-group">
                    <label class="form-label" for="signup-fullname">Full Name</label>
                    <input type="text" id="signup-fullname" class="form-input" placeholder="Enter your full name" required>
                    <div id="signup-fullname-error" class="form-error"></div>
                </div>
                <div class="form-group">
                    <label class="form-label" for="signup-username">Username</label>
                    <input type="text" id="signup-username" class="form-input" placeholder="Choose a username" required>
                    <div id="signup-username-error" class="form-error"></div>
                </div>
                <div class="form-group">
                    <label class="form-label" for="signup-email">Email Address</label>
                    <input type="email" id="signup-email" class="form-input" placeholder="Enter your email" required>
                    <div id="signup-email-error" class="form-error"></div>
                </div>
                <div class="form-group">
                    <label class="form-label" for="signup-password">Password</label>
                    <input type="password" id="signup-password" class="form-input" placeholder="Min. 6 characters" required>
                    <div id="signup-password-error" class="form-error"></div>
                </div>
                <div class="form-group">
                    <label class="form-label" for="signup-confirm">Confirm Password</label>
                    <input type="password" id="signup-confirm" class="form-input" placeholder="Confirm your password" required>
                    <div id="signup-confirm-error" class="form-error"></div>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%" id="signup-btn">
                    Create Account
                </button>
            </form>
            <div class="auth-footer">
                Already have an account? <span class="link" onclick="navigateTo('login')">Sign in</span>
            </div>
        </div>
    </div>`;
}

// ─── Home Page (After Login) ─────────────────────────────────────────
function renderHomePage() {
    return `
    <div class="home-page">
        <div class="home-hero">
            <h1 class="home-hero-title">
                Welcome to <span class="hero-title-gradient">MediScan AI</span>
            </h1>
            <p class="home-hero-desc">
                Upload medical images and let our AI analyze them instantly. 
                Detect diseases across 5 scan types — chest X-rays, brain MRI, skin lesions, retinal scans, and bone X-rays.
            </p>
            <button class="btn btn-primary btn-lg" onclick="navigateTo('scan')">
                🔬 Start New Scan
            </button>
        </div>

        <div class="how-it-works">
            <span class="section-label">📋 Process</span>
            <h2 class="section-title">How It Works</h2>
            <p class="section-desc">Our AI analysis follows a proven medical imaging pipeline.</p>
            <div class="steps-grid">
                <div class="step-card">
                    <div class="step-number">1</div>
                    <h3 class="step-title">Upload Scan</h3>
                    <p class="step-desc">Upload your chest X-ray or CT scan image (PNG, JPG, JPEG).</p>
                </div>
                <div class="step-card">
                    <div class="step-number">2</div>
                    <h3 class="step-title">AI Preprocessing</h3>
                    <p class="step-desc">Image is resized, normalized, and enhanced using CLAHE.</p>
                </div>
                <div class="step-card">
                    <div class="step-number">3</div>
                    <h3 class="step-title">Deep Analysis</h3>
                    <p class="step-desc">CNN model extracts features and detects disease patterns.</p>
                </div>
                <div class="step-card">
                    <div class="step-number">4</div>
                    <h3 class="step-title">Get Results</h3>
                    <p class="step-desc">View prediction, risk score, heatmap, and detailed insights.</p>
                </div>
            </div>
        </div>

        <div class="benefits-section">
            <span class="section-label">💡 Benefits</span>
            <h2 class="section-title">Why Early Detection Matters</h2>
            <div class="benefits-grid">
                <div class="benefit-item">
                    <span class="benefit-icon">⏱️</span>
                    <div class="benefit-text">
                        <h4>Faster Diagnosis</h4>
                        <p>AI analysis in seconds vs. hours of manual radiologist review.</p>
                    </div>
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">🎯</span>
                    <div class="benefit-text">
                        <h4>Higher Accuracy</h4>
                        <p>Deep learning models detect subtle patterns humans might miss.</p>
                    </div>
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">💰</span>
                    <div class="benefit-text">
                        <h4>Cost Effective</h4>
                        <p>Reduce healthcare costs with automated preliminary screening.</p>
                    </div>
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">🌍</span>
                    <div class="benefit-text">
                        <h4>Accessible Healthcare</h4>
                        <p>Bring expert-level diagnosis to remote and underserved areas.</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="cta-section">
            <h2 class="cta-title">Ready to Analyze a Scan?</h2>
            <p class="cta-desc">Upload your medical image and get AI-powered results in seconds.</p>
            <button class="btn btn-primary btn-lg" onclick="navigateTo('scan')" style="position:relative">
                🚀 Get Started
            </button>
        </div>
    </div>`;
}

// ─── Scan Upload Page ────────────────────────────────────────────────
function renderScanPage() {
    return `
    <div class="scan-page">
        <div class="scan-header">
            <h1>🔬 Upload Medical Scan</h1>
            <p>Select the scan type, then upload your medical image for AI-powered analysis</p>
        </div>

        <div class="scan-type-section">
            <h3 class="scan-type-label">Select Scan Type</h3>
            <div class="scan-type-grid" id="scan-type-grid">
                <div class="scan-type-card selected" data-type="chest_xray" onclick="selectScanType(this)">
                    <div class="scan-type-icon">🫁</div>
                    <div class="scan-type-name">Chest X-ray</div>
                    <div class="scan-type-desc">Pneumonia detection</div>
                </div>
                <div class="scan-type-card" data-type="brain_tumor" onclick="selectScanType(this)">
                    <div class="scan-type-icon">🧠</div>
                    <div class="scan-type-name">Brain MRI</div>
                    <div class="scan-type-desc">Tumor classification</div>
                </div>
                <div class="scan-type-card" data-type="skin_lesion" onclick="selectScanType(this)">
                    <div class="scan-type-icon">🔬</div>
                    <div class="scan-type-name">Skin Lesion</div>
                    <div class="scan-type-desc">Melanoma screening</div>
                </div>
                <div class="scan-type-card" data-type="retinal" onclick="selectScanType(this)">
                    <div class="scan-type-icon">👁️</div>
                    <div class="scan-type-name">Retinal OCT</div>
                    <div class="scan-type-desc">Retinal disease detection</div>
                </div>
                <div class="scan-type-card" data-type="bone_fracture" onclick="selectScanType(this)">
                    <div class="scan-type-icon">🦴</div>
                    <div class="scan-type-name">Bone X-ray</div>
                    <div class="scan-type-desc">Fracture detection</div>
                </div>
            </div>
        </div>

        <div class="upload-zone" id="upload-zone" onclick="document.getElementById('scan-file-input').click()"
             ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)" ondrop="handleDrop(event)">
            <input type="file" id="scan-file-input" accept=".png,.jpg,.jpeg" onchange="handleFileSelect(event)">
            <div id="upload-placeholder">
                <div class="upload-icon">📤</div>
                <h3 class="upload-title">Drop your scan here</h3>
                <p class="upload-desc">or click to browse files</p>
                <div class="upload-formats">
                    <span class="format-tag">PNG</span>
                    <span class="format-tag">JPG</span>
                    <span class="format-tag">JPEG</span>
                </div>
            </div>
        </div>
        <div class="upload-preview" id="upload-preview">
            <img id="preview-image" class="preview-image" src="" alt="Scan Preview">
            <p class="preview-filename" id="preview-filename"></p>
        </div>
        <div class="upload-actions" id="upload-actions" style="display:none">
            <button class="btn btn-secondary" onclick="clearUpload()">✕ Clear</button>
            <button class="btn btn-primary btn-lg" onclick="analyzeScan()" id="analyze-btn">
                🧠 Analyze with AI
            </button>
        </div>
    </div>`;
}

// ─── Analysis Result Page ────────────────────────────────────────────
function renderResultPage(data) {
    const predClass = data.prediction.toLowerCase().replace(' ', '');
    const riskColor = data.risk_score > 60 ? 'var(--danger)' : data.risk_score > 30 ? 'var(--warning)' : 'var(--success)';
    const confColor = data.confidence > 80 ? 'var(--success)' : data.confidence > 60 ? 'var(--warning)' : 'var(--danger)';

    // Determine if prediction is "normal/safe" or concerning
    const safeClasses = ['normal', 'notumor', 'benign', 'notfractured'];
    const isSafe = safeClasses.includes(predClass);
    const predIcon = isSafe ? '✅' : '⚠️';
    const predBadgeClass = isSafe ? 'prediction-normal' : 'prediction-abnormal';

    const scanTypeDisplay = data.scan_type_display || data.scan_type || 'Medical Scan';
    const modelBadge = data.real_model 
        ? '<span class="model-badge real">🤖 Real AI Model</span>' 
        : '<span class="model-badge simulated">⚡ Simulated Model</span>';

    let insightsHtml = '';
    if (data.insights && data.insights.length) {
        insightsHtml = data.insights.map(i => `
            <div class="insight-item">
                <span class="insight-dot"></span>
                <span>${i}</span>
            </div>`).join('');
    }

    return `
    <div class="result-page">
        <div class="result-header">
            <h1>📋 Analysis Results</h1>
            <p class="result-scan-type">${scanTypeDisplay} ${modelBadge}</p>
        </div>

        <div class="text-center mb-3">
            <div class="prediction-badge ${predBadgeClass}">
                ${predIcon}
                ${data.prediction}
            </div>
        </div>

        <div class="metrics-row">
            <div class="metric-card">
                <div class="metric-value" style="color:${riskColor}">${data.risk_score}%</div>
                <div class="metric-label">Risk Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color:${confColor}">${data.confidence}%</div>
                <div class="metric-label">Confidence</div>
            </div>
        </div>

        <div class="result-grid">
            <div class="result-card">
                <div class="result-card-title">📷 Original Scan</div>
                <div class="result-image-container">
                    <img class="result-image" src="${API_BASE}${data.scan_url}" alt="Original Scan">
                </div>
            </div>
            <div class="result-card">
                <div class="result-card-title">🔥 AI Heatmap Analysis</div>
                <div class="result-image-container">
                    <img class="result-image" src="${API_BASE}${data.heatmap_url}" alt="Heatmap">
                </div>
            </div>
        </div>

        <div class="chart-container">
            <div class="result-card-title">📊 Disease Probability Distribution</div>
            <div class="chart-wrapper">
                <canvas id="probability-chart"></canvas>
            </div>
        </div>

        <div class="insights-card">
            <div class="result-card-title">🔍 Detailed Insights</div>
            ${insightsHtml}
        </div>

        <div class="result-actions">
            <button class="btn btn-secondary" onclick="navigateTo('scan')">🔬 New Scan</button>
            <button class="btn btn-primary" onclick="toggleAssistant()">💬 Ask AI Assistant</button>
            <button class="btn btn-secondary" onclick="navigateTo('dashboard')">📊 Dashboard</button>
        </div>
    </div>`;
}

// ─── Dashboard Page ──────────────────────────────────────────────────
function renderDashboardPage(history) {
    const user = getUser();
    const totalScans = history.length;
    const safePreds = ['Normal', 'NORMAL', 'notumor', 'benign', 'not fractured'];
    const normal = history.filter(s => safePreds.includes(s.prediction)).length;
    const abnormal = totalScans - normal;
    const avgRisk = totalScans > 0 ? (history.reduce((a, s) => a + s.risk_score, 0) / totalScans).toFixed(1) : 0;

    let tableRows = '';
    if (history.length === 0) {
        tableRows = `
        <tr><td colspan="7">
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>No scans yet</h3>
                <p>Upload your first scan to get started with AI analysis.</p>
                <button class="btn btn-primary" onclick="navigateTo('scan')">🔬 Upload Scan</button>
            </div>
        </td></tr>`;
    } else {
        tableRows = history.map(scan => {
            const isSafe = safePreds.includes(scan.prediction);
            const badgeClass = isSafe ? 'normal' : 'pneumonia';
            const riskColor = scan.risk_score > 60 ? 'var(--danger)' : scan.risk_score > 30 ? 'var(--warning)' : 'var(--success)';
            const date = new Date(scan.date).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'});
            return `
            <tr>
                <td><img class="scan-thumb" src="${API_BASE}${scan.scan_url}" alt="scan"></td>
                <td>${scan.filename}</td>
                <td><span class="status-badge ${badgeClass}">${scan.prediction}</span></td>
                <td>
                    <span class="risk-bar"><span class="risk-bar-fill" style="width:${scan.risk_score}%;background:${riskColor}"></span></span>
                    ${scan.risk_score}%
                </td>
                <td>${scan.confidence}%</td>
                <td>${date}</td>
                <td><button class="view-btn" onclick="viewScanDetail(${scan.id})">View</button></td>
            </tr>`;
        }).join('');
    }

    return `
    <div class="dashboard-page">
        <div class="dashboard-header">
            <div>
                <h1>📊 Dashboard</h1>
                <p class="dashboard-welcome">Welcome back, <strong class="text-cyan">${user ? user.username : 'User'}</strong></p>
            </div>
            <button class="btn btn-primary" onclick="navigateTo('scan')">🔬 New Scan</button>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon cyan">🔬</div>
                <div class="stat-info">
                    <h3>${totalScans}</h3>
                    <p>Total Scans</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon teal">✅</div>
                <div class="stat-info">
                    <h3>${normal}</h3>
                    <p>Normal Results</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon pink">⚠️</div>
                <div class="stat-info">
                    <h3>${abnormal}</h3>
                    <p>Abnormal Detected</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon purple">📈</div>
                <div class="stat-info">
                    <h3>${avgRisk}%</h3>
                    <p>Avg Risk Score</p>
                </div>
            </div>
        </div>

        ${totalScans > 0 ? `
        <div class="dashboard-charts">
            <div class="dashboard-chart-card">
                <h3>📊 Scan Results Distribution</h3>
                <div class="dashboard-chart-wrapper">
                    <canvas id="dashboard-pie-chart"></canvas>
                </div>
            </div>
            <div class="dashboard-chart-card">
                <h3>📈 Risk Score History</h3>
                <div class="dashboard-chart-wrapper">
                    <canvas id="dashboard-line-chart"></canvas>
                </div>
            </div>
        </div>` : ''}

        <div class="history-section">
            <h3>🕐 Scan History</h3>
            <div class="history-table-wrapper">
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Image</th>
                            <th>File</th>
                            <th>Prediction</th>
                            <th>Risk</th>
                            <th>Confidence</th>
                            <th>Date</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>${tableRows}</tbody>
                </table>
            </div>
        </div>
    </div>`;
}
