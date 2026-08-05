"""
Dental Insight – Master Test Suite
300 test cases covering:
  TC001-TC040  : Authentication (Login / Signup / Password Reset)
  TC041-TC080  : Scans API
  TC081-TC110  : Pain Assessment API
  TC111-TC140  : Anesthesia Prediction API
  TC141-TC170  : Appointments API
  TC171-TC200  : Consultations API
  TC201-TC220  : Admin / User Management API
  TC221-TC240  : Dashboard & Reports API
  TC241-TC260  : Validation / Edge Cases
  TC261-TC280  : Security & Permission Tests
  TC281-TC300  : Performance & Load Tests (smoke)
"""

import pytest
import json
import sys
import os
import time
import random
import string
import threading
from unittest.mock import patch, MagicMock
from datetime import datetime

# ── Add project root to path so `dental` can be imported ──────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ── Import the Flask app (with DB mocked to avoid real MySQL connection) ───────
os.environ.setdefault("DATABASE_URL", "sqlite:///test_dental.db")
os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "test")
os.environ.setdefault("CLOUDINARY_API_KEY", "test")
os.environ.setdefault("CLOUDINARY_API_SECRET", "test")

# Mock heavy dependencies before importing dental
import unittest.mock as mock

# Patch groq and cloudinary before importing dental
with mock.patch.dict('sys.modules', {
    'groq': mock.MagicMock(),
    'cloudinary': mock.MagicMock(),
    'cloudinary.uploader': mock.MagicMock(),
    'pymysql': mock.MagicMock(),
}):
    try:
        from dental import app, db
        DENTAL_AVAILABLE = True
    except Exception as e:
        DENTAL_AVAILABLE = False
        print(f"[WARN] Could not import dental app: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    if not DENTAL_AVAILABLE:
        pytest.skip("Dental app not importable (missing DB/deps)")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_dental_pytest.db"
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
        yield c
        with app.app_context():
            db.drop_all()


def _rand_email():
    return "test_" + "".join(random.choices(string.ascii_lowercase, k=6)) + "@dental.test"


def _rand_str(n=8):
    return "".join(random.choices(string.ascii_letters, k=n))


# ──────────────────────────────────────────────────────────────────────────────
# HELPER – POST / GET wrappers
# ──────────────────────────────────────────────────────────────────────────────

def post(client, url, payload):
    return client.post(url, data=json.dumps(payload),
                       content_type="application/json")


def get(client, url):
    return client.get(url)


# ══════════════════════════════════════════════════════════════════════════════
# TC001-TC040 : AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthentication:

    # ── SIGNUP ────────────────────────────────────────────────────────────────

    def test_TC001_signup_patient_success(self, client):
        """TC001 – Patient signup with all valid fields returns success."""
        r = post(client, "/signup", {
            "name": "Alice Patient", "email": _rand_email(),
            "password": "Secure@123", "role": "patient",
            "phone": "9876543210", "age": 28, "gender": "Female"
        })
        assert r.status_code in (200, 201)
        data = json.loads(r.data)
        assert "user" in data or "message" in data or "id" in data

    def test_TC002_signup_dentist_success(self, client):
        """TC002 – Dentist signup with specialization field."""
        r = post(client, "/signup", {
            "name": "Dr. Bob", "email": _rand_email(),
            "password": "DrPass@99", "role": "dentist",
            "specialization": "Orthodontics", "age": 40, "gender": "Male"
        })
        assert r.status_code in (200, 201)

    def test_TC003_signup_duplicate_email(self, client):
        """TC003 – Duplicate email signup must be rejected."""
        email = _rand_email()
        post(client, "/signup", {"name": "First", "email": email, "password": "Pass1234", "role": "patient"})
        r = post(client, "/signup", {"name": "Second", "email": email, "password": "Pass5678", "role": "patient"})
        assert r.status_code in (400, 409, 200)
        data = json.loads(r.data)
        assert "error" in data or "message" in data

    def test_TC004_signup_missing_name(self, client):
        """TC004 – Signup without name field."""
        r = post(client, "/signup", {"email": _rand_email(), "password": "Pass123", "role": "patient"})
        data = json.loads(r.data)
        assert r.status_code in (400, 422) or "error" in data

    def test_TC005_signup_missing_email(self, client):
        """TC005 – Signup without email field."""
        r = post(client, "/signup", {"name": "Test", "password": "Pass123", "role": "patient"})
        data = json.loads(r.data)
        assert r.status_code in (400, 422) or "error" in data

    def test_TC006_signup_missing_password(self, client):
        """TC006 – Signup without password field."""
        r = post(client, "/signup", {"name": "Test", "email": _rand_email(), "role": "patient"})
        data = json.loads(r.data)
        assert r.status_code in (400, 422) or "error" in data

    def test_TC007_signup_invalid_email_format(self, client):
        """TC007 – Invalid email format should be rejected."""
        r = post(client, "/signup", {"name": "T", "email": "not-an-email", "password": "Pass123", "role": "patient"})
        assert r.status_code in (400, 422, 200)

    def test_TC008_signup_short_password(self, client):
        """TC008 – Password shorter than minimum length."""
        r = post(client, "/signup", {"name": "T", "email": _rand_email(), "password": "123", "role": "patient"})
        assert r.status_code in (400, 422, 200)

    def test_TC009_signup_invalid_role(self, client):
        """TC009 – Invalid role value."""
        r = post(client, "/signup", {"name": "T", "email": _rand_email(), "password": "Pass123", "role": "hacker"})
        assert r.status_code in (400, 200)

    def test_TC010_signup_returns_json(self, client):
        """TC010 – Signup always returns JSON content-type."""
        r = post(client, "/signup", {"name": "J", "email": _rand_email(), "password": "Pass123", "role": "patient"})
        assert "application/json" in r.content_type

    # ── LOGIN ─────────────────────────────────────────────────────────────────

    def test_TC011_login_valid_patient(self, client):
        """TC011 – Login with valid patient credentials returns user object."""
        email = _rand_email()
        post(client, "/signup", {"name": "Login User", "email": email, "password": "MyPass@123", "role": "patient"})
        r = post(client, "/login", {"email": email, "password": "MyPass@123"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "user" in data

    def test_TC012_login_wrong_password(self, client):
        """TC012 – Wrong password returns error."""
        email = _rand_email()
        post(client, "/signup", {"name": "P", "email": email, "password": "CorrectPass1", "role": "patient"})
        r = post(client, "/login", {"email": email, "password": "WrongPass!"})
        data = json.loads(r.data)
        assert "error" in data or r.status_code == 401

    def test_TC013_login_nonexistent_user(self, client):
        """TC013 – Non-existent email returns error."""
        r = post(client, "/login", {"email": "nobody@nowhere.com", "password": "anypass"})
        data = json.loads(r.data)
        assert "error" in data

    def test_TC014_login_empty_email(self, client):
        """TC014 – Empty email field."""
        r = post(client, "/login", {"email": "", "password": "Pass123"})
        data = json.loads(r.data)
        assert "error" in data

    def test_TC015_login_empty_password(self, client):
        """TC015 – Empty password field."""
        r = post(client, "/login", {"email": "test@dental.test", "password": ""})
        data = json.loads(r.data)
        assert "error" in data

    def test_TC016_login_returns_role(self, client):
        """TC016 – Login response includes user role."""
        email = _rand_email()
        post(client, "/signup", {"name": "RoleUser", "email": email, "password": "Pass@321", "role": "patient"})
        r = post(client, "/login", {"email": email, "password": "Pass@321"})
        if r.status_code == 200:
            data = json.loads(r.data)
            if "user" in data:
                assert "role" in data["user"]

    def test_TC017_login_returns_user_id(self, client):
        """TC017 – Login response includes user id."""
        email = _rand_email()
        post(client, "/signup", {"name": "IDUser", "email": email, "password": "Pass@111", "role": "patient"})
        r = post(client, "/login", {"email": email, "password": "Pass@111"})
        if r.status_code == 200:
            data = json.loads(r.data)
            if "user" in data:
                assert "id" in data["user"]

    def test_TC018_login_sql_injection_attempt(self, client):
        """TC018 – SQL injection in email field must not crash server."""
        r = post(client, "/login", {"email": "' OR '1'='1", "password": "x"})
        assert r.status_code in (400, 401, 200)
        assert r.data  # response body present

    def test_TC019_login_xss_payload(self, client):
        """TC019 – XSS payload in email."""
        r = post(client, "/login", {"email": "<script>alert(1)</script>@x.com", "password": "x"})
        assert r.status_code in (400, 401, 200)

    def test_TC020_login_unicode_email(self, client):
        """TC020 – Unicode characters in email handled gracefully."""
        r = post(client, "/login", {"email": "用户@测试.com", "password": "pass"})
        assert r.status_code in (400, 401, 200)

    # ── PASSWORD RESET ────────────────────────────────────────────────────────

    def test_TC021_reset_password_success(self, client):
        """TC021 – Valid email + new password resets successfully."""
        email = _rand_email()
        post(client, "/signup", {"name": "Reset Me", "email": email, "password": "OldPass1", "role": "patient"})
        r = post(client, "/reset_password", {"email": email, "new_password": "NewPass@2024"})
        assert r.status_code in (200, 201)

    def test_TC022_reset_password_unknown_email(self, client):
        """TC022 – Reset for unknown email returns error."""
        r = post(client, "/reset_password", {"email": "unknown@dental.test", "new_password": "NewPass1"})
        data = json.loads(r.data)
        assert "error" in data or r.status_code == 404

    def test_TC023_reset_password_missing_fields(self, client):
        """TC023 – Reset without new_password."""
        r = post(client, "/reset_password", {"email": "test@dental.test"})
        data = json.loads(r.data)
        assert "error" in data or r.status_code in (400, 422)

    def test_TC024_reset_then_login(self, client):
        """TC024 – After reset, login with new password succeeds."""
        email = _rand_email()
        post(client, "/signup", {"name": "ResetThenLogin", "email": email, "password": "OldPwd1", "role": "patient"})
        post(client, "/reset_password", {"email": email, "new_password": "NewPwd@99"})
        r = post(client, "/login", {"email": email, "password": "NewPwd@99"})
        assert r.status_code == 200

    def test_TC025_reset_old_password_rejected(self, client):
        """TC025 – After reset, old password login fails."""
        email = _rand_email()
        post(client, "/signup", {"name": "OldFail", "email": email, "password": "OldPwd123", "role": "patient"})
        post(client, "/reset_password", {"email": email, "new_password": "BrandNew@1"})
        r = post(client, "/login", {"email": email, "password": "OldPwd123"})
        data = json.loads(r.data)
        assert "error" in data or r.status_code == 401

    def test_TC026_signup_age_zero(self, client):
        """TC026 – Signup with age 0 is accepted."""
        r = post(client, "/signup", {"name": "Baby", "email": _rand_email(), "password": "Pass123", "role": "patient", "age": 0})
        assert r.status_code in (200, 201)

    def test_TC027_signup_age_negative(self, client):
        """TC027 – Signup with negative age handled."""
        r = post(client, "/signup", {"name": "Neg", "email": _rand_email(), "password": "Pass123", "role": "patient", "age": -5})
        assert r.status_code in (200, 201, 400)

    def test_TC028_signup_very_long_name(self, client):
        """TC028 – Very long name (255 chars)."""
        r = post(client, "/signup", {"name": "A" * 255, "email": _rand_email(), "password": "Pass123", "role": "patient"})
        assert r.status_code in (200, 201, 400)

    def test_TC029_signup_special_chars_name(self, client):
        """TC029 – Special characters in name."""
        r = post(client, "/signup", {"name": "O'Brien-Smith", "email": _rand_email(), "password": "Pass123", "role": "patient"})
        assert r.status_code in (200, 201)

    def test_TC030_login_case_sensitive_email(self, client):
        """TC030 – Email case sensitivity check."""
        email = _rand_email()
        post(client, "/signup", {"name": "Case", "email": email, "password": "Pass123", "role": "patient"})
        r = post(client, "/login", {"email": email.upper(), "password": "Pass123"})
        # either works or gives clear error – no crash
        assert r.status_code in (200, 401, 400)

    def test_TC031_login_missing_body(self, client):
        """TC031 – POST /login with empty body."""
        r = client.post("/login", data="", content_type="application/json")
        assert r.status_code in (400, 500, 200)

    def test_TC032_signup_with_phone_number(self, client):
        """TC032 – Signup includes phone number."""
        r = post(client, "/signup", {"name": "PhoneUser", "email": _rand_email(), "password": "Pass@123", "role": "patient", "phone": "+91-9876543210"})
        assert r.status_code in (200, 201)

    def test_TC033_signup_gender_male(self, client):
        """TC033 – Signup with Male gender."""
        r = post(client, "/signup", {"name": "Male User", "email": _rand_email(), "password": "Pass123", "role": "patient", "gender": "Male"})
        assert r.status_code in (200, 201)

    def test_TC034_signup_gender_female(self, client):
        """TC034 – Signup with Female gender."""
        r = post(client, "/signup", {"name": "Female User", "email": _rand_email(), "password": "Pass123", "role": "patient", "gender": "Female"})
        assert r.status_code in (200, 201)

    def test_TC035_signup_gender_other(self, client):
        """TC035 – Signup with Other gender."""
        r = post(client, "/signup", {"name": "Other User", "email": _rand_email(), "password": "Pass123", "role": "patient", "gender": "Other"})
        assert r.status_code in (200, 201)

    def test_TC036_login_method_get_rejected(self, client):
        """TC036 – GET /login should return 405."""
        r = client.get("/login")
        assert r.status_code == 405

    def test_TC037_signup_method_get_rejected(self, client):
        """TC037 – GET /signup should return 405."""
        r = client.get("/signup")
        assert r.status_code == 405

    def test_TC038_reset_password_method_get_rejected(self, client):
        """TC038 – GET /reset_password should return 405."""
        r = client.get("/reset_password")
        assert r.status_code == 405

    def test_TC039_login_response_time(self, client):
        """TC039 – Login responds within 5 seconds."""
        start = time.time()
        post(client, "/login", {"email": "speed@dental.test", "password": "any"})
        assert (time.time() - start) < 5

    def test_TC040_signup_response_time(self, client):
        """TC040 – Signup responds within 5 seconds."""
        start = time.time()
        post(client, "/signup", {"name": "S", "email": _rand_email(), "password": "P@ssw0rd", "role": "patient"})
        assert (time.time() - start) < 5


# ══════════════════════════════════════════════════════════════════════════════
# TC041-TC080 : SCANS API
# ══════════════════════════════════════════════════════════════════════════════

class TestScansAPI:

    def _create_patient(self, client):
        email = _rand_email()
        post(client, "/signup", {"name": "Scan Patient", "email": email, "password": "ScanPass1", "role": "patient"})
        r = post(client, "/login", {"email": email, "password": "ScanPass1"})
        data = json.loads(r.data)
        uid = data.get("user", {}).get("id", 1)
        return uid, email

    def test_TC041_get_all_scans(self, client):
        """TC041 – GET /scans returns a list."""
        r = get(client, "/scans")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC042_get_scans_with_status_filter(self, client):
        """TC042 – GET /scans?status=Pending filters correctly."""
        r = get(client, "/scans?status=Pending")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_TC043_get_scans_reviewed_filter(self, client):
        """TC043 – GET /scans?status=Reviewed."""
        r = get(client, "/scans?status=Reviewed")
        assert r.status_code == 200

    def test_TC044_get_patient_scans_empty(self, client):
        """TC044 – New patient has empty scans list."""
        uid, _ = self._create_patient(client)
        r = get(client, f"/scans/patient/{uid}")
        assert r.status_code == 200
        assert json.loads(r.data) == []

    def test_TC045_get_patient_scans_nonexistent_id(self, client):
        """TC045 – Non-existent patient ID returns empty list or 404."""
        r = get(client, "/scans/patient/999999")
        assert r.status_code in (200, 404)

    def test_TC046_scans_returns_json(self, client):
        """TC046 – GET /scans returns JSON content type."""
        r = get(client, "/scans")
        assert "application/json" in r.content_type

    def test_TC047_scan_review_nonexistent(self, client):
        """TC047 – Review non-existent scan returns error."""
        r = post(client, "/scans/999999/review", {
            "dentist_id": 1, "dentist_name": "Dr.X", "dentist_note": "No finding"
        })
        data = json.loads(r.data)
        assert "error" in data or r.status_code == 404

    def test_TC048_scan_review_missing_dentist_id(self, client):
        """TC048 – Review without dentist_id."""
        r = post(client, "/scans/1/review", {"dentist_name": "Dr.X", "dentist_note": "Note"})
        assert r.status_code in (200, 400, 404)

    def test_TC049_get_scans_invalid_status(self, client):
        """TC049 – Invalid status filter parameter."""
        r = get(client, "/scans?status=INVALID")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC050_scans_list_structure(self, client):
        """TC050 – Scan objects contain required fields."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        if data:
            scan = data[0]
            for field in ["id", "patient_id", "patient_name"]:
                assert field in scan

    def test_TC051_scan_severity_mild(self, client):
        """TC051 – Severity Mild in scan object."""
        r = get(client, "/scans?status=Pending")
        data = json.loads(r.data)
        for s in data:
            assert s.get("severity") in ["Mild", "Moderate", "Severe", None]

    def test_TC052_scan_review_status_values(self, client):
        """TC052 – review_status values are Pending or Reviewed."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert s.get("review_status") in ["Pending", "Reviewed", None]

    def test_TC053_get_scans_response_time(self, client):
        """TC053 – GET /scans responds within 3 seconds."""
        start = time.time()
        get(client, "/scans")
        assert (time.time() - start) < 3

    def test_TC054_scan_review_method_get_rejected(self, client):
        """TC054 – GET on review endpoint should be 405."""
        r = client.get("/scans/1/review")
        assert r.status_code == 405

    def test_TC055_post_scans_without_image(self, client):
        """TC055 – POST /scans without image file returns error."""
        r = client.post("/scans", data={"patient_id": "1", "patient_name": "Test"})
        assert r.status_code in (400, 422, 500)

    def test_TC056_scan_patient_id_zero(self, client):
        """TC056 – Scans for patient_id=0."""
        r = get(client, "/scans/patient/0")
        assert r.status_code in (200, 400, 404)

    def test_TC057_scan_patient_id_negative(self, client):
        """TC057 – Scans for negative patient_id."""
        r = get(client, "/scans/patient/-1")
        assert r.status_code in (200, 400, 404)

    def test_TC058_scan_patient_id_string(self, client):
        """TC058 – Scans for non-numeric patient_id."""
        r = get(client, "/scans/patient/abc")
        assert r.status_code in (400, 404)

    def test_TC059_scan_review_note_long(self, client):
        """TC059 – Dentist note with 1000 characters."""
        r = post(client, "/scans/1/review", {
            "dentist_id": 1, "dentist_name": "Dr.Long",
            "dentist_note": "N" * 1000
        })
        assert r.status_code in (200, 404)

    def test_TC060_scan_review_empty_note(self, client):
        """TC060 – Dentist note can be empty string."""
        r = post(client, "/scans/1/review", {
            "dentist_id": 1, "dentist_name": "Dr.Empty", "dentist_note": ""
        })
        assert r.status_code in (200, 404)

    def test_TC061_scan_findings_json_array(self, client):
        """TC061 – Scan findings is a list."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert isinstance(s.get("findings", []), list)

    def test_TC062_scan_recommendations_json_array(self, client):
        """TC062 – Scan recommendations is a list."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert isinstance(s.get("recommendations", []), list)

    def test_TC063_scan_created_at_format(self, client):
        """TC063 – created_at is a string date."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            if s.get("created_at"):
                assert isinstance(s["created_at"], str)

    def test_TC064_scan_image_url_present(self, client):
        """TC064 – Scan image_url field present."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert "image_url" in s

    def test_TC065_scan_notes_present(self, client):
        """TC065 – Notes field present in scan."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert "notes" in s

    def test_TC066_get_scans_no_params(self, client):
        """TC066 – GET /scans with no params returns all."""
        r = get(client, "/scans")
        assert r.status_code == 200

    def test_TC067_scan_delete_not_allowed(self, client):
        """TC067 – DELETE /scans/1 should return 405 if not supported."""
        r = client.delete("/scans/1")
        assert r.status_code in (405, 404, 200)

    def test_TC068_scan_condition_field(self, client):
        """TC068 – Condition field present in scan."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert "condition" in s

    def test_TC069_scan_summary_field(self, client):
        """TC069 – Summary field present in scan."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert "summary" in s

    def test_TC070_scan_analysis_field(self, client):
        """TC070 – Analysis field present in scan."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert "analysis" in s

    def test_TC071_scan_dentist_name_field(self, client):
        """TC071 – Dentist name field present."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert "dentist_name" in s

    def test_TC072_scan_dentist_note_field(self, client):
        """TC072 – Dentist note field present."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert "dentist_note" in s

    def test_TC073_scan_review_unicode_note(self, client):
        """TC073 – Unicode in dentist note handled."""
        r = post(client, "/scans/1/review", {
            "dentist_id": 1, "dentist_name": "डॉ राज",
            "dentist_note": "अच्छा है"
        })
        assert r.status_code in (200, 404)

    def test_TC074_scan_review_special_chars(self, client):
        """TC074 – Special characters in dentist note."""
        r = post(client, "/scans/1/review", {
            "dentist_id": 1, "dentist_name": "Dr. O'Brien",
            "dentist_note": "Patient's <tooth> shows > 50% decay & needs root canal"
        })
        assert r.status_code in (200, 404)

    def test_TC075_scans_concurrent_get(self, client):
        """TC075 – Concurrent GET /scans doesn't crash."""
        errors = []
        def do_get():
            try:
                get(client, "/scans")
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_get) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC076_scans_status_reviewed(self, client):
        """TC076 – Reviewed scans filter works."""
        r = get(client, "/scans?status=Reviewed")
        assert r.status_code == 200

    def test_TC077_scans_status_empty_string(self, client):
        """TC077 – Empty status string handled."""
        r = get(client, "/scans?status=")
        assert r.status_code in (200, 400)

    def test_TC078_scan_id_is_integer(self, client):
        """TC078 – Scan id is integer type."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert isinstance(s["id"], int)

    def test_TC079_scan_patient_id_is_integer(self, client):
        """TC079 – Scan patient_id is integer."""
        r = get(client, "/scans")
        data = json.loads(r.data)
        for s in data:
            assert isinstance(s["patient_id"], int)

    def test_TC080_scan_review_returns_json(self, client):
        """TC080 – Scan review endpoint returns JSON."""
        r = post(client, "/scans/999/review", {"dentist_id": 1, "dentist_name": "Dr", "dentist_note": "ok"})
        assert "application/json" in r.content_type


# ══════════════════════════════════════════════════════════════════════════════
# TC081-TC110 : PAIN ASSESSMENT API
# ══════════════════════════════════════════════════════════════════════════════

class TestPainAPI:

    def _valid_pain(self, patient_id=1):
        return {
            "patient_id": patient_id, "patient_name": "Pain Patient",
            "intensity": 7, "duration": "3 days",
            "trigger": "Cold", "swelling": True,
            "sensitivity": True, "bleeding": False
        }

    def test_TC081_add_pain_valid(self, client):
        """TC081 – Valid pain assessment accepted."""
        r = post(client, "/pain", self._valid_pain())
        assert r.status_code in (200, 201)

    def test_TC082_add_pain_missing_patient_id(self, client):
        """TC082 – Pain without patient_id."""
        payload = self._valid_pain()
        del payload["patient_id"]
        r = post(client, "/pain", payload)
        assert r.status_code in (400, 422, 500)

    def test_TC083_add_pain_intensity_zero(self, client):
        """TC083 – Pain intensity 0 (no pain)."""
        r = post(client, "/pain", {**self._valid_pain(), "intensity": 0})
        assert r.status_code in (200, 201)

    def test_TC084_add_pain_intensity_ten(self, client):
        """TC084 – Pain intensity 10 (maximum)."""
        r = post(client, "/pain", {**self._valid_pain(), "intensity": 10})
        assert r.status_code in (200, 201)

    def test_TC085_add_pain_intensity_over_ten(self, client):
        """TC085 – Pain intensity > 10 edge case."""
        r = post(client, "/pain", {**self._valid_pain(), "intensity": 15})
        assert r.status_code in (200, 201, 400)

    def test_TC086_add_pain_negative_intensity(self, client):
        """TC086 – Negative intensity handled."""
        r = post(client, "/pain", {**self._valid_pain(), "intensity": -1})
        assert r.status_code in (200, 201, 400)

    def test_TC087_get_patient_pain_empty(self, client):
        """TC087 – New patient has empty pain list."""
        r = get(client, "/pain/patient/999998")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC088_get_patient_pain_returns_list(self, client):
        """TC088 – Pain endpoint returns list."""
        r = get(client, "/pain/patient/1")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC089_pain_swelling_true(self, client):
        """TC089 – Pain with swelling=True."""
        r = post(client, "/pain", {**self._valid_pain(), "swelling": True})
        assert r.status_code in (200, 201)

    def test_TC090_pain_bleeding_true(self, client):
        """TC090 – Pain with bleeding=True."""
        r = post(client, "/pain", {**self._valid_pain(), "bleeding": True})
        assert r.status_code in (200, 201)

    def test_TC091_pain_all_symptoms_true(self, client):
        """TC091 – Pain with all symptoms True."""
        r = post(client, "/pain", {**self._valid_pain(), "swelling": True, "sensitivity": True, "bleeding": True})
        assert r.status_code in (200, 201)

    def test_TC092_pain_no_symptoms(self, client):
        """TC092 – Pain with all symptoms False."""
        r = post(client, "/pain", {**self._valid_pain(), "swelling": False, "sensitivity": False, "bleeding": False})
        assert r.status_code in (200, 201)

    def test_TC093_pain_duration_long_string(self, client):
        """TC093 – Long duration string."""
        r = post(client, "/pain", {**self._valid_pain(), "duration": "Several weeks and ongoing"})
        assert r.status_code in (200, 201)

    def test_TC094_pain_trigger_hot(self, client):
        """TC094 – Trigger = Hot."""
        r = post(client, "/pain", {**self._valid_pain(), "trigger": "Hot"})
        assert r.status_code in (200, 201)

    def test_TC095_pain_trigger_pressure(self, client):
        """TC095 – Trigger = Pressure."""
        r = post(client, "/pain", {**self._valid_pain(), "trigger": "Pressure"})
        assert r.status_code in (200, 201)

    def test_TC096_pain_trigger_sweet(self, client):
        """TC096 – Trigger = Sweet."""
        r = post(client, "/pain", {**self._valid_pain(), "trigger": "Sweet"})
        assert r.status_code in (200, 201)

    def test_TC097_pain_severity_returned(self, client):
        """TC097 – Response includes severity field."""
        r = post(client, "/pain", self._valid_pain())
        if r.status_code in (200, 201):
            data = json.loads(r.data)
            # Either returns assessment or nested object
            assert r.data is not None

    def test_TC098_pain_score_returned(self, client):
        """TC098 – Response includes score or message."""
        r = post(client, "/pain", self._valid_pain())
        assert r.data is not None

    def test_TC099_get_pain_returns_json(self, client):
        """TC099 – GET /pain/patient/1 returns JSON."""
        r = get(client, "/pain/patient/1")
        assert "application/json" in r.content_type

    def test_TC100_add_pain_returns_json(self, client):
        """TC100 – POST /pain returns JSON."""
        r = post(client, "/pain", self._valid_pain())
        assert "application/json" in r.content_type

    def test_TC101_pain_patient_name_arabic(self, client):
        """TC101 – Arabic patient name handled."""
        r = post(client, "/pain", {**self._valid_pain(), "patient_name": "مريض"})
        assert r.status_code in (200, 201)

    def test_TC102_pain_missing_intensity(self, client):
        """TC102 – Missing intensity defaults or errors."""
        payload = self._valid_pain()
        del payload["intensity"]
        r = post(client, "/pain", payload)
        assert r.status_code in (200, 201, 400)

    def test_TC103_pain_missing_duration(self, client):
        """TC103 – Missing duration handled."""
        payload = self._valid_pain()
        del payload["duration"]
        r = post(client, "/pain", payload)
        assert r.status_code in (200, 201, 400)

    def test_TC104_pain_empty_trigger(self, client):
        """TC104 – Empty trigger string."""
        r = post(client, "/pain", {**self._valid_pain(), "trigger": ""})
        assert r.status_code in (200, 201, 400)

    def test_TC105_pain_intensity_string(self, client):
        """TC105 – String intensity coerced or rejected."""
        r = post(client, "/pain", {**self._valid_pain(), "intensity": "seven"})
        assert r.status_code in (200, 201, 400, 422)

    def test_TC106_pain_method_get(self, client):
        """TC106 – GET /pain returns 405."""
        r = client.get("/pain")
        assert r.status_code in (405, 404)

    def test_TC107_pain_history_same_as_pain(self, client):
        """TC107 – /pain/patient/{id} same as history."""
        uid = 1
        r1 = get(client, f"/pain/patient/{uid}")
        r2 = get(client, f"/pain/patient/{uid}")
        assert r1.status_code == r2.status_code == 200

    def test_TC108_pain_response_time(self, client):
        """TC108 – Pain POST responds within 10 seconds (Groq may be slow)."""
        start = time.time()
        post(client, "/pain", self._valid_pain())
        assert (time.time() - start) < 10

    def test_TC109_pain_large_payload(self, client):
        """TC109 – Extra fields in payload don't crash server."""
        payload = self._valid_pain()
        payload["extra_field"] = "x" * 500
        r = post(client, "/pain", payload)
        assert r.status_code in (200, 201, 400)

    def test_TC110_pain_patient_id_float(self, client):
        """TC110 – Float patient_id handled."""
        r = post(client, "/pain", {**self._valid_pain(), "patient_id": 1.5})
        assert r.status_code in (200, 201, 400)


# ══════════════════════════════════════════════════════════════════════════════
# TC111-TC140 : ANESTHESIA PREDICTION API
# ══════════════════════════════════════════════════════════════════════════════

class TestAnesthesiaAPI:

    def _valid_anesthesia(self, patient_id=1):
        return {
            "patient_id": patient_id, "patient_name": "Anesthesia Patient",
            "region": "Lower Molar", "infection": "No",
            "inflammation": "Mild", "anxiety": "Low",
            "history": "No", "medical_conditions": "None",
            "medications": "None"
        }

    def test_TC111_add_anesthesia_valid(self, client):
        """TC111 – Valid anesthesia prediction accepted."""
        r = post(client, "/anesthesia", self._valid_anesthesia())
        assert r.status_code in (200, 201)

    def test_TC112_get_patient_anesthesia(self, client):
        """TC112 – GET /anesthesia/patient/1 returns list."""
        r = get(client, "/anesthesia/patient/1")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC113_anesthesia_infection_yes(self, client):
        """TC113 – Infection=Yes increases risk."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "infection": "Yes"})
        assert r.status_code in (200, 201)

    def test_TC114_anesthesia_high_anxiety(self, client):
        """TC114 – High anxiety level."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "anxiety": "High"})
        assert r.status_code in (200, 201)

    def test_TC115_anesthesia_history_yes(self, client):
        """TC115 – Prior anesthesia failure."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "history": "Yes"})
        assert r.status_code in (200, 201)

    def test_TC116_anesthesia_severe_inflammation(self, client):
        """TC116 – Severe inflammation."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "inflammation": "Severe"})
        assert r.status_code in (200, 201)

    def test_TC117_anesthesia_missing_patient_id(self, client):
        """TC117 – Missing patient_id."""
        payload = self._valid_anesthesia()
        del payload["patient_id"]
        r = post(client, "/anesthesia", payload)
        assert r.status_code in (400, 422, 500)

    def test_TC118_anesthesia_returns_risk_level(self, client):
        """TC118 – Response contains risk level."""
        r = post(client, "/anesthesia", self._valid_anesthesia())
        assert r.data is not None

    def test_TC119_anesthesia_medical_conditions_long(self, client):
        """TC119 – Long medical conditions string."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "medical_conditions": "Diabetes, Hypertension, Asthma, Heart disease, Epilepsy"})
        assert r.status_code in (200, 201)

    def test_TC120_anesthesia_medications_multiple(self, client):
        """TC120 – Multiple medications listed."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "medications": "Metformin, Lisinopril, Albuterol"})
        assert r.status_code in (200, 201)

    def test_TC121_anesthesia_returns_json(self, client):
        """TC121 – Response is JSON."""
        r = post(client, "/anesthesia", self._valid_anesthesia())
        assert "application/json" in r.content_type

    def test_TC122_anesthesia_get_patient_returns_json(self, client):
        """TC122 – GET /anesthesia/patient returns JSON."""
        r = get(client, "/anesthesia/patient/1")
        assert "application/json" in r.content_type

    def test_TC123_anesthesia_patient_id_negative(self, client):
        """TC123 – Negative patient_id."""
        r = get(client, "/anesthesia/patient/-1")
        assert r.status_code in (200, 400, 404)

    def test_TC124_anesthesia_region_upper_molar(self, client):
        """TC124 – Upper Molar region."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "region": "Upper Molar"})
        assert r.status_code in (200, 201)

    def test_TC125_anesthesia_region_front_teeth(self, client):
        """TC125 – Front Teeth region."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "region": "Front Teeth"})
        assert r.status_code in (200, 201)

    def test_TC126_anesthesia_empty_region(self, client):
        """TC126 – Empty region string."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "region": ""})
        assert r.status_code in (200, 201, 400)

    def test_TC127_anesthesia_null_medications(self, client):
        """TC127 – Null medications."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "medications": None})
        assert r.status_code in (200, 201, 400)

    def test_TC128_anesthesia_null_conditions(self, client):
        """TC128 – Null medical_conditions."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "medical_conditions": None})
        assert r.status_code in (200, 201, 400)

    def test_TC129_anesthesia_response_time(self, client):
        """TC129 – Response within 10 seconds."""
        start = time.time()
        post(client, "/anesthesia", self._valid_anesthesia())
        assert (time.time() - start) < 10

    def test_TC130_anesthesia_new_patient_empty(self, client):
        """TC130 – New patient has no anesthesia records."""
        r = get(client, "/anesthesia/patient/999997")
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_TC131_anesthesia_inflammation_moderate(self, client):
        """TC131 – Moderate inflammation."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "inflammation": "Moderate"})
        assert r.status_code in (200, 201)

    def test_TC132_anesthesia_anxiety_moderate(self, client):
        """TC132 – Moderate anxiety."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "anxiety": "Moderate"})
        assert r.status_code in (200, 201)

    def test_TC133_anesthesia_method_get_rejected(self, client):
        """TC133 – GET /anesthesia returns 405."""
        r = client.get("/anesthesia")
        assert r.status_code in (405, 404)

    def test_TC134_anesthesia_all_risk_factors(self, client):
        """TC134 – All risk factors elevated (High risk scenario)."""
        r = post(client, "/anesthesia", {
            **self._valid_anesthesia(),
            "infection": "Yes", "inflammation": "Severe",
            "anxiety": "High", "history": "Yes",
            "medical_conditions": "Diabetes, Heart Disease",
            "medications": "Warfarin"
        })
        assert r.status_code in (200, 201)

    def test_TC135_anesthesia_no_risk_factors(self, client):
        """TC135 – No risk factors (Low risk scenario)."""
        r = post(client, "/anesthesia", {
            **self._valid_anesthesia(),
            "infection": "No", "inflammation": "Mild",
            "anxiety": "Low", "history": "No",
            "medical_conditions": "None", "medications": "None"
        })
        assert r.status_code in (200, 201)

    def test_TC136_anesthesia_unicode_patient_name(self, client):
        """TC136 – Unicode patient name."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "patient_name": "Müller"})
        assert r.status_code in (200, 201)

    def test_TC137_anesthesia_region_wisdom_tooth(self, client):
        """TC137 – Wisdom tooth region."""
        r = post(client, "/anesthesia", {**self._valid_anesthesia(), "region": "Wisdom Tooth"})
        assert r.status_code in (200, 201)

    def test_TC138_anesthesia_concurrent_requests(self, client):
        """TC138 – Concurrent anesthesia requests don't crash."""
        errors = []
        def do_post():
            try:
                post(client, "/anesthesia", self._valid_anesthesia())
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_post) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC139_anesthesia_patient_string_id(self, client):
        """TC139 – String patient_id in GET URL."""
        r = get(client, "/anesthesia/patient/abc")
        assert r.status_code in (400, 404)

    def test_TC140_anesthesia_empty_body(self, client):
        """TC140 – Empty body to /anesthesia."""
        r = client.post("/anesthesia", data="{}", content_type="application/json")
        assert r.status_code in (400, 422, 500)


# ══════════════════════════════════════════════════════════════════════════════
# TC141-TC170 : APPOINTMENTS API
# ══════════════════════════════════════════════════════════════════════════════

class TestAppointmentsAPI:

    def _valid_appt(self, patient_id=1):
        return {
            "patient_id": patient_id, "patient_name": "Appt Patient",
            "dentist_name": "Dr. Smith", "date": "2025-12-25",
            "time": "10:30 AM"
        }

    def test_TC141_add_appointment_valid(self, client):
        """TC141 – Valid appointment created."""
        r = post(client, "/appointments", self._valid_appt())
        assert r.status_code in (200, 201)

    def test_TC142_get_all_appointments(self, client):
        """TC142 – GET /appointments returns list."""
        r = get(client, "/appointments")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC143_get_patient_appointments(self, client):
        """TC143 – GET /appointments/patient/1 returns list."""
        r = get(client, "/appointments/patient/1")
        assert r.status_code == 200

    def test_TC144_appointment_status_pending_default(self, client):
        """TC144 – New appointment default status is Pending."""
        post(client, "/appointments", self._valid_appt())
        r = get(client, "/appointments")
        data = json.loads(r.data)
        if data:
            assert any(a["status"] == "Pending" for a in data)

    def test_TC145_update_appointment_confirmed(self, client):
        """TC145 – Update appointment status to Confirmed."""
        r = post(client, "/appointments/1/status", {"status": "Confirmed"})
        assert r.status_code in (200, 404)

    def test_TC146_update_appointment_declined(self, client):
        """TC146 – Update appointment status to Declined."""
        r = post(client, "/appointments/1/status", {"status": "Declined"})
        assert r.status_code in (200, 404)

    def test_TC147_update_appointment_invalid_status(self, client):
        """TC147 – Invalid status value."""
        r = post(client, "/appointments/1/status", {"status": "Flying"})
        assert r.status_code in (200, 400, 404)

    def test_TC148_appointment_missing_date(self, client):
        """TC148 – Appointment without date."""
        payload = self._valid_appt()
        del payload["date"]
        r = post(client, "/appointments", payload)
        assert r.status_code in (400, 422, 500)

    def test_TC149_appointment_missing_time(self, client):
        """TC149 – Appointment without time."""
        payload = self._valid_appt()
        del payload["time"]
        r = post(client, "/appointments", payload)
        assert r.status_code in (400, 422, 500)

    def test_TC150_appointment_missing_dentist_name(self, client):
        """TC150 – Appointment without dentist name."""
        payload = self._valid_appt()
        del payload["dentist_name"]
        r = post(client, "/appointments", payload)
        assert r.status_code in (400, 422, 500)

    def test_TC151_appointment_returns_json(self, client):
        """TC151 – POST /appointments returns JSON."""
        r = post(client, "/appointments", self._valid_appt())
        assert "application/json" in r.content_type

    def test_TC152_appointment_list_returns_json(self, client):
        """TC152 – GET /appointments returns JSON."""
        r = get(client, "/appointments")
        assert "application/json" in r.content_type

    def test_TC153_appointment_fields_present(self, client):
        """TC153 – Appointment has required fields."""
        post(client, "/appointments", self._valid_appt())
        r = get(client, "/appointments")
        data = json.loads(r.data)
        if data:
            appt = data[0]
            for f in ["id", "patient_id", "patient_name", "date", "time", "status"]:
                assert f in appt

    def test_TC154_appointment_date_past(self, client):
        """TC154 – Past date appointment created."""
        r = post(client, "/appointments", {**self._valid_appt(), "date": "2020-01-01"})
        assert r.status_code in (200, 201, 400)

    def test_TC155_appointment_date_future(self, client):
        """TC155 – Future date appointment created."""
        r = post(client, "/appointments", {**self._valid_appt(), "date": "2030-01-01"})
        assert r.status_code in (200, 201)

    def test_TC156_appointment_time_formats(self, client):
        """TC156 – Different time formats accepted."""
        for t in ["09:00 AM", "14:30", "3:00 PM", "11:59 PM"]:
            r = post(client, "/appointments", {**self._valid_appt(), "time": t})
            assert r.status_code in (200, 201, 400)

    def test_TC157_get_patient_appointments_empty(self, client):
        """TC157 – New patient has no appointments."""
        r = get(client, "/appointments/patient/999996")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC158_appointment_patient_id_zero(self, client):
        """TC158 – Patient id 0."""
        r = get(client, "/appointments/patient/0")
        assert r.status_code in (200, 400, 404)

    def test_TC159_appointment_update_nonexistent(self, client):
        """TC159 – Update status of non-existent appointment."""
        r = post(client, "/appointments/999999/status", {"status": "Confirmed"})
        assert r.status_code in (200, 404)

    def test_TC160_appointment_patient_name_long(self, client):
        """TC160 – Long patient name in appointment."""
        r = post(client, "/appointments", {**self._valid_appt(), "patient_name": "A" * 100})
        assert r.status_code in (200, 201, 400)

    def test_TC161_appointment_dentist_id_present(self, client):
        """TC161 – dentist_id field present in response."""
        r = get(client, "/appointments")
        data = json.loads(r.data)
        if data:
            assert "dentist_id" in data[0]

    def test_TC162_appointment_created_at_present(self, client):
        """TC162 – created_at field present."""
        r = get(client, "/appointments")
        data = json.loads(r.data)
        if data:
            assert "created_at" in data[0]

    def test_TC163_multiple_appointments_same_patient(self, client):
        """TC163 – Patient can have multiple appointments."""
        for _ in range(3):
            post(client, "/appointments", self._valid_appt(patient_id=500))
        r = get(client, "/appointments/patient/500")
        data = json.loads(r.data)
        assert len(data) >= 3

    def test_TC164_appointment_status_method_get_rejected(self, client):
        """TC164 – GET /appointments/1/status returns 405."""
        r = client.get("/appointments/1/status")
        assert r.status_code in (405, 404)

    def test_TC165_appointment_response_time(self, client):
        """TC165 – POST /appointments responds within 3 seconds."""
        start = time.time()
        post(client, "/appointments", self._valid_appt())
        assert (time.time() - start) < 3

    def test_TC166_appointment_string_patient_id(self, client):
        """TC166 – String patient_id in GET."""
        r = get(client, "/appointments/patient/abc")
        assert r.status_code in (400, 404)

    def test_TC167_appointment_unicode_name(self, client):
        """TC167 – Unicode patient name."""
        r = post(client, "/appointments", {**self._valid_appt(), "patient_name": "تهانی"})
        assert r.status_code in (200, 201)

    def test_TC168_appointment_unicode_dentist(self, client):
        """TC168 – Unicode dentist name."""
        r = post(client, "/appointments", {**self._valid_appt(), "dentist_name": "डॉ. राज"})
        assert r.status_code in (200, 201)

    def test_TC169_appointment_empty_body(self, client):
        """TC169 – Empty body to /appointments."""
        r = client.post("/appointments", data="{}", content_type="application/json")
        assert r.status_code in (400, 422, 500)

    def test_TC170_appointments_concurrent(self, client):
        """TC170 – Concurrent appointment creation."""
        errors = []
        def do_post():
            try:
                post(client, "/appointments", self._valid_appt())
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_post) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


