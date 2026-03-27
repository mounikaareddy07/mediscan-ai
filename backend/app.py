"""
MediScan AI - Flask Backend Application
Main API server with endpoints for authentication, scan analysis, and AI assistant.
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import local modules
from database.db import get_db, init_db
from utils.auth import hash_password, verify_password, generate_token, validate_signup
from models.ai_model import predict, get_available_models
from utils.heatmap import generate_heatmap

# ─── App Configuration ───────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mediscan-ai-secret-key-2024')
CORS(app, supports_credentials=True)

# Folder configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
HEATMAP_FOLDER = os.path.join(os.path.dirname(__file__), 'heatmaps')
FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)

# In-memory session store (token → user_id)
active_sessions = {}


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Authentication Endpoints ────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def signup():
    """Register a new user account."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    full_name = data.get('full_name', '').strip()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    # Validate input fields
    errors = validate_signup(full_name, username, email, password, confirm_password)
    if errors:
        return jsonify({'success': False, 'message': errors[0], 'errors': errors}), 400

    # Check if user already exists
    db = get_db()
    existing = db.execute(
        'SELECT id FROM users WHERE email = ? OR username = ?', (email, username)
    ).fetchone()

    if existing:
        db.close()
        return jsonify({'success': False, 'message': 'Email or username already registered'}), 409

    # Create user
    pwd_hash = hash_password(password)
    db.execute(
        'INSERT INTO users (full_name, username, email, password_hash) VALUES (?, ?, ?, ?)',
        (full_name, username, email, pwd_hash)
    )
    db.commit()
    db.close()

    return jsonify({'success': True, 'message': 'Account created successfully! Please login.'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return session token."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    identifier = data.get('identifier', '').strip()  # Can be email or username
    password = data.get('password', '')
    remember = data.get('remember', False)

    if not identifier or not password:
        return jsonify({'success': False, 'message': 'Please fill in all fields'}), 400

    # Find user by email or username
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE email = ? OR username = ?',
        (identifier.lower(), identifier)
    ).fetchone()
    db.close()

    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'success': False, 'message': 'Invalid credentials. Please try again.'}), 401

    # Generate session token
    token = generate_token()
    active_sessions[token] = {
        'user_id': user['id'],
        'username': user['username'],
        'full_name': user['full_name'],
        'email': user['email']
    }

    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'email': user['email']
        }
    })


@app.route('/api/logout', methods=['POST'])
def logout():
    """Invalidate user session."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in active_sessions:
        del active_sessions[token]
    return jsonify({'success': True, 'message': 'Logged out successfully'})


def get_current_user():
    """Get the current authenticated user from the session token."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    return active_sessions.get(token)


# ─── Scan Analysis Endpoints ─────────────────────────────────────────

@app.route('/api/models', methods=['GET'])
def list_models():
    """Return available AI models and their status."""
    return jsonify({'success': True, 'models': get_available_models()})


