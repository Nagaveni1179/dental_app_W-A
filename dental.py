from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import zoneinfo
import os
import json
import re
import pymysql
import sys
import io
import base64
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import cloudinary
import cloudinary.uploader

def get_ist_now():
    """Returns current datetime in Asia/Kolkata (IST) timezone without tzinfo for MySQL compatibility."""
    try:
        ist = zoneinfo.ZoneInfo("Asia/Kolkata")
        return datetime.now(ist).replace(tzinfo=None)
    except Exception:
        return datetime.now()

def format_local_dt(dt):
    """Formats datetime object into user-friendly IST local string."""
    if not dt:
        return None
    return dt.strftime('%d %b %Y, %I:%M %p')

# Force UTF-8 output streams on Windows to prevent 'charmap' codec errors when printing emojis/Unicode
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def sanitize_text(text):
    """Ensure text is valid UTF-8 and safely encodeable without surrogate/charmap errors."""
    if not text:
        return ""

    if not isinstance(text, str):
        text = str(text)

    return text.encode("utf-8", errors="replace").decode("utf-8")

def clean_thinking_text(text):
    """Remove <think>...</think> reasoning and return only the final answer."""
    if not text:
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    if "</think>" in text:
        text = text.split("</think>", 1)[1]

    return text.strip()

def safe_print(*args, **kwargs):
    """Safely print text to standard output on Windows systems."""
    try:
        print(*args, **kwargs)
    except Exception:
        safe_args = [
            arg.encode('ascii', errors='backslashreplace').decode('ascii')
            if isinstance(arg, str) else arg for arg in args
        ]
        print(*safe_args, **kwargs)

pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app)

# ============================
# Load TensorFlow AI Model
# ============================
MODEL_PATH = "dental_model.h5"
CLASS_NAMES_PATH = "class_names.json"

try:
    model = load_model(MODEL_PATH)

    with open(CLASS_NAMES_PATH, "r") as f:
        class_names = json.load(f)

    safe_print("✅ TensorFlow model loaded successfully!")
    safe_print("Classes:", class_names)

except Exception as e:
    safe_print("❌ Error loading TensorFlow model:", e)
    model = None
    class_names = ["Calculus", "Data caries", "Gingivitis", "Hypodontia", "Mouth Ulcer", "Tooth Discoloration"]

DISEASE_INFO = {
    "Calculus": {
        "description": "Calculus (tartar) is hardened dental plaque that forms on teeth over time. If untreated, it can lead to gum disease and tooth loss.",
        "symptoms": [
            "Bleeding gums",
            "Bad breath",
            "Swollen gums",
            "Rough deposits on teeth"
        ],
        "causes": [
            "Poor oral hygiene",
            "Plaque buildup",
            "Smoking",
            "Sugary diet"
        ],
        "treatment": [
            "Professional dental scaling",
            "Regular brushing",
            "Daily flossing",
            "Antibacterial mouthwash"
        ],
        "prevention": [
            "Brush twice daily",
            "Visit dentist every 6 months",
            "Reduce sugary foods",
            "Maintain oral hygiene"
        ]
    },
    "Data caries": {
        "description": "Dental caries (tooth decay) is caused by bacteria that damage the tooth enamel.",
        "symptoms": [
            "Tooth pain",
            "Sensitivity",
            "Visible holes",
            "Dark spots"
        ],
        "causes": [
            "Sugar",
            "Poor brushing",
            "Plaque bacteria"
        ],
        "treatment": [
            "Dental filling",
            "Root canal if severe",
            "Fluoride treatment"
        ],
        "prevention": [
            "Brush regularly",
            "Avoid sugary foods",
            "Dental checkups"
        ]
    },
    "Gingivitis": {
        "description": "Gingivitis is inflammation of the gums caused by plaque buildup.",
        "symptoms": [
            "Red gums",
            "Bleeding while brushing",
            "Swollen gums"
        ],
        "causes": [
            "Plaque",
            "Poor oral hygiene"
        ],
        "treatment": [
            "Professional cleaning",
            "Improve brushing",
            "Daily flossing"
        ],
        "prevention": [
            "Brush twice daily",
            "Routine dental visits"
        ]
    },
    "Hypodontia": {
        "description": "Hypodontia is a condition where one or more teeth fail to develop naturally.",
        "symptoms": [
            "Missing teeth",
            "Spacing"
        ],
        "causes": [
            "Genetics"
        ],
        "treatment": [
            "Dental implants",
            "Braces",
            "Dental bridge"
        ],
        "prevention": [
            "Early dental consultation"
        ]
    },
    "Mouth Ulcer": {
        "description": "A mouth ulcer is a painful sore inside the mouth.",
        "symptoms": [
            "Pain",
            "White ulcer",
            "Difficulty eating"
        ],
        "causes": [
            "Stress",
            "Vitamin deficiency",
            "Injury"
        ],
        "treatment": [
            "Ulcer gel",
            "Pain relief",
            "Vitamin supplements"
        ],
        "prevention": [
            "Balanced diet",
            "Good oral hygiene"
        ]
    },
    "Tooth Discoloration": {
        "description": "Tooth discoloration refers to changes in the natural color of teeth.",
        "symptoms": [
            "Yellow teeth",
            "Brown stains",
            "White spots"
        ],
        "causes": [
            "Coffee",
            "Tea",
            "Smoking",
            "Poor brushing"
        ],
        "treatment": [
            "Teeth whitening",
            "Professional cleaning"
        ],
        "prevention": [
            "Brush twice daily",
            "Limit staining drinks"
        ]
    }
}