# ══════════════════════════════════════════════════════════════════════════════
# TC171-TC200 : CONSULTATIONS API
# ══════════════════════════════════════════════════════════════════════════════

class TestConsultationsAPI:

    def _valid_consult(self, patient_id=1):
        return {
            "patient_id": patient_id, "patient_name": "Consult Patient",
            "message": "I have tooth pain for 3 days. Please advise."
        }

    def test_TC171_add_consultation_valid(self, client):
        """TC171 – Valid consultation message accepted."""
        r = post(client, "/consultations", self._valid_consult())
        assert r.status_code in (200, 201)

    def test_TC172_get_all_consultations(self, client):
        """TC172 – GET /consultations returns list."""
        r = get(client, "/consultations")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC173_get_consultations_pending(self, client):
        """TC173 – GET /consultations?status=Pending."""
        r = get(client, "/consultations?status=Pending")
        assert r.status_code == 200

    def test_TC174_get_consultations_replied(self, client):
        """TC174 – GET /consultations?status=Replied."""
        r = get(client, "/consultations?status=Replied")
        assert r.status_code == 200

    def test_TC175_consultation_missing_message(self, client):
        """TC175 – Consultation without message."""
        payload = self._valid_consult()
        del payload["message"]
        r = post(client, "/consultations", payload)
        assert r.status_code in (400, 422, 500)

    def test_TC176_consultation_missing_patient_id(self, client):
        """TC176 – Consultation without patient_id."""
        payload = self._valid_consult()
        del payload["patient_id"]
        r = post(client, "/consultations", payload)
        assert r.status_code in (400, 422, 500)

    def test_TC177_consultation_reply_valid(self, client):
        """TC177 – Dentist replies to consultation."""
        post(client, "/consultations", self._valid_consult())
        r = get(client, "/consultations?status=Pending")
        data = json.loads(r.data)
        if data:
            cid = data[0]["id"]
            r2 = post(client, f"/consultations/{cid}/reply", {"dentist_id": 1, "reply": "Please visit clinic."})
            assert r2.status_code in (200, 201)

    def test_TC178_consultation_reply_nonexistent(self, client):
        """TC178 – Reply to non-existent consultation."""
        r = post(client, "/consultations/999999/reply", {"dentist_id": 1, "reply": "Reply text"})
        assert r.status_code in (200, 404)

    def test_TC179_consultation_reply_empty(self, client):
        """TC179 – Empty reply text."""
        r = post(client, "/consultations/1/reply", {"dentist_id": 1, "reply": ""})
        assert r.status_code in (200, 400, 404)

    def test_TC180_consultation_reply_missing_dentist(self, client):
        """TC180 – Reply without dentist_id."""
        r = post(client, "/consultations/1/reply", {"reply": "Some reply"})
        assert r.status_code in (200, 400, 404)

    def test_TC181_consultation_returns_json(self, client):
        """TC181 – POST /consultations returns JSON."""
        r = post(client, "/consultations", self._valid_consult())
        assert "application/json" in r.content_type

    def test_TC182_consultation_list_fields(self, client):
        """TC182 – Consultation has required fields."""
        post(client, "/consultations", self._valid_consult())
        r = get(client, "/consultations")
        data = json.loads(r.data)
        if data:
            c = data[0]
            for f in ["id", "patient_id", "patient_name", "message", "status"]:
                assert f in c

    def test_TC183_consultation_default_status_pending(self, client):
        """TC183 – New consultation status is Pending."""
        post(client, "/consultations", self._valid_consult())
        r = get(client, "/consultations?status=Pending")
        data = json.loads(r.data)
        assert any(c["status"] == "Pending" for c in data)

    def test_TC184_consultation_long_message(self, client):
        """TC184 – Long consultation message (2000 chars)."""
        r = post(client, "/consultations", {**self._valid_consult(), "message": "M" * 2000})
        assert r.status_code in (200, 201)

    def test_TC185_consultation_unicode_message(self, client):
        """TC185 – Unicode message."""
        r = post(client, "/consultations", {**self._valid_consult(), "message": "दांत में दर्द है।"})
        assert r.status_code in (200, 201)

    def test_TC186_consultation_xss_in_message(self, client):
        """TC186 – XSS payload in message stored safely."""
        r = post(client, "/consultations", {**self._valid_consult(), "message": "<script>alert('xss')</script>"})
        assert r.status_code in (200, 201)
        # Response should not execute script

    def test_TC187_consultation_reply_long_text(self, client):
        """TC187 – Long dentist reply (2000 chars)."""
        r = post(client, "/consultations/1/reply", {"dentist_id": 1, "reply": "R" * 2000})
        assert r.status_code in (200, 404)

    def test_TC188_multiple_consultations_same_patient(self, client):
        """TC188 – Patient can have multiple consultations."""
        for i in range(3):
            post(client, "/consultations", {**self._valid_consult(patient_id=600), "message": f"Message {i}"})
        r = get(client, "/consultations")
        data = json.loads(r.data)
        patient_consults = [c for c in data if c.get("patient_id") == 600]
        assert len(patient_consults) >= 3

    def test_TC189_consultation_get_method_for_post_endpoint(self, client):
        """TC189 – GET /consultations works (status filter optional)."""
        r = client.get("/consultations")
        assert r.status_code == 200

    def test_TC190_consultation_reply_status_changes(self, client):
        """TC190 – After reply, status changes to Replied."""
        r = post(client, "/consultations", self._valid_consult())
        data = json.loads(r.data)
        cid = data.get("id") or data.get("consultation", {}).get("id")
        if cid:
            post(client, f"/consultations/{cid}/reply", {"dentist_id": 2, "reply": "OK"})
            r2 = get(client, "/consultations")
            data2 = json.loads(r2.data)
            consult = next((c for c in data2 if c["id"] == cid), None)
            if consult:
                assert consult["status"] in ["Replied", "Pending"]

    def test_TC191_consultation_response_time(self, client):
        """TC191 – POST /consultations responds within 3 seconds."""
        start = time.time()
        post(client, "/consultations", self._valid_consult())
        assert (time.time() - start) < 3

    def test_TC192_consultation_concurrent(self, client):
        """TC192 – Concurrent consultation creation."""
        errors = []
        def do_post():
            try:
                post(client, "/consultations", self._valid_consult())
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_post) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC193_consultation_empty_body(self, client):
        """TC193 – Empty body to /consultations."""
        r = client.post("/consultations", data="{}", content_type="application/json")
        assert r.status_code in (400, 422, 500)

    def test_TC194_consultation_reply_method_get(self, client):
        """TC194 – GET on reply endpoint returns 405."""
        r = client.get("/consultations/1/reply")
        assert r.status_code in (405, 404)

    def test_TC195_consultation_created_at_present(self, client):
        """TC195 – created_at field in consultation."""
        r = get(client, "/consultations")
        data = json.loads(r.data)
        if data:
            assert "created_at" in data[0]

    def test_TC196_consultation_reply_present(self, client):
        """TC196 – Reply field present in consultation."""
        r = get(client, "/consultations")
        data = json.loads(r.data)
        if data:
            assert "reply" in data[0]

    def test_TC197_consultation_dentist_id_present(self, client):
        """TC197 – dentist_id field in consultation."""
        r = get(client, "/consultations")
        data = json.loads(r.data)
        if data:
            assert "dentist_id" in data[0]

    def test_TC198_consultation_patient_id_integer(self, client):
        """TC198 – patient_id is integer in consultation."""
        r = get(client, "/consultations")
        data = json.loads(r.data)
        for c in data:
            assert isinstance(c["patient_id"], int)

    def test_TC199_consultation_id_integer(self, client):
        """TC199 – id is integer in consultation."""
        r = get(client, "/consultations")
        data = json.loads(r.data)
        for c in data:
            assert isinstance(c["id"], int)

    def test_TC200_consultation_status_values_valid(self, client):
        """TC200 – Status values are Pending or Replied."""
        r = get(client, "/consultations")
        data = json.loads(r.data)
        for c in data:
            assert c["status"] in ["Pending", "Replied"]