@app.route('/api/analyze', methods=['POST'])
def analyze_scan():
    """Upload and analyze a medical scan image."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    if 'scan' not in request.files:
        return jsonify({'success': False, 'message': 'No scan file uploaded'}), 400

    file = request.files['scan']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload PNG, JPG, or JPEG'}), 400

    # Get scan type from form data (default: chest_xray)
    scan_type = request.form.get('scan_type', 'chest_xray')

    # Save uploaded file
    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    # Run AI prediction with scan type
    result = predict(file_path, scan_type=scan_type)

    if not result['success']:
        return jsonify({'success': False, 'message': 'Analysis failed. Please try again.'}), 500

    # Generate heatmap
    heatmap_filename = f"heatmap_{unique_filename}"
    heatmap_path = os.path.join(HEATMAP_FOLDER, heatmap_filename)
    generate_heatmap(file_path, result['prediction'], heatmap_path, scan_type=scan_type)

    # Save scan record to database
    db = get_db()
    cursor = db.execute(
        '''INSERT INTO scans 
           (user_id, filename, original_filename, prediction, risk_score, confidence, insights, heatmap_filename) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (user['user_id'], unique_filename, original_filename,
         result['prediction'], result['risk_score'], result['confidence'],
         json.dumps(result['insights']), heatmap_filename)
    )
    scan_id = cursor.lastrowid
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'scan_id': scan_id,
        'prediction': result['prediction'],
        'risk_score': result['risk_score'],
        'confidence': result['confidence'],
        'insights': result['insights'],
        'probabilities': result['probabilities'],
        'scan_type': scan_type,
        'scan_type_display': result.get('scan_type_display', scan_type),
        'real_model': result.get('real_model', False),
        'scan_url': f'/uploads/{unique_filename}',
        'heatmap_url': f'/heatmaps/{heatmap_filename}'
    })


@app.route('/api/history', methods=['GET'])
def get_scan_history():
    """Get scan history for the current user."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    db = get_db()
    scans = db.execute(
        'SELECT * FROM scans WHERE user_id = ? ORDER BY created_at DESC',
        (user['user_id'],)
    ).fetchall()
    db.close()

    history = []
    for scan in scans:
        history.append({
            'id': scan['id'],
            'filename': scan['original_filename'],
            'prediction': scan['prediction'],
            'risk_score': scan['risk_score'],
            'confidence': scan['confidence'],
            'insights': json.loads(scan['insights']) if scan['insights'] else [],
            'scan_url': f'/uploads/{scan["filename"]}',
            'heatmap_url': f'/heatmaps/{scan["heatmap_filename"]}' if scan['heatmap_filename'] else None,
            'date': scan['created_at']
        })

    return jsonify({'success': True, 'history': history})


@app.route('/api/scan/<int:scan_id>', methods=['GET'])
def get_scan_detail(scan_id):
    """Get detailed information about a specific scan."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    db = get_db()
    scan = db.execute(
        'SELECT * FROM scans WHERE id = ? AND user_id = ?',
        (scan_id, user['user_id'])
    ).fetchone()
    db.close()

    if not scan:
        return jsonify({'success': False, 'message': 'Scan not found'}), 404

    return jsonify({
        'success': True,
        'scan': {
            'id': scan['id'],
            'filename': scan['original_filename'],
            'prediction': scan['prediction'],
            'risk_score': scan['risk_score'],
            'confidence': scan['confidence'],
            'insights': json.loads(scan['insights']) if scan['insights'] else [],
            'scan_url': f'/uploads/{scan["filename"]}',
            'heatmap_url': f'/heatmaps/{scan["heatmap_filename"]}' if scan['heatmap_filename'] else None,
            'date': scan['created_at']
        }
    })


# ─── AI Assistant Endpoint ───────────────────────────────────────────

@app.route('/api/assistant', methods=['POST'])
def ai_assistant():
    """AI assistant that helps users understand their scan results."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    data = request.get_json()
    message = data.get('message', '').strip().lower()
    scan_context = data.get('scan_context', None)

    if not message:
        return jsonify({'success': False, 'message': 'Please enter a message'}), 400

    # Generate intelligent response based on context and query
    response = generate_assistant_response(message, scan_context, user['full_name'])

    return jsonify({'success': True, 'response': response})


