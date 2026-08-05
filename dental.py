from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
import pymysql
from groq import Groq
import sys
import io

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
    return text.encode('utf-8', errors='replace').decode('utf-8')

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

# ── Cloudinary (oral image storage) ──
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
CORS(app)

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

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
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
    created_at     = db.Column(db.DateTime, default=datetime.now)

class ActiveSession(db.Model):
    __tablename__ = 'active_sessions'
    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email    = db.Column(db.String(255), nullable=False)
    login_at = db.Column(db.DateTime, default=datetime.now)

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
    analysis        = db.Column(db.Text, nullable=True)           # full Groq text
    summary         = db.Column(db.Text, nullable=True)
    dentist_id      = db.Column(db.Integer, nullable=True)
    dentist_name    = db.Column(db.String(255), nullable=True)
    dentist_note    = db.Column(db.Text, nullable=True)
    review_status   = db.Column(db.String(15), default='Pending')  # Pending|Reviewed
    created_at      = db.Column(db.DateTime, default=datetime.now)

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
    advice       = db.Column(db.Text, nullable=True)              # Groq advice
    created_at   = db.Column(db.DateTime, default=datetime.now)

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
    result             = db.Column(db.Text, nullable=True)        # full Groq text
    created_at         = db.Column(db.DateTime, default=datetime.now)

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
    created_at   = db.Column(db.DateTime, default=datetime.now)

class Consultation(db.Model):
    __tablename__ = 'consultations'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    dentist_id   = db.Column(db.Integer, nullable=True)
    message      = db.Column(db.Text, nullable=False)
    reply        = db.Column(db.Text, nullable=True)
    status       = db.Column(db.String(15), default='Pending')   # Pending|Replied
    created_at   = db.Column(db.DateTime, default=datetime.now)


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
        'analysis': s.analysis or '',
        'summary': s.summary or '',
        'dentist_name': s.dentist_name,
        'dentist_note': s.dentist_note,
        'review_status': s.review_status,
        'created_at': s.created_at.strftime('%d %b %Y, %I:%M %p') if s.created_at else None,
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
        'advice': p.advice or '',
        'created_at': p.created_at.strftime('%d %b %Y, %I:%M %p') if p.created_at else None,
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
        'result': a.result or '',
        'created_at': a.created_at.strftime('%d %b %Y, %I:%M %p') if a.created_at else None,
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
        'created_at': a.created_at.strftime('%d %b %Y, %I:%M %p') if a.created_at else None,
    }