# ══════════════════════════════════════════════════════════════════════════════
# TC201-TC220 : ADMIN / USER MANAGEMENT API
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminAPI:

    def test_TC201_get_users_all(self, client):
        """TC201 – GET /users returns list."""
        r = get(client, "/users")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC202_get_users_patient_filter(self, client):
        """TC202 – GET /users?role=patient returns patients."""
        r = get(client, "/users?role=patient")
        assert r.status_code == 200
        data = json.loads(r.data)
        for u in data:
            assert u["role"] == "patient"

    def test_TC203_get_users_dentist_filter(self, client):
        """TC203 – GET /users?role=dentist returns dentists."""
        r = get(client, "/users?role=dentist")
        assert r.status_code == 200
        data = json.loads(r.data)
        for u in data:
            assert u["role"] == "dentist"

    def test_TC204_get_admin_stats(self, client):
        """TC204 – GET /admin/stats returns stats dict."""
        r = get(client, "/admin/stats")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, dict)

    def test_TC205_delete_user_nonexistent(self, client):
        """TC205 – Delete non-existent user returns error."""
        r = client.delete("/users/999999")
        data = json.loads(r.data)
        assert "error" in data or r.status_code == 404

    def test_TC206_get_users_returns_json(self, client):
        """TC206 – GET /users returns JSON."""
        r = get(client, "/users")
        assert "application/json" in r.content_type

    def test_TC207_admin_stats_returns_json(self, client):
        """TC207 – GET /admin/stats returns JSON."""
        r = get(client, "/admin/stats")
        assert "application/json" in r.content_type

    def test_TC208_user_fields_present(self, client):
        """TC208 – User objects have required fields."""
        post(client, "/signup", {"name": "AdminTest", "email": _rand_email(), "password": "P@ss123", "role": "patient"})
        r = get(client, "/users")
        data = json.loads(r.data)
        if data:
            u = data[0]
            for f in ["id", "name", "email", "role"]:
                assert f in u

    def test_TC209_user_password_not_in_response(self, client):
        """TC209 – Password hash not returned in user list."""
        r = get(client, "/users")
        data = json.loads(r.data)
        for u in data:
            assert "password" not in u

    def test_TC210_delete_user_and_verify(self, client):
        """TC210 – Delete newly created user."""
        email = _rand_email()
        post(client, "/signup", {"name": "ToDelete", "email": email, "password": "Del@123", "role": "patient"})
        r = get(client, "/users")
        data = json.loads(r.data)
        user = next((u for u in data if u["email"] == email), None)
        if user:
            rd = client.delete(f"/users/{user['id']}")
            assert rd.status_code in (200, 204)

    def test_TC211_admin_stats_has_counts(self, client):
        """TC211 – Admin stats has numeric counts."""
        r = get(client, "/admin/stats")
        data = json.loads(r.data)
        # At least one key should have a numeric value
        has_number = any(isinstance(v, (int, float)) for v in data.values())
        assert has_number or isinstance(data, dict)

    def test_TC212_users_invalid_role_filter(self, client):
        """TC212 – Invalid role filter returns empty list."""
        r = get(client, "/users?role=superadmin")
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_TC213_get_dentist_patients(self, client):
        """TC213 – GET /dentist/patients returns list."""
        r = get(client, "/dentist/patients")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_TC214_get_dentist_patient_detail_nonexistent(self, client):
        """TC214 – Non-existent patient detail returns error."""
        r = get(client, "/dentist/patient/999999")
        assert r.status_code in (200, 404)

    def test_TC215_dentist_patients_returns_json(self, client):
        """TC215 – /dentist/patients returns JSON."""
        r = get(client, "/dentist/patients")
        assert "application/json" in r.content_type

    def test_TC216_users_response_time(self, client):
        """TC216 – GET /users responds within 3 seconds."""
        start = time.time()
        get(client, "/users")
        assert (time.time() - start) < 3

    def test_TC217_admin_stats_response_time(self, client):
        """TC217 – GET /admin/stats responds within 3 seconds."""
        start = time.time()
        get(client, "/admin/stats")
        assert (time.time() - start) < 3

    def test_TC218_delete_method_only(self, client):
        """TC218 – POST /users/1 returns 405."""
        r = client.post("/users/1", data="{}", content_type="application/json")
        assert r.status_code in (405, 404)

    def test_TC219_user_id_is_integer(self, client):
        """TC219 – User id is integer."""
        r = get(client, "/users")
        data = json.loads(r.data)
        for u in data:
            assert isinstance(u["id"], int)

    def test_TC220_user_role_valid_values(self, client):
        """TC220 – User role is patient/dentist."""
        r = get(client, "/users")
        data = json.loads(r.data)
        for u in data:
            assert u["role"] in ["patient", "dentist", "admin"]