def predict_dental_image(image_bytes):
    """Classifies a dental image using local TensorFlow model and class_names.json."""
    if model is None:
        raise Exception("TensorFlow model is not loaded.")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_resized = img.resize((224, 224))

    img_array = np.array(img_resized, dtype=np.float32)
    img_array = preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)
    predicted_index = int(np.argmax(predictions[0]))
    confidence = float(np.max(predictions[0]))

    if class_names and predicted_index < len(class_names):
        condition = class_names[predicted_index]
    else:
        condition = "Dental Condition Detected"

    conf_pct = confidence * 100.0

    if condition == "Calculus":
        severity = "Moderate"
        findings = [
            "Visible hardened dental plaque/tartar buildup along the gumline.",
            "Signs of localized gingival irritation."
        ]
        recommendations = [
            "Schedule a professional dental scaling and cleaning (prophylaxis).",
            "Maintain daily flossing and anti-plaque mouthwash routine."
        ]
        summary = f"Calculus detected with {conf_pct:.1f}% confidence. Hardened plaque deposits along teeth margins."
    elif condition == "Data caries":
        severity = "Severe" if confidence > 0.8 else "Moderate"
        findings = [
            "Localized tooth decay / cavity lesion detected on enamel surface.",
            "Demineralization of enamel/dentin layer observed."
        ]
        recommendations = [
            "Consult a dentist promptly for restorative treatment (filling/crown).",
            "Maintain good oral hygiene and limit sugary foods/drinks."
        ]
        summary = f"Data caries (Tooth decay) detected with {conf_pct:.1f}% confidence. Cavity lesion visible."
    elif condition == "Gingivitis":
        severity = "Moderate"
        findings = [
            "Erythematous, swollen, or inflamed gum tissue.",
            "Signs of early periodontal inflammation."
        ]
        recommendations = [
            "Improve daily oral hygiene using a soft-bristled toothbrush.",
            "Use warm salt water or chlorhexidine mouthwash."
        ]
        summary = f"Gingivitis detected with {conf_pct:.1f}% confidence. Inflammation of the gum tissue identified."
    elif condition == "Hypodontia":
        severity = "Mild"
        findings = [
            "Congenitally missing tooth or empty socket space observed.",
            "Alveolar space alteration present."
        ]
        recommendations = [
            "Consult an orthodontist or prosthodontist for replacement options.",
            "Evaluate options such as implants, bridges, or space closure."
        ]
        summary = f"Hypodontia detected with {conf_pct:.1f}% confidence. Missing tooth space observed."
    elif condition == "Mouth Ulcer":
        severity = "Moderate"
        findings = [
            "Localized oral mucosal ulceration/lesion present.",
            "Erythematous border surrounding central mucosal defect."
        ]
        recommendations = [
            "Apply topical oral anesthetic gel or protective paste.",
            "Avoid spicy, acidic, or hard foods until healed."
        ]
        summary = f"Mouth Ulcer detected with {conf_pct:.1f}% confidence. Oral mucosal lesion identified."
    elif condition == "Tooth Discoloration":
        severity = "Mild"
        findings = [
            "Surface staining or enamel shade alteration.",
            "Extrinsic/intrinsic tooth color variations visible."
        ]
        recommendations = [
            "Schedule professional dental prophylaxis polishing or whitening.",
            "Reduce consumption of staining items like coffee, tea, or tobacco."
        ]
        summary = f"Tooth Discoloration detected with {conf_pct:.1f}% confidence. Enamel staining noted."
    else:
        severity = "Mild"
        findings = [f"Visual features matching {condition} detected."]
        recommendations = ["Consult a dental professional for detailed examination."]
        summary = f"{condition} detected with {conf_pct:.1f}% confidence."

    info = DISEASE_INFO.get(condition, {})

    symptoms_list = info.get("symptoms", [])
    causes_list = info.get("causes", [])
    treatment_list = info.get("treatment", recommendations)
    prevention_list = info.get("prevention", [])

    symptoms_str = '\n• '.join(symptoms_list) if symptoms_list else "None listed"
    causes_str = '\n• '.join(causes_list) if causes_list else "None listed"
    findings_str = '\n• '.join(findings) if findings else "None listed"
    recommendations_str = '\n• '.join(treatment_list) if treatment_list else "None listed"
    prevention_str = '\n• '.join(prevention_list) if prevention_list else "None listed"

    analysis = f"""
🦷 AI DENTAL HEALTH REPORT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONDITION DETECTED
{condition}

CONFIDENCE SCORE
{conf_pct:.1f}%

SEVERITY
{severity}

DESCRIPTION
{info.get("description", "Not available")}

POSSIBLE SYMPTOMS
• {symptoms_str}

POSSIBLE CAUSES
• {causes_str}

OBSERVATIONS
• {findings_str}

RECOMMENDED TREATMENT
• {recommendations_str}

PREVENTION TIPS
• {prevention_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISCLAIMER

This AI analysis is intended for educational and preliminary screening purposes only. It should not be considered a final diagnosis. Please consult a qualified dentist for confirmation and treatment.
""".strip()

    return {
        "condition": condition,
        "confidence": confidence,
        "severity": severity,
        "findings": findings,
        "recommendations": recommendations,
        "summary": summary,
        "analysis": analysis
    }

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:@localhost/dentalinsight?charset=utf8mb4"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dentalinsight_secret'
app.config['JSON_AS_ASCII'] = False