def generate_assistant_response(message, scan_context, user_name):
    """Generate an intelligent AI assistant response."""

    # Greeting responses
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
        return (f"Hello {user_name}! 👋 I'm MediScan AI Assistant. I can help you understand your "
                f"scan results, explain medical conditions, and provide general health guidance. "
                f"How can I assist you today?")

    # Scan result explanation
    if any(word in message for word in ['explain', 'result', 'scan', 'report', 'analysis', 'diagnosis']):
        if scan_context:
            pred = scan_context.get('prediction', 'Unknown')
            risk = scan_context.get('risk_score', 0)
            conf = scan_context.get('confidence', 0)

            if pred == 'Pneumonia':
                return (f"📋 **Scan Analysis Summary:**\n\n"
                        f"The AI model detected patterns consistent with **Pneumonia** with a "
                        f"confidence of **{conf}%** and a risk score of **{risk}%**.\n\n"
                        f"**What this means:** Pneumonia is an infection that inflames the air sacs "
                        f"in one or both lungs. The air sacs may fill with fluid or pus, causing "
                        f"cough with phlegm, fever, chills, and difficulty breathing.\n\n"
                        f"**Key findings:**\n"
                        f"• Lung opacity detected in lower regions\n"
                        f"• Consolidation patterns observed\n"
                        f"• Possible alveolar inflammation\n\n"
                        f"⚠️ **Important:** This is an AI-assisted screening tool. Please consult "
                        f"a healthcare professional for definitive diagnosis and treatment.")

            elif pred == 'Tuberculosis':
                return (f"📋 **Scan Analysis Summary:**\n\n"
                        f"The AI model detected patterns consistent with **Tuberculosis (TB)** with "
                        f"a confidence of **{conf}%** and a risk score of **{risk}%**.\n\n"
                        f"**What this means:** Tuberculosis is a bacterial infection caused by "
                        f"Mycobacterium tuberculosis. It primarily affects the lungs but can also "
                        f"affect other parts of the body.\n\n"
                        f"**Key findings:**\n"
                        f"• Upper lobe infiltrates detected\n"
                        f"• Possible cavitary lesions\n"
                        f"• Fibrotic changes in apical regions\n\n"
                        f"⚠️ **Important:** Please get tested with AFB sputum smear and consult "
                        f"a pulmonologist for proper diagnosis.")

            else:
                return (f"📋 **Scan Analysis Summary:**\n\n"
                        f"Great news! The AI model found **no significant abnormalities** in your "
                        f"scan with a confidence of **{conf}%**.\n\n"
                        f"Your risk score is **{risk}%**, which is within normal limits.\n\n"
                        f"**Key findings:**\n"
                        f"• Lung fields appear clear\n"
                        f"• Heart size appears normal\n"
                        f"• No signs of infection detected\n\n"
                        f"✅ Continue maintaining good health practices!")

        return ("I'd be happy to explain your scan results! Please upload a scan first, "
                "or select a previous scan from your history to get detailed analysis.")

    # Pneumonia information
    if 'pneumonia' in message:
        return ("🫁 **About Pneumonia:**\n\n"
                "Pneumonia is an infection that inflames the air sacs in the lungs. "
                "It can be caused by bacteria, viruses, or fungi.\n\n"
                "**Common Symptoms:**\n"
                "• Cough with phlegm or pus\n"
                "• Fever, sweating, and chills\n"
                "• Shortness of breath\n"
                "• Chest pain when breathing or coughing\n"
                "• Fatigue and loss of appetite\n\n"
                "**Risk Factors:** Age (very young or elderly), smoking, weakened immune system, "
                "chronic diseases.\n\n"
                "**Prevention:** Vaccination, good hygiene, healthy lifestyle, avoiding smoking.")

    # Tuberculosis information
    if any(word in message for word in ['tuberculosis', 'tb']):
        return ("🦠 **About Tuberculosis (TB):**\n\n"
                "TB is caused by Mycobacterium tuberculosis bacteria. It spreads through "
                "airborne droplets when an infected person coughs or sneezes.\n\n"
                "**Common Symptoms:**\n"
                "• Persistent cough (3+ weeks)\n"
                "• Coughing up blood\n"
                "• Night sweats\n"
                "• Weight loss and fatigue\n"
                "• Fever and chills\n\n"
                "**Treatment:** TB is treatable with a 6-9 month course of antibiotics. "
                "Early detection is crucial for successful treatment.\n\n"
                "**Prevention:** BCG vaccination, avoiding close contact with TB patients, "
                "good ventilation in living spaces.")

    # Risk and precautions
    if any(word in message for word in ['risk', 'precaution', 'prevent', 'safety', 'protect']):
        return ("🛡️ **General Health Precautions:**\n\n"
                "**To reduce respiratory disease risk:**\n"
                "• Get vaccinated (flu, pneumonia, COVID-19)\n"
                "• Practice good hand hygiene\n"
                "• Avoid smoking and secondhand smoke\n"
                "• Maintain a healthy diet rich in vitamins\n"
                "• Exercise regularly to strengthen lungs\n"
                "• Get adequate sleep (7-9 hours)\n"
                "• Wear masks in high-risk environments\n"
                "• Keep living spaces well-ventilated\n\n"
                "**When to see a doctor:**\n"
                "• Persistent cough lasting more than 2 weeks\n"
                "• Difficulty breathing or chest pain\n"
                "• Unexplained weight loss or night sweats\n"
                "• Coughing up blood")

    # How the AI works
    if any(word in message for word in ['how', 'work', 'model', 'ai', 'algorithm', 'detect']):
        return ("🤖 **How MediScan AI Works:**\n\n"
                "Our system uses a **Convolutional Neural Network (CNN)** trained on thousands "
                "of chest X-ray images to detect abnormalities.\n\n"
                "**The Process:**\n"
                "1️⃣ **Upload** — You upload a chest X-ray or CT scan\n"
                "2️⃣ **Preprocess** — Image is resized, normalized, and enhanced\n"
                "3️⃣ **Analyze** — CNN model extracts features and patterns\n"
                "4️⃣ **Predict** — Model classifies as Normal, Pneumonia, or TB\n"
                "5️⃣ **Visualize** — Grad-CAM heatmap highlights areas of concern\n\n"
                "The model outputs a **prediction**, **confidence score**, and **risk percentage** "
                "to help medical professionals make informed decisions.")

    # Help
    if any(word in message for word in ['help', 'what', 'can you', 'feature']):
        return ("💡 **I can help you with:**\n\n"
                "• 📋 Explaining your scan results\n"
                "• 🫁 Information about Pneumonia\n"
                "• 🦠 Information about Tuberculosis\n"
                "• 🛡️ Health precautions and prevention tips\n"
                "• 🤖 How the AI detection system works\n"
                "• ⚕️ When to consult a doctor\n\n"
                "Just type your question and I'll do my best to help! For example:\n"
                "• \"Explain my scan result\"\n"
                "• \"What is pneumonia?\"\n"
                "• \"What precautions should I take?\"")

    # Default response
    return ("I understand your question. As MediScan AI Assistant, I can help you with:\n\n"
            "• Understanding scan results — try \"explain my result\"\n"
            "• Disease information — try \"what is pneumonia\" or \"tell me about TB\"\n"
            "• Health tips — try \"what precautions should I take\"\n"
            "• How the system works — try \"how does the AI work\"\n\n"
            "Feel free to ask anything related to your scan results or respiratory health!")


# ─── File Serving ─────────────────────────────────────────────────────

@app.route('/')
def serve_index():
    """Serve the frontend index.html."""
    return send_from_directory(FRONTEND_FOLDER, 'index.html')


@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'css'), filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files."""
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'js'), filename)


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve asset files."""
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'assets'), filename)


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded scan images."""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/heatmaps/<filename>')
def serve_heatmap(filename):
    """Serve generated heatmap images."""
    return send_from_directory(HEATMAP_FOLDER, filename)


# ─── Admin Endpoint (View Users) ─────────────────────────────────────

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    """View all registered users (for admin/debugging)."""
    db = get_db()
    users = db.execute('SELECT id, full_name, username, email, created_at FROM users').fetchall()
    db.close()
    user_list = [{'id': u['id'], 'full_name': u['full_name'], 'username': u['username'],
                  'email': u['email'], 'created_at': u['created_at']} for u in users]
    return jsonify({'success': True, 'total': len(user_list), 'users': user_list})


# ─── Initialize and Run ──────────────────────────────────────────────

# Initialize DB on import (needed for production)
init_db()

if __name__ == '__main__':
    print("=" * 50)
    print("  MediScan AI - Backend Server")
    print("=" * 50)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    print(f"[Server] Starting on http://localhost:{port}")
    app.run(debug=debug, host='0.0.0.0', port=port)