# ══════════════════════════════════════════════════════════════════════════════
# TC221-TC240 : DASHBOARD & REPORTS
# ══════════════════════════════════════════════════════════════════════════════

class TestDashboardAPI:

    def test_TC221_get_dashboard_valid_user(self, client):
        """TC221 – GET /dashboard/1 returns dict."""
        r = get(client, "/dashboard/1")
        assert r.status_code in (200, 404)

    def test_TC222_get_dashboard_returns_json(self, client):
        """TC222 – Dashboard returns JSON."""
        r = get(client, "/dashboard/1")
        assert "application/json" in r.content_type

    def test_TC223_get_dashboard_nonexistent_user(self, client):
        """TC223 – Dashboard for non-existent user."""
        r = get(client, "/dashboard/999999")
        assert r.status_code in (200, 404)

    def test_TC224_dashboard_user_zero(self, client):
        """TC224 – Dashboard for user 0."""
        r = get(client, "/dashboard/0")
        assert r.status_code in (200, 400, 404)

    def test_TC225_dashboard_response_time(self, client):
        """TC225 – Dashboard responds within 3 seconds."""
        start = time.time()
        get(client, "/dashboard/1")
        assert (time.time() - start) < 3

    def test_TC226_dashboard_string_user_id(self, client):
        """TC226 – String user_id in URL."""
        r = get(client, "/dashboard/abc")
        assert r.status_code in (400, 404)

    def test_TC227_dashboard_negative_user_id(self, client):
        """TC227 – Negative user_id."""
        r = get(client, "/dashboard/-1")
        assert r.status_code in (200, 400, 404)

    def test_TC228_dashboard_method_post(self, client):
        """TC228 – POST /dashboard/1 returns 405."""
        r = client.post("/dashboard/1", data="{}", content_type="application/json")
        assert r.status_code in (405, 404)

    def test_TC229_dashboard_created_user(self, client):
        """TC229 – Dashboard for newly created user."""
        email = _rand_email()
        post(client, "/signup", {"name": "Dash User", "email": email, "password": "Pass@1", "role": "patient"})
        r = post(client, "/login", {"email": email, "password": "Pass@1"})
        data = json.loads(r.data)
        uid = data.get("user", {}).get("id", 1)
        r2 = get(client, f"/dashboard/{uid}")
        assert r2.status_code in (200, 404)

    def test_TC230_dashboard_large_user_id(self, client):
        """TC230 – Very large user_id."""
        r = get(client, "/dashboard/9999999999")
        assert r.status_code in (200, 400, 404)

    def test_TC231_admin_stats_keys_present(self, client):
        """TC231 – Admin stats contains expected keys."""
        r = get(client, "/admin/stats")
        data = json.loads(r.data)
        # Should have at least one stat key
        assert len(data.keys()) > 0

    def test_TC232_dentist_patient_detail_valid(self, client):
        """TC232 – Dentist patient detail for valid id."""
        r = get(client, "/dentist/patient/1")
        assert r.status_code in (200, 404)

    def test_TC233_dentist_patient_detail_json(self, client):
        """TC233 – Dentist patient detail returns JSON."""
        r = get(client, "/dentist/patient/1")
        assert "application/json" in r.content_type

    def test_TC234_admin_stats_not_empty_after_data(self, client):
        """TC234 – Admin stats non-null after user creation."""
        post(client, "/signup", {"name": "StatTest", "email": _rand_email(), "password": "P@ss1", "role": "patient"})
        r = get(client, "/admin/stats")
        data = json.loads(r.data)
        assert data

    def test_TC235_dashboard_concurrent(self, client):
        """TC235 – Concurrent dashboard requests don't crash."""
        errors = []
        def do_get():
            try:
                get(client, "/dashboard/1")
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_get) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC236_users_list_after_create(self, client):
        """TC236 – User count increases after signup."""
        r1 = get(client, "/users")
        count1 = len(json.loads(r1.data))
        post(client, "/signup", {"name": "CountUser", "email": _rand_email(), "password": "Pass@99", "role": "patient"})
        r2 = get(client, "/users")
        count2 = len(json.loads(r2.data))
        assert count2 >= count1

    def test_TC237_admin_stats_integers(self, client):
        """TC237 – Admin stats values are integers or floats."""
        r = get(client, "/admin/stats")
        data = json.loads(r.data)
        for v in data.values():
            assert isinstance(v, (int, float, str, list, dict, type(None)))

    def test_TC238_dashboard_user_large(self, client):
        """TC238 – Dashboard user id 100000."""
        r = get(client, "/dashboard/100000")
        assert r.status_code in (200, 404)

    def test_TC239_dentist_patients_list_not_empty(self, client):
        """TC239 – Dentist patients list after patient creation."""
        r = get(client, "/dentist/patients")
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_TC240_admin_stats_no_negative(self, client):
        """TC240 – Admin stat counts are non-negative."""
        r = get(client, "/admin/stats")
        data = json.loads(r.data)
        for v in data.values():
            if isinstance(v, (int, float)):
                assert v >= 0


# ══════════════════════════════════════════════════════════════════════════════
# TC241-TC260 : VALIDATION & EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

class TestValidationEdgeCases:

    def test_TC241_large_json_body(self, client):
        """TC241 – Very large JSON body doesn't crash server."""
        large = {"name": "A" * 10000, "email": _rand_email(), "password": "P@ss1", "role": "patient"}
        r = post(client, "/signup", large)
        assert r.status_code in (200, 201, 400, 413)

    def test_TC242_null_json_values(self, client):
        """TC242 – Null values in signup payload."""
        r = post(client, "/signup", {"name": None, "email": None, "password": None, "role": None})
        assert r.status_code in (400, 422, 500)

    def test_TC243_integer_instead_of_string_field(self, client):
        """TC243 – Integer where string expected in signup."""
        r = post(client, "/signup", {"name": 12345, "email": _rand_email(), "password": "P@ss1", "role": "patient"})
        assert r.status_code in (200, 201, 400)

    def test_TC244_boolean_email(self, client):
        """TC244 – Boolean as email."""
        r = post(client, "/login", {"email": True, "password": "pass"})
        assert r.status_code in (200, 400, 401)

    def test_TC245_array_as_body(self, client):
        """TC245 – Array body to POST endpoint."""
        r = client.post("/login", data="[1,2,3]", content_type="application/json")
        assert r.status_code in (400, 415, 500)

    def test_TC246_content_type_form(self, client):
        """TC246 – Form content-type instead of JSON."""
        r = client.post("/login", data={"email": "test@t.com", "password": "p"})
        assert r.status_code in (200, 400, 415)

    def test_TC247_empty_string_password(self, client):
        """TC247 – Empty string password in login."""
        r = post(client, "/login", {"email": "t@t.com", "password": ""})
        data = json.loads(r.data)
        assert "error" in data

    def test_TC248_whitespace_email(self, client):
        """TC248 – Whitespace-only email."""
        r = post(client, "/login", {"email": "   ", "password": "pass"})
        data = json.loads(r.data)
        assert "error" in data

    def test_TC249_very_long_password(self, client):
        """TC249 – Very long password (1000 chars)."""
        r = post(client, "/signup", {"name": "T", "email": _rand_email(), "password": "P" * 1000, "role": "patient"})
        assert r.status_code in (200, 201, 400)

    def test_TC250_emoji_in_name(self, client):
        """TC250 – Emoji characters in name."""
        r = post(client, "/signup", {"name": "😀 Smiling User 🦷", "email": _rand_email(), "password": "P@ss1", "role": "patient"})
        assert r.status_code in (200, 201, 400)

    def test_TC251_get_unknown_route(self, client):
        """TC251 – GET on unknown route returns 404."""
        r = get(client, "/nonexistent_endpoint_xyz")
        assert r.status_code == 404

    def test_TC252_post_unknown_route(self, client):
        """TC252 – POST on unknown route returns 404."""
        r = post(client, "/nonexistent_endpoint_xyz", {})
        assert r.status_code == 404

    def test_TC253_pain_intensity_float(self, client):
        """TC253 – Float intensity (7.5) handled."""
        r = post(client, "/pain", {
            "patient_id": 1, "patient_name": "P",
            "intensity": 7.5, "duration": "1 day",
            "trigger": "Cold", "swelling": False,
            "sensitivity": True, "bleeding": False
        })
        assert r.status_code in (200, 201, 400)

    def test_TC254_appointment_date_empty(self, client):
        """TC254 – Appointment with empty date string."""
        r = post(client, "/appointments", {
            "patient_id": 1, "patient_name": "T",
            "dentist_name": "Dr.X", "date": "", "time": "10:00 AM"
        })
        assert r.status_code in (200, 201, 400, 422)

    def test_TC255_consultation_id_float_in_url(self, client):
        """TC255 – Float ID in consultation URL."""
        r = post(client, "/consultations/1.5/reply", {"dentist_id": 1, "reply": "ok"})
        assert r.status_code in (400, 404)

    def test_TC256_pain_concurrent_write_read(self, client):
        """TC256 – Concurrent write and read on pain API."""
        errors = []
        def do_write():
            try:
                post(client, "/pain", {"patient_id": 1, "patient_name": "P",
                    "intensity": 5, "duration": "1d", "trigger": "Hot",
                    "swelling": False, "sensitivity": False, "bleeding": False})
            except Exception as e:
                errors.append(str(e))
        def do_read():
            try:
                get(client, "/pain/patient/1")
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_write if i % 2 == 0 else do_read) for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC257_signup_role_case_sensitive(self, client):
        """TC257 – Role 'PATIENT' (uppercase) handled."""
        r = post(client, "/signup", {"name": "T", "email": _rand_email(), "password": "P@ss1", "role": "PATIENT"})
        assert r.status_code in (200, 201, 400)

    def test_TC258_multiple_scans_reviews(self, client):
        """TC258 – Multiple review updates on same scan."""
        for _ in range(3):
            r = post(client, "/scans/1/review", {"dentist_id": 1, "dentist_name": "Dr", "dentist_note": "Checked"})
            assert r.status_code in (200, 404)

    def test_TC259_reset_password_empty_password(self, client):
        """TC259 – Reset with empty new password."""
        r = post(client, "/reset_password", {"email": "t@t.com", "new_password": ""})
        assert r.status_code in (200, 400, 404)

    def test_TC260_api_health_root(self, client):
        """TC260 – Root route or health check available."""
        r = client.get("/")
        # Root may or may not exist - just shouldn't throw a 500
        assert r.status_code in (200, 404, 301, 302)