if hasattr(app, 'json'):
    app.json.ensure_ascii = False

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', ''),
)

db = SQLAlchemy(app)

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name           = db.Column(db.String(255), nullable=False)
    email          = db.Column(db.String(255), unique=True, nullable=False)
    password       = db.Column(db.String(255), nullable=False)
    role           = db.Column(db.String(20), default='patient')  # patient|dentist|admin
    phone          = db.Column(db.String(20), nullable=True)
    age            = db.Column(db.Integer, default=0)
    gender         = db.Column(db.String(10), nullable=True)
    specialization = db.Column(db.String(150), nullable=True)     # dentists only
    created_at     = db.Column(db.DateTime, default=get_ist_now)

class ActiveSession(db.Model):
    __tablename__ = 'active_sessions'
    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email    = db.Column(db.String(255), nullable=False)
    login_at = db.Column(db.DateTime, default=get_ist_now)

class Scan(db.Model):
    __tablename__ = 'scans'
    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name    = db.Column(db.String(255), nullable=False)
    image_url       = db.Column(db.Text, nullable=False)          # Cloudinary URL or Data URI
    notes           = db.Column(db.Text, nullable=True)           # patient's notes
    condition       = db.Column(db.String(255), nullable=True)    # e.g. "Tooth decay"
    severity        = db.Column(db.String(20), default='Mild')    # Mild|Moderate|Severe
    findings        = db.Column(db.Text, nullable=True)           # JSON array
    recommendations = db.Column(db.Text, nullable=True)           # JSON array
    analysis        = db.Column(db.Text, nullable=True)           # full analysis text
    summary         = db.Column(db.Text, nullable=True)
    dentist_id      = db.Column(db.Integer, nullable=True)
    dentist_name    = db.Column(db.String(255), nullable=True)
    dentist_note    = db.Column(db.Text, nullable=True)
    review_status   = db.Column(db.String(15), default='Pending')  # Pending|Reviewed
    created_at      = db.Column(db.DateTime, default=get_ist_now)

class PainAssessment(db.Model):
    __tablename__ = 'pain_assessments'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    intensity    = db.Column(db.Integer, default=0)               # 0-10
    duration     = db.Column(db.String(50), nullable=True)
    trigger      = db.Column(db.String(50), nullable=True)
    swelling     = db.Column(db.Boolean, default=False)
    sensitivity  = db.Column(db.Boolean, default=False)
    bleeding     = db.Column(db.Boolean, default=False)
    score        = db.Column(db.Integer, default=0)               # 0-100
    severity     = db.Column(db.String(20), default='Mild')       # Mild|Moderate|Severe
    advice       = db.Column(db.Text, nullable=True)              # clinical advice
    created_at   = db.Column(db.DateTime, default=get_ist_now)