def consultation_to_json(c):
    return {
        'id': c.id,
        'patient_id': c.patient_id,
        'patient_name': c.patient_name,
        'dentist_id': c.dentist_id,
        'message': c.message,
        'reply': c.reply or '',
        'status': c.status,
        'created_at': c.created_at.strftime('%d %b %Y, %I:%M %p') if c.created_at else None,
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
        # Admin accounts are not self-registered.
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

# Receives the image FILE + the result the app already computed with Groq
# (Groq runs in the frontend, not here). Uploads the image to Cloudinary
# and saves the row.
@app.route('/scans', methods=['POST'])
def add_scan():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        image = request.files['image']
        form = request.form

        patient_id = form.get('patient_id')
        patient_name = form.get('patient_name', '')

        if not patient_id:
            return jsonify({'error': 'patient_id required'}), 400

        # Read image for base64 before cloudinary consumes it
        image_bytes = image.read()
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = image.mimetype if image.mimetype else 'image/jpeg'
        
        # Reset pointer for cloudinary
        image.seek(0)

        # Upload image to Cloudinary with fallback
        try:
            upload_result = cloudinary.uploader.upload(image, folder='dentalinsight')
            image_url = upload_result['secure_url']
            print("Uploading image:", image_url)
        except Exception as e:
            print("Cloudinary upload fallback:", e)
            image_url = f"data:{mime_type};base64,{base64_image}"

        # ---------- REAL GROQ VISION AI ANALYSIS ----------
        # qwen/qwen3.6-27b is the only model on this Groq API key that
        # accepts multimodal image_url content. All other available models
        # reject image_url with "messages[0].content must be a string".
        # meta-llama/llama-4-scout-17b-16e-instruct does NOT exist on this key
        # and causes a 404 crash.
        VISION_MODEL = "qwen/qwen3.6-27b"

        prompt = f"""You are examining a dental/oral photograph. Analyze it thoroughly.

Patient's notes: {form.get('notes', 'None provided')}

Provide your analysis in this exact structure:

CONDITION DETECTED: (what dental condition you observe)
PAIN SEVERITY: (None / Mild / Moderate / Severe)
POSSIBLE DIAGNOSIS: (your clinical assessment)
OBSERVATIONS: (what is visible in the image)
AFFECTED TOOTH / REGION: (which area is affected)
CONFIDENCE SCORE: (your confidence as a percentage, e.g. 75%)
RECOMMENDED TREATMENT: (what treatment you suggest)
URGENCY: (Low / Medium / High)

Instructions:
- Analyze the image carefully and provide ALL fields above.
- Focus on visible dental features: teeth color, gum condition, alignment, decay, plaque, swelling, etc.
- Always provide your best analysis even if image quality is not perfect.
- Be specific and clinical in your observations."""

        safe_print(f"\n========== GROQ VISION REQUEST ==========")
        safe_print(f"Model       : {VISION_MODEL}")
        safe_print(f"Image MIME  : {mime_type}")
        safe_print(f"Image bytes : {len(image_bytes)}")
        safe_print(f"Patient notes: {form.get('notes', '')}")
        safe_print(f"==========================================")

        try:
            response = client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a dental imaging AI specialist. Analyze the oral/dental image provided and give a detailed clinical assessment. Always provide your best professional analysis of visible dental features."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            )
        except Exception as groq_err:
            import traceback
            safe_print(f"\n========== GROQ API ERROR ==========")
            safe_print(f"Error type : {type(groq_err).__name__}")
            safe_print(f"Error msg  : {groq_err}")
            traceback.print_exc()
            safe_print(f"=====================================")
            return jsonify({'error': f'AI analysis failed: {str(groq_err)}'}), 500

        # Guard: ensure choices exist before accessing
        if not response.choices or not response.choices[0].message.content:
            safe_print("[ERROR] Groq returned empty choices — model may have refused the request.")
            return jsonify({'error': 'AI model returned an empty response. Please try again.'}), 500

        raw_analysis = sanitize_text(response.choices[0].message.content)

        safe_print(f"\n========== RAW GROQ RESPONSE ==========")
        safe_print(raw_analysis[:500])  # print first 500 chars to avoid log flood
        safe_print(f"==========================================")

        import re
        # Strip <think>...</think> reasoning blocks if the model emits them
        if '</think>' in raw_analysis:
            analysis = raw_analysis.split('</think>')[-1].strip()
        else:
            analysis = re.sub(r'<think>.*?</think>', '', raw_analysis, flags=re.DOTALL | re.IGNORECASE).strip()

        # If analysis is empty after stripping thinking tags, use raw text
        if not analysis:
            analysis = raw_analysis.strip()

        analysis = sanitize_text(analysis)

        safe_print("\n========== REAL AI VISION RESULT ==========")
        safe_print(analysis)
        safe_print("============================================")

        severity = "Mild"
        condition = "Dental Condition Detected"

        for line in analysis.split('\n'):
            line_str = line.strip()
            if line_str.upper().startswith("CONDITION DETECTED:"):
                cond_val = line_str.split(":", 1)[1].strip()
                if cond_val:
                    condition = sanitize_text(cond_val)
            if line_str.upper().startswith("PAIN SEVERITY:") or line_str.upper().startswith("SEVERITY:"):
                sev_val = line_str.split(":", 1)[1].strip()
                if "SEVERE" in sev_val.upper():
                    severity = "Severe"
                elif "MODERATE" in sev_val.upper():
                    severity = "Moderate"
                elif "NONE" in sev_val.upper():
                    severity = "None"
                else:
                    severity = "Mild"

        new_scan = Scan(
            patient_id=int(patient_id),
            patient_name=patient_name,
            image_url=image_url,
            notes=sanitize_text(form.get('notes', '')),
            condition=condition,
            severity=severity,
            findings='[]',
            recommendations='[]',
            analysis=analysis,
            summary=analysis[:200]
        )
        db.session.add(new_scan)
        
        # Save consultation automatically
        new_consult = Consultation(
            patient_id=int(patient_id),
            patient_name=patient_name,
            message=f"AI Scan Analysis:\nSeverity: {severity}\n\nNotes: {form.get('notes', '')}\nAnalysis: {analysis}",
            status='Pending'
        )
        db.session.add(new_consult)
        
        db.session.commit()

        return jsonify({
            "message": "Scan saved",
            "analysis": analysis,
            "scan": scan_to_json(new_scan)
        }), 201

    except Exception as e:
        db.session.rollback()

        safe_print("\n========== ERROR ==========")
        safe_print(type(e))
        safe_print(str(e))
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
        print("========== ERROR ==========")
        print(e)
        print("===========================")
        return jsonify({'error': str(e)}), 500
# Dentist / admin: all scans, optional ?status=Pending or ?status=Reviewed
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

# Dentist submits a review / recommendation on a scan
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

        symptoms = f"""
Trigger: {data.get('trigger', '')}
Swelling: {data.get('swelling', False)}
Sensitivity: {data.get('sensitivity', False)}
Bleeding: {data.get('bleeding', False)}
"""

        prompt = f"""
A patient has a dental pain score of {score}/100.

Symptoms:
{symptoms}

Give:
1. What this pain level means.
2. Whether urgent dental care is needed.
3. Safe home-care advice.

Keep the answer under 120 words.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly dental assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        advice = sanitize_text(response.choices[0].message.content)

        pain = PainAssessment(
            patient_id=int(data['patient_id']),
            patient_name=data.get('patient_name', ''),
            intensity=int(data.get('intensity', 0)),
            duration=data.get('duration', ''),
            trigger=data.get('trigger', ''),
            swelling=bool(data.get('swelling', False)),
            sensitivity=bool(data.get('sensitivity', False)),
            bleeding=bool(data.get('bleeding', False)),
            score=score,
            severity=data.get('severity', 'Mild'),
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

        prompt = f"""
Assess the likelihood of LOCAL ANESTHESIA FAILURE.

Patient details:
- Age: {data.get('age')}
- Gender: {data.get('gender')}
- Tooth/Region: {data.get('region')}
- Existing infection: {data.get('infection')}
- Inflammation: {data.get('inflammation')}
- Anxiety: {data.get('anxiety')}
- Previous anesthesia failure: {data.get('history')}
- Medical conditions: {data.get('medical_conditions')}
- Current medications: {data.get('medications')}

Return exactly:

RISK LEVEL:
CONFIDENCE:
KEY FACTORS:
RECOMMENDATIONS FOR DENTIST:
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical decision-support assistant for dentists."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = sanitize_text(response.choices[0].message.content)

        if "High" in result:
            risk = "High"
        elif "Moderate" in result:
            risk = "Moderate"
        else:
            risk = "Low"

        pred = AnesthesiaPrediction(
            patient_id=int(data['patient_id']),
            patient_name=data.get('patient_name', ''),
            region=data.get('region', ''),
            infection=data.get('infection', 'No'),
            inflammation=data.get('inflammation', 'Mild'),
            anxiety=data.get('anxiety', 'Low'),
            history=data.get('history', 'No'),
            medical_conditions=data.get('medical_conditions', ''),
            medications=data.get('medications', ''),
            risk_level=risk,
            confidence=0,
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

# Dentist / admin: all appointments
@app.route('/appointments', methods=['GET'])
def get_all_appointments():
    try:
        rows = Appointment.query.order_by(Appointment.created_at.desc()).all()
        return jsonify([appointment_to_json(a) for a in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dentist confirms / declines: {status: "Confirmed"|"Declined"}
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

# Dentist / admin: all consultations, optional ?status=Pending
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

# Dentist replies: {dentist_id, reply}
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

# Patient list for the dentist — one summarised row per patient.
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

# Full patient detail for the dentist — matches patient_detail.dart keys.
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
        role = request.args.get('role')   # optional: patient | dentist
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
    return jsonify({'status': 'Dental Insight API running'}), 200

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)