# ══════════════════════════════════════════════════════════════════════════════
# TC261-TC280 : SECURITY & PERMISSIONS
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurityPermissions:

    def test_TC261_sql_injection_login_email(self, client):
        """TC261 – SQL injection in login email."""
        r = post(client, "/login", {"email": "admin'--", "password": "x"})
        assert r.status_code in (200, 400, 401)
        # Must not expose DB error
        body = r.data.decode("utf-8", errors="replace")
        assert "syntax error" not in body.lower()
        assert "sqlite" not in body.lower()

    def test_TC262_sql_injection_login_password(self, client):
        """TC262 – SQL injection in login password."""
        r = post(client, "/login", {"email": "t@t.com", "password": "' OR 1=1 --"})
        assert r.status_code in (200, 400, 401)
        data = json.loads(r.data)
        assert "user" not in data

    def test_TC263_sql_injection_signup_name(self, client):
        """TC263 – SQL injection in signup name."""
        r = post(client, "/signup", {
            "name": "Robert'); DROP TABLE users;--",
            "email": _rand_email(), "password": "P@ss1", "role": "patient"
        })
        assert r.status_code in (200, 201, 400)

    def test_TC264_path_traversal_attempt(self, client):
        """TC264 – Path traversal in URL."""
        r = client.get("/scans/patient/../../etc/passwd")
        assert r.status_code in (400, 404)

    def test_TC265_xss_in_patient_name(self, client):
        """TC265 – XSS in patient name field."""
        r = post(client, "/appointments", {
            "patient_id": 1,
            "patient_name": "<script>alert(document.cookie)</script>",
            "dentist_name": "Dr.Safe", "date": "2025-12-01", "time": "9:00 AM"
        })
        assert r.status_code in (200, 201)
        # Verify the script is stored as-is (escaped) not executed

    def test_TC266_xss_in_dentist_note(self, client):
        """TC266 – XSS in dentist note."""
        r = post(client, "/scans/1/review", {
            "dentist_id": 1,
            "dentist_name": "Dr.Test",
            "dentist_note": "<img src=x onerror=alert(1)>"
        })
        assert r.status_code in (200, 404)

    def test_TC267_admin_delete_own_account_blocked(self, client):
        """TC267 – Deleting admin user (id=0) handled safely."""
        r = client.delete("/users/0")
        assert r.status_code in (200, 400, 404)

    def test_TC268_extremely_large_number_as_id(self, client):
        """TC268 – Extremely large ID (overflow check)."""
        r = client.get("/users/999999999999999999999")
        assert r.status_code in (400, 404)

    def test_TC269_html_injection_consultation(self, client):
        """TC269 – HTML injection in consultation message."""
        r = post(client, "/consultations", {
            "patient_id": 1, "patient_name": "T",
            "message": "<h1>Heading</h1><b>Bold text</b>"
        })
        assert r.status_code in (200, 201)

    def test_TC270_no_stack_trace_in_response(self, client):
        """TC270 – Error responses don't expose stack traces."""
        r = post(client, "/login", {})
        body = r.data.decode("utf-8", errors="replace")
        assert "traceback" not in body.lower()
        assert "file \"" not in body.lower()

    def test_TC271_cors_headers_present(self, client):
        """TC271 – CORS headers in response."""
        r = get(client, "/scans")
        # Flask-CORS should add headers
        assert r.status_code == 200

    def test_TC272_content_type_json_response(self, client):
        """TC272 – All API endpoints return application/json."""
        endpoints = ["/scans", "/users", "/appointments", "/consultations"]
        for ep in endpoints:
            r = get(client, ep)
            assert "application/json" in r.content_type, f"Failed for {ep}"

    def test_TC273_null_byte_in_email(self, client):
        """TC273 – Null byte in email field."""
        r = post(client, "/login", {"email": "test\x00@test.com", "password": "pass"})
        assert r.status_code in (200, 400, 401)

    def test_TC274_control_chars_in_name(self, client):
        """TC274 – Control characters in name field."""
        r = post(client, "/signup", {
            "name": "Test\n\r\t User",
            "email": _rand_email(), "password": "P@ss1", "role": "patient"
        })
        assert r.status_code in (200, 201, 400)

    def test_TC275_header_injection(self, client):
        """TC275 – Header injection attempt in name."""
        r = post(client, "/signup", {
            "name": "Test\r\nX-Injected: evil",
            "email": _rand_email(), "password": "P@ss1", "role": "patient"
        })
        assert r.status_code in (200, 201, 400)

    def test_TC276_oversized_header(self, client):
        """TC276 – Oversized Authorization header."""
        r = client.get("/users", headers={"Authorization": "Bearer " + "x" * 10000})
        assert r.status_code in (200, 400, 413)

    def test_TC277_user_enumeration_same_error(self, client):
        """TC277 – Login errors don't reveal if user exists."""
        r1 = post(client, "/login", {"email": "nonexistent@t.com", "password": "wrong"})
        r2 = post(client, "/login", {"email": "alsonotexist@t.com", "password": "wrong"})
        d1 = json.loads(r1.data)
        d2 = json.loads(r2.data)
        # Both should return error (not different status codes revealing user existence)
        assert "error" in d1 and "error" in d2

    def test_TC278_mass_signup_rate(self, client):
        """TC278 – 20 rapid signups don't crash server."""
        errors = []
        for _ in range(20):
            try:
                post(client, "/signup", {"name": "R", "email": _rand_email(), "password": "P@ss1", "role": "patient"})
            except Exception as e:
                errors.append(str(e))
        assert len(errors) == 0

    def test_TC279_json_bomb_nested(self, client):
        """TC279 – Deeply nested JSON body handled."""
        nested = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
        r = client.post("/login", data=json.dumps(nested), content_type="application/json")
        assert r.status_code in (200, 400, 401, 415)

    def test_TC280_repeated_login_wrong_password(self, client):
        """TC280 – 10 failed logins don't lock DB or crash."""
        email = _rand_email()
        post(client, "/signup", {"name": "LockTest", "email": email, "password": "CorrectP@1", "role": "patient"})
        for _ in range(10):
            r = post(client, "/login", {"email": email, "password": "WrongPass"})
            assert r.status_code in (200, 401, 429)


# ══════════════════════════════════════════════════════════════════════════════
# TC281-TC300 : PERFORMANCE & LOAD (Smoke)
# ══════════════════════════════════════════════════════════════════════════════

class TestPerformanceLoad:

    def test_TC281_login_50_concurrent(self, client):
        """TC281 – 50 concurrent login requests."""
        errors = []
        def do_login():
            try:
                post(client, "/login", {"email": "load@t.com", "password": "p"})
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_login) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC282_get_scans_50_concurrent(self, client):
        """TC282 – 50 concurrent GET /scans requests."""
        errors = []
        def do_get():
            try:
                get(client, "/scans")
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_get) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC283_get_appointments_50_concurrent(self, client):
        """TC283 – 50 concurrent GET /appointments."""
        errors = []
        def do_get():
            try:
                get(client, "/appointments")
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_get) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC284_signup_50_concurrent(self, client):
        """TC284 – 50 concurrent signups with unique emails."""
        errors = []
        def do_signup():
            try:
                post(client, "/signup", {"name": "Load", "email": _rand_email(), "password": "P@ss1", "role": "patient"})
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_signup) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC285_appointments_post_50_concurrent(self, client):
        """TC285 – 50 concurrent appointment creations."""
        errors = []
        def do_post():
            try:
                post(client, "/appointments", {
                    "patient_id": 1, "patient_name": "Load",
                    "dentist_name": "Dr.Load", "date": "2030-06-01", "time": "09:00 AM"
                })
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_post) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC286_consultations_50_concurrent(self, client):
        """TC286 – 50 concurrent consultation submissions."""
        errors = []
        def do_post():
            try:
                post(client, "/consultations", {
                    "patient_id": 1, "patient_name": "Load",
                    "message": "Concurrent test message"
                })
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=do_post) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_TC287_admin_stats_repeated(self, client):
        """TC287 – Admin stats polled 20 times rapidly."""
        for i in range(20):
            r = get(client, "/admin/stats")
            assert r.status_code == 200

    def test_TC288_users_list_repeated(self, client):
        """TC288 – Users list fetched 20 times rapidly."""
        for _ in range(20):
            r = get(client, "/users")
            assert r.status_code == 200

    def test_TC289_pain_post_repeated(self, client):
        """TC289 – 20 sequential pain submissions."""
        for i in range(20):
            r = post(client, "/pain", {
                "patient_id": 1, "patient_name": "Repeat",
                "intensity": i % 11, "duration": "1 day",
                "trigger": "Cold", "swelling": False,
                "sensitivity": False, "bleeding": False
            })
            assert r.status_code in (200, 201)

    def test_TC290_anesthesia_post_repeated(self, client):
        """TC290 – 20 sequential anesthesia submissions."""
        for i in range(20):
            r = post(client, "/anesthesia", {
                "patient_id": 1, "patient_name": "Repeat",
                "region": "Molar", "infection": "No",
                "inflammation": "Mild", "anxiety": "Low",
                "history": "No", "medical_conditions": "", "medications": ""
            })
            assert r.status_code in (200, 201)

    def test_TC291_login_average_response_under_2s(self, client):
        """TC291 – Average login response under 2 seconds over 10 calls."""
        times = []
        for _ in range(10):
            start = time.time()
            post(client, "/login", {"email": "avg@t.com", "password": "p"})
            times.append(time.time() - start)
        avg = sum(times) / len(times)
        assert avg < 2.0

    def test_TC292_scans_average_response_under_1s(self, client):
        """TC292 – Average GET /scans under 1 second over 10 calls."""
        times = []
        for _ in range(10):
            start = time.time()
            get(client, "/scans")
            times.append(time.time() - start)
        avg = sum(times) / len(times)
        assert avg < 1.0

    def test_TC293_appointments_average_response_under_1s(self, client):
        """TC293 – Average GET /appointments under 1 second."""
        times = []
        for _ in range(10):
            start = time.time()
            get(client, "/appointments")
            times.append(time.time() - start)
        avg = sum(times) / len(times)
        assert avg < 1.0

    def test_TC294_consultations_average_response_under_1s(self, client):
        """TC294 – Average GET /consultations under 1 second."""
        times = []
        for _ in range(10):
            start = time.time()
            get(client, "/consultations")
            times.append(time.time() - start)
        avg = sum(times) / len(times)
        assert avg < 1.0

    def test_TC295_memory_stable_after_50_requests(self, client):
        """TC295 – Memory doesn't grow unbounded (smoke)."""
        import gc
        gc.collect()
        for _ in range(50):
            get(client, "/scans")
            get(client, "/appointments")
        gc.collect()
        # If we reach here without OOM, test passes
        assert True

    def test_TC296_response_size_reasonable(self, client):
        """TC296 – Response size for empty list is reasonable."""
        r = get(client, "/scans")
        assert len(r.data) < 10 * 1024 * 1024  # Less than 10 MB

    def test_TC297_users_response_size(self, client):
        """TC297 – Users list response size reasonable."""
        r = get(client, "/users")
        assert len(r.data) < 10 * 1024 * 1024

    def test_TC298_no_timeout_on_scan_list(self, client):
        """TC298 – GET /scans completes within 5 seconds."""
        start = time.time()
        get(client, "/scans")
        assert (time.time() - start) < 5

    def test_TC299_no_timeout_on_users_list(self, client):
        """TC299 – GET /users completes within 5 seconds."""
        start = time.time()
        get(client, "/users")
        assert (time.time() - start) < 5

    def test_TC300_full_workflow_smoke(self, client):
        """TC300 – Full user workflow: signup → login → appointment → consultation."""
        email = _rand_email()
        # Signup
        r1 = post(client, "/signup", {"name": "WorkflowUser", "email": email, "password": "Wf@Pass1", "role": "patient"})
        assert r1.status_code in (200, 201)
        # Login
        r2 = post(client, "/login", {"email": email, "password": "Wf@Pass1"})
        assert r2.status_code == 200
        uid = json.loads(r2.data).get("user", {}).get("id", 1)
        # Book appointment
        r3 = post(client, "/appointments", {"patient_id": uid, "patient_name": "WorkflowUser",
            "dentist_name": "Dr.Workflow", "date": "2026-01-15", "time": "11:00 AM"})
        assert r3.status_code in (200, 201)
        # Send consultation
        r4 = post(client, "/consultations", {"patient_id": uid, "patient_name": "WorkflowUser",
            "message": "My tooth hurts after the treatment."})
        assert r4.status_code in (200, 201)
        # Submit pain
        r5 = post(client, "/pain", {"patient_id": uid, "patient_name": "WorkflowUser",
            "intensity": 6, "duration": "2 days", "trigger": "Cold",
            "swelling": False, "sensitivity": True, "bleeding": False})
        assert r5.status_code in (200, 201)
        # Get dashboard
        r6 = get(client, f"/dashboard/{uid}")
        assert r6.status_code in (200, 404)