class AnesthesiaPrediction(db.Model):
    __tablename__ = 'anesthesia_predictions'
    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name       = db.Column(db.String(255), nullable=False)
    region             = db.Column(db.String(255), nullable=True)
    infection          = db.Column(db.String(10), default='No')
    inflammation       = db.Column(db.String(20), default='Mild')
    anxiety            = db.Column(db.String(20), default='Low')
    history            = db.Column(db.String(10), default='No')   # prior failure
    medical_conditions = db.Column(db.Text, nullable=True)
    medications        = db.Column(db.Text, nullable=True)
    risk_level         = db.Column(db.String(15), default='Low')  # Low|Moderate|High
    confidence         = db.Column(db.Float, default=0.0)
    result             = db.Column(db.Text, nullable=True)        # full prediction text
    created_at         = db.Column(db.DateTime, default=get_ist_now)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    dentist_id   = db.Column(db.Integer, nullable=True)
    dentist_name = db.Column(db.String(255), nullable=False)
    date         = db.Column(db.String(30), nullable=False)
    time         = db.Column(db.String(20), nullable=False)
    status       = db.Column(db.String(15), default='Pending')   # Pending|Confirmed|Declined
    created_at   = db.Column(db.DateTime, default=get_ist_now)

class Consultation(db.Model):
    __tablename__ = 'consultations'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    dentist_id   = db.Column(db.Integer, nullable=True)
    message      = db.Column(db.Text, nullable=False)
    reply        = db.Column(db.Text, nullable=True)
    status       = db.Column(db.String(15), default='Pending')   # Pending|Replied
    created_at   = db.Column(db.DateTime, default=get_ist_now)

# ─────────────────────────────────────────
# JSON HELPERS
# ─────────────────────────────────────────

def user_to_json(u):
    return {
        'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role,
        'phone': u.phone or '', 'age': u.age or 0, 'gender': u.gender or '',
        'specialization': u.specialization or '',
    }

def scan_to_json(s):
    clean_analysis = clean_thinking_text(s.analysis or '')
    clean_summary = clean_thinking_text(s.summary or (clean_analysis[:200] if clean_analysis else ''))
    return {
        'id': s.id,
        'patient_id': s.patient_id,
        'patient_name': s.patient_name,
        'image_url': s.image_url,
        'notes': s.notes or '',
        'condition': s.condition or '',
        'severity': s.severity or 'Mild',
        'findings': json.loads(s.findings) if s.findings else [],
        'recommendations': json.loads(s.recommendations) if s.recommendations else [],
        'analysis': clean_analysis,
        'summary': clean_summary,
        'dentist_name': s.dentist_name,
        'dentist_note': s.dentist_note,
        'review_status': s.review_status,
        'created_at': format_local_dt(s.created_at),
    }

def pain_to_json(p):
    return {
        'id': p.id,
        'patient_id': p.patient_id,
        'patient_name': p.patient_name,
        'intensity': p.intensity,
        'duration': p.duration,
        'trigger': p.trigger,
        'swelling': p.swelling,
        'sensitivity': p.sensitivity,
        'bleeding': p.bleeding,
        'score': p.score,
        'severity': p.severity,
        'advice': clean_thinking_text(p.advice or ''),
        'created_at': format_local_dt(p.created_at),
    }

def anesthesia_to_json(a):
    return {
        'id': a.id,
        'patient_id': a.patient_id,
        'patient_name': a.patient_name,
        'region': a.region,
        'infection': a.infection,
        'inflammation': a.inflammation,
        'anxiety': a.anxiety,
        'history': a.history,
        'medical_conditions': a.medical_conditions or '',
        'medications': a.medications or '',
        'risk_level': a.risk_level,
        'confidence': float(a.confidence),
        'result': clean_thinking_text(a.result or ''),
        'created_at': format_local_dt(a.created_at),
    }

def appointment_to_json(a):
    return {
        'id': a.id,
        'patient_id': a.patient_id,
        'patient_name': a.patient_name,
        'dentist_id': a.dentist_id,
        'dentist_name': a.dentist_name,
        'date': a.date,
        'time': a.time,
        'status': a.status,
        'created_at': format_local_dt(a.created_at),
    }

def consultation_to_json(c):
    return {
        'id': c.id,
        'patient_id': c.patient_id,
        'patient_name': c.patient_name,
        'dentist_id': c.dentist_id,
        'message': c.message,
        'reply': clean_thinking_text(c.reply or ''),
        'status': c.status,
        'created_at': format_local_dt(c.created_at),
    }

# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        required = ['name', 'email', 'password', 'role']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        if data['role'] not in ('patient', 'dentist'):
            return jsonify({'error': 'Invalid role'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        new_user = User(
            name=data['name'], email=data['email'],
            password=generate_password_hash(data['password']),
            role=data['role'],
            phone=data.get('phone', ''),
            age=int(data.get('age', 0) or 0),
            gender=data.get('gender', ''),
            specialization=data.get('specialization', ''),
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully',
                        'user': user_to_json(new_user)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        session = ActiveSession(email=user.email)
        db.session.add(session)
        db.session.commit()
        return jsonify({'message': 'Login successful',
                        'user': user_to_json(user)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/get_current_user', methods=['GET'])
def get_current_user():
    try:
        last = ActiveSession.query.order_by(ActiveSession.id.desc()).first()
        if not last:
            return jsonify({'error': 'No active user found'}), 404
        user = User.query.filter_by(email=last.email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user_to_json(user)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/change_password', methods=['POST'])
def change_password():
    try:
        data = request.get_json()
        required = ['email', 'current_password', 'new_password']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        if len(data['new_password']) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        user.password = generate_password_hash(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# SCANS (oral image analysis)
# ─────────────────────────────────────────

@app.route('/scans', methods=['POST'])
def add_scan():
    try:
        safe_print("\n========== START AI SCAN ANALYSIS ==========")

        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        image = request.files['image']
        form = request.form

        patient_id = form.get('patient_id')
        patient_name = form.get('patient_name', '')

        if not patient_id:
            return jsonify({'error': 'patient_id required'}), 400

        patient_notes = form.get('notes', '')

        # Read image bytes before Cloudinary consumes it
        image_bytes = image.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = image.mimetype if image.mimetype else 'image/jpeg'

        # Reset pointer for Cloudinary
        image.seek(0)

        # Upload image to Cloudinary with fallback
        try:
            upload_result = cloudinary.uploader.upload(image, folder='dentalinsight')
            image_url = upload_result['secure_url']
            safe_print(f"Cloudinary URL: {image_url}")
        except Exception as e:
            safe_print("Cloudinary upload fallback:", e)
            image_url = f"data:{mime_type};base64,{base64_image}"

        # Perform local TensorFlow classification
        safe_print("Running local TensorFlow inference...")
        prediction_result = predict_dental_image(image_bytes)

        condition = prediction_result["condition"]
        severity = prediction_result["severity"]
        findings = prediction_result["findings"]
        recommendations = prediction_result["recommendations"]
        summary = prediction_result["summary"]
        analysis = prediction_result["analysis"]

        safe_print(f"Predicted Condition: {condition}")
        safe_print(f"Confidence: {prediction_result['confidence']:.4f}")
        safe_print(f"Severity: {severity}")

        safe_print("Saving to database...")
        new_scan = Scan(
            patient_id=int(patient_id),
            patient_name=patient_name,
            image_url=image_url,
            notes=sanitize_text(patient_notes),
            condition=condition,
            severity=severity,
            findings=json.dumps(findings),
            recommendations=json.dumps(recommendations),
            analysis=analysis,
            summary=summary
        )
        db.session.add(new_scan)

        # Save consultation automatically
        new_consult = Consultation(
            patient_id=int(patient_id),
            patient_name=patient_name,
            message=f"AI Scan Analysis:\nSeverity: {severity}\n\nNotes: {patient_notes}\nAnalysis: {analysis}",
            status='Pending'
        )
        db.session.add(new_consult)

        db.session.commit()
        safe_print("Database save successful.")
        safe_print("========== END AI SCAN ANALYSIS ==========\n")

        return jsonify({
            "message": "Scan saved",
            "analysis": analysis,
            "scan": scan_to_json(new_scan)
        }), 201

    except Exception as e:
        db.session.rollback()
        import traceback
        safe_print("\n========== ERROR ==========")
        safe_print(f"Type: {type(e)}")
        safe_print(f"Message: {str(e)}")
        traceback.print_exc()
        safe_print("===========================\n")
        return jsonify({'error': str(e)}), 500

@app.route('/scans/patient/<int:user_id>', methods=['GET'])
def get_patient_scans(user_id):
    try:
        scans = Scan.query.filter_by(patient_id=user_id)\
            .order_by(Scan.created_at.desc()).all()

        return jsonify([scan_to_json(s) for s in scans]), 200

    except Exception as e:
        db.session.rollback()
        safe_print("========== ERROR ==========")
        safe_print(e)
        safe_print("===========================")
        return jsonify({'error': str(e)}), 500

@app.route('/scans', methods=['GET'])
def get_all_scans():
    try:
        status = request.args.get('status')
        q = Scan.query
        if status:
            q = q.filter_by(review_status=status)
        scans = q.order_by(Scan.created_at.desc()).all()
        return jsonify([scan_to_json(s) for s in scans]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scans/<int:scan_id>', methods=['GET'])
def get_scan(scan_id):
    try:
        s = Scan.query.get(scan_id)
        if not s:
            return jsonify({'error': 'Scan not found'}), 404
        return jsonify(scan_to_json(s)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scans/<int:scan_id>/review', methods=['POST'])
def review_scan(scan_id):
    try:
        data = request.get_json()
        s = Scan.query.get(scan_id)
        if not s:
            return jsonify({'error': 'Scan not found'}), 404
        s.dentist_id    = data.get('dentist_id')
        s.dentist_name  = data.get('dentist_name')
        s.dentist_note  = data.get('dentist_note')
        s.review_status = 'Reviewed'
        db.session.commit()
        return jsonify({'message': 'Review saved', 'scan': scan_to_json(s)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# PAIN ASSESSMENTS
# ─────────────────────────────────────────

@app.route('/pain', methods=['POST'])
def add_pain():
    try:
        data = request.get_json()
        if not data or 'patient_id' not in data:
            return jsonify({'error': 'patient_id required'}), 400

        score = int(data.get('score', 0))
        trigger = data.get('trigger', '')
        swelling = bool(data.get('swelling', False))
        sensitivity = bool(data.get('sensitivity', False))
        bleeding = bool(data.get('bleeding', False))

        severity = data.get('severity', 'Mild')

        if score >= 70 or severity == 'Severe' or swelling:
            advice = (
                f"High pain intensity ({score}/100) recorded. Urgent dental examination is recommended. "
                "Apply an external cold compress to minimize swelling and take over-the-counter analgesics as advised by your healthcare provider. Avoid hard, hot, or cold foods."
            )
        elif score >= 40 or severity == 'Moderate' or bleeding:
            advice = (
                f"Moderate pain intensity ({score}/100) recorded. Schedule a dental appointment soon. "
                "Rinse gently with warm salt water, maintain light brushing, and avoid chewing on the affected side."
            )
        else:
            advice = (
                f"Mild dental discomfort ({score}/100) recorded. Continue careful brushing and flossing. "
                "If discomfort persists or worsens, consult your dentist for a routine checkup."
            )

        pain = PainAssessment(
            patient_id=int(data['patient_id']),
            patient_name=data.get('patient_name', ''),
            intensity=int(data.get('intensity', 0)),
            duration=data.get('duration', ''),
            trigger=trigger,
            swelling=swelling,
            sensitivity=sensitivity,
            bleeding=bleeding,
            score=score,
            severity=severity,
            advice=advice,
        )

        db.session.add(pain)
        db.session.commit()

        return jsonify({
            'message': 'Pain assessment saved',
            'advice': advice,
            'pain': pain_to_json(pain)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/pain/patient/<int:user_id>', methods=['GET'])
def get_patient_pain_assessments(user_id):
    try:
        pains = PainAssessment.query.filter_by(patient_id=user_id)\
            .order_by(PainAssessment.created_at.desc()).all()
        return jsonify([pain_to_json(p) for p in pains]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# ANESTHESIA PREDICTIONS
# ─────────────────────────────────────────

@app.route('/anesthesia', methods=['POST'])
def add_anesthesia():
    try:
        data = request.get_json()

        if not data or 'patient_id' not in data:
            return jsonify({'error': 'patient_id required'}), 400

        infection = data.get('infection', 'No')
        inflammation = data.get('inflammation', 'Mild')
        anxiety = data.get('anxiety', 'Low')
        history = data.get('history', 'No')

        if infection == 'Yes' or history == 'Yes' or inflammation == 'Severe':
            risk = 'High'
            conf_val = 88.0
        elif inflammation == 'Moderate' or anxiety == 'High':
            risk = 'Moderate'
            conf_val = 82.0
        else:
            risk = 'Low'
            conf_val = 90.0

        result = (
            f"RISK LEVEL: {risk}\n"
            f"CONFIDENCE: {conf_val}%\n"
            f"KEY FACTORS: Infection: {infection}, Inflammation: {inflammation}, Anxiety: {anxiety}, Prior Failure: {history}\n"
            f"RECOMMENDATIONS FOR DENTIST: "
            f"{'Consider nerve block buffering, supplemental infiltration, or alternative local anesthetics due to tissue inflammation/infection.' if risk != 'Low' else 'Proceed with standard local anesthesia technique.'}"
        )

        pred = AnesthesiaPrediction(
            patient_id=int(data['patient_id']),
            patient_name=data.get('patient_name', ''),
            region=data.get('region', ''),
            infection=infection,
            inflammation=inflammation,
            anxiety=anxiety,
            history=history,
            medical_conditions=data.get('medical_conditions', ''),
            medications=data.get('medications', ''),
            risk_level=risk,
            confidence=conf_val,
            result=result,
        )

        db.session.add(pred)
        db.session.commit()

        return jsonify({
            'message': 'Prediction saved',
            'result': result,
            'risk_level': risk,
            'anesthesia': anesthesia_to_json(pred)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/anesthesia/patient/<int:user_id>', methods=['GET'])
def get_patient_anesthesia(user_id):
    try:
        rows = AnesthesiaPrediction.query.filter_by(patient_id=user_id)\
            .order_by(AnesthesiaPrediction.created_at.desc()).all()
        return jsonify([anesthesia_to_json(a) for a in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# APPOINTMENTS
# ─────────────────────────────────────────

@app.route('/appointments', methods=['POST'])
def add_appointment():
    try:
        data = request.get_json()
        required = ['patient_id', 'dentist_name', 'date', 'time']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        appt = Appointment(
            patient_id=int(data['patient_id']),
            patient_name=data.get('patient_name', ''),
            dentist_id=data.get('dentist_id'),
            dentist_name=data['dentist_name'],
            date=data['date'],
            time=data['time'],
        )
        db.session.add(appt)
        db.session.commit()
        return jsonify({'message': 'Appointment booked',
                        'appointment': appointment_to_json(appt)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/appointments/patient/<int:user_id>', methods=['GET'])
def get_patient_appointments(user_id):
    try:
        rows = Appointment.query.filter_by(patient_id=user_id)\
            .order_by(Appointment.created_at.desc()).all()
        return jsonify([appointment_to_json(a) for a in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/appointments/dentist/<int:dentist_id>', methods=['GET'])
def get_dentist_appointments(dentist_id):
    try:
        rows = Appointment.query.filter_by(dentist_id=dentist_id)\
            .order_by(Appointment.created_at.desc()).all()
        return jsonify([appointment_to_json(a) for a in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/appointments', methods=['GET'])
def get_all_appointments():
    try:
        rows = Appointment.query.order_by(Appointment.created_at.desc()).all()
        return jsonify([appointment_to_json(a) for a in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/appointments/<int:appt_id>/status', methods=['POST'])
def update_appointment_status(appt_id):
    try:
        data = request.get_json()
        appt = Appointment.query.get(appt_id)
        if not appt:
            return jsonify({'error': 'Appointment not found'}), 404
        status = data.get('status')
        if status not in ('Pending', 'Confirmed', 'Declined'):
            return jsonify({'error': 'Invalid status'}), 400
        appt.status = status
        db.session.commit()
        return jsonify({'message': 'Status updated',
                        'appointment': appointment_to_json(appt)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# CONSULTATIONS
# ─────────────────────────────────────────

@app.route('/consultations', methods=['POST'])
def add_consultation():
    try:
        data = request.get_json()
        required = ['patient_id', 'message']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        c = Consultation(
            patient_id=int(data['patient_id']),
            patient_name=data.get('patient_name', ''),
            dentist_id=data.get('dentist_id'),
            message=data['message'],
        )
        db.session.add(c)
        db.session.commit()
        return jsonify({'message': 'Consultation sent',
                        'consultation': consultation_to_json(c)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/consultations/patient/<int:user_id>', methods=['GET'])
def get_patient_consultations(user_id):
    try:
        rows = Consultation.query.filter_by(patient_id=user_id)\
            .order_by(Consultation.created_at.desc()).all()
        return jsonify([consultation_to_json(c) for c in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/consultations', methods=['GET'])
def get_all_consultations():
    try:
        status = request.args.get('status')
        q = Consultation.query
        if status:
            q = q.filter_by(status=status)
        rows = q.order_by(Consultation.created_at.desc()).all()
        return jsonify([consultation_to_json(c) for c in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/consultations/<int:consult_id>/reply', methods=['POST'])
def reply_consultation(consult_id):
    try:
        data = request.get_json()
        c = Consultation.query.get(consult_id)
        if not c:
            return jsonify({'error': 'Consultation not found'}), 404
        c.dentist_id = data.get('dentist_id')
        c.reply      = data.get('reply', '')
        c.status     = 'Replied'
        db.session.commit()
        return jsonify({'message': 'Reply sent',
                        'consultation': consultation_to_json(c)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# DENTIST VIEWS
# ─────────────────────────────────────────

@app.route('/dentist/patients', methods=['GET'])
def dentist_patients():
    try:
        patients = User.query.filter_by(role='patient')\
            .order_by(User.created_at.desc()).all()
        result = []
        for p in patients:
            latest_scan = Scan.query.filter_by(patient_id=p.id)\
                .order_by(Scan.created_at.desc()).first()
            latest_pain = PainAssessment.query.filter_by(patient_id=p.id)\
                .order_by(PainAssessment.created_at.desc()).first()
            latest_anes = AnesthesiaPrediction.query.filter_by(patient_id=p.id)\
                .order_by(AnesthesiaPrediction.created_at.desc()).first()

            is_high_risk = False
            if latest_scan and latest_scan.severity == 'Severe':
                is_high_risk = True
            elif latest_anes and latest_anes.risk_level == 'High':
                is_high_risk = True

            result.append({
                'id': p.id,
                'name': p.name,
                'age': p.age or 0,
                'gender': p.gender or '',
                'condition': latest_scan.condition if latest_scan else 'No scans yet',
                'risk': 'High' if is_high_risk else 'Low',
                'painScore': latest_pain.score if latest_pain else 0,
                'lastVisit': latest_scan.created_at.strftime('%d %b %Y')
                             if latest_scan and latest_scan.created_at else '-',
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dentist/patient/<int:patient_id>', methods=['GET'])
def dentist_patient_detail(patient_id):
    try:
        p = User.query.get(patient_id)
        if not p or p.role != 'patient':
            return jsonify({'error': 'Patient not found'}), 404
        latest_scan = Scan.query.filter_by(patient_id=p.id)\
            .order_by(Scan.created_at.desc()).first()
        latest_pain = PainAssessment.query.filter_by(patient_id=p.id)\
            .order_by(PainAssessment.created_at.desc()).first()
        latest_anes = AnesthesiaPrediction.query.filter_by(patient_id=p.id)\
            .order_by(AnesthesiaPrediction.created_at.desc()).first()
        return jsonify({
            'id': p.id,
            'name': p.name,
            'age': p.age or 0,
            'gender': p.gender or '',
            'lastVisit': latest_scan.created_at.strftime('%d %b %Y')
                         if latest_scan and latest_scan.created_at else '-',
            'risk': latest_anes.risk_level if latest_anes else 'Low',
            'condition': latest_scan.condition if latest_scan else 'No scans yet',
            'painScore': latest_pain.score if latest_pain else 0,
            'imageUrl': latest_scan.image_url if latest_scan else '',
            'scan': (latest_scan.analysis or latest_scan.summary)
                    if latest_scan else 'No scan available.',
            'anesthesia': latest_anes.result if latest_anes else 'No prediction available.',
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────

@app.route('/users', methods=['GET'])
def get_users():
    try:
        role = request.args.get('role')
        q = User.query
        if role:
            q = q.filter_by(role=role)
        users = q.order_by(User.created_at.desc()).all()
        return jsonify([user_to_json(u) for u in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user.role == 'admin':
            return jsonify({'error': 'Cannot remove admin'}), 403
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User removed'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    try:
        return jsonify({
            'patients': User.query.filter_by(role='patient').count(),
            'dentists': User.query.filter_by(role='dentist').count(),
            'total_scans': Scan.query.count(),
            'total_reports': Scan.query.count() + PainAssessment.query.count(),
            'anesthesia_predictions': AnesthesiaPrediction.query.count(),
            'consultations': Consultation.query.count(),
            'appointments': Appointment.query.count(),
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# PATIENT HOME DASHBOARD (aggregate endpoint)
# ─────────────────────────────────────────

@app.route('/dashboard/<int:user_id>', methods=['GET'])
def get_dashboard(user_id):
    """Single endpoint the patient Home screen calls."""
    try:
        scans = Scan.query.filter_by(patient_id=user_id)\
            .order_by(Scan.created_at.desc()).all()
        latest_scan = scan_to_json(scans[0]) if scans else None
        latest_pain = PainAssessment.query.filter_by(patient_id=user_id)\
            .order_by(PainAssessment.created_at.desc()).first()
        return jsonify({
            'total_scans': len(scans),
            'reviewed': sum(1 for s in scans if s.review_status == 'Reviewed'),
            'latest_scan': latest_scan,
            'latest_pain_score': latest_pain.score if latest_pain else None,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    return render_template('login.html')

@app.route('/login-page', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'new_password' not in data:
            return jsonify({'error': 'Email and new password required'}), 400
        if len(data['new_password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'No account found with this email'}), 404
        user.password = generate_password_hash(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password reset successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)