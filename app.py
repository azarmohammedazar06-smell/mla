from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

WHATSAPP_NUMBER = "919483927300"
DATA_DIR = Path("data")
UPLOAD_DIR = Path("static/uploads")
DB_PATH = DATA_DIR / "portal.db"
MAX_IMAGE_BYTES = int(1.6 * 1024 * 1024)
MAX_VIDEO_BYTES = int(5 * 1024 * 1024)
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".ogg"}

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

LANG_DATA = {
    "en": {
        "title": "YOUR MLA — Public Help Portal",
        "subtitle": "Report public issues — saved on server & auto-opened in WhatsApp",
        "report": "Report an Issue",
        "about": "About / Plans",
        "list": "View All Complaints",
        "admin": "Admin Panel",
        "export": "Export JSON",
        "reportTitle": "Report a Public Issue",
        "reportDesc": "Fill details below — complaint is saved and WhatsApp opens automatically.",
        "category": "Issue Category",
        "desc": "Describe the Issue",
        "age": "Your Age Group",
        "contactMethod": "Preferred Contact Method (optional)",
        "contactInfo": "Contact Info (optional)",
        "uploadImg": "Upload Image (optional)",
        "uploadVid": "Upload Video (optional)",
        "submit": "Save & Send on WhatsApp",
        "aboutTitle": "About",
        "aboutText": "This portal helps citizens report public issues directly to MLA’s office through WhatsApp.",
        "noComplaints": "No complaints yet.",
        "status": "Status",
        "statusOptions": ["New", "In Review", "Resolved"],
        "search": "Search description",
        "apply": "Apply",
        "clear": "Clear",
        "login": "Admin Login",
        "username": "Username",
        "password": "Password",
        "logout": "Logout",
        "errors": {
            "category": "Please select a category.",
            "description": "Please describe the issue.",
            "image_type": "Unsupported image format.",
            "video_type": "Unsupported video format.",
            "image_size": "Image exceeds 1.6 MB limit.",
            "video_size": "Video exceeds 5 MB limit.",
            "auth": "Invalid username or password.",
        },
    },
    "kn": {
        "title": "ನಿಮ್ಮ ಶಾಸಕರು — ಸಾರ್ವಜನಿಕ ಸಹಾಯ ಪೋರ್ಟಲ್",
        "subtitle": "ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆಗಳನ್ನು ವರದಿ ಮಾಡಿ — ಸರ್ವರ್‌ನಲ್ಲಿ ಉಳಿಸಿ, ವಾಟ್ಸಾಪ್ ಸ್ವಯಂ ತೆರೆಯುತ್ತದೆ",
        "report": "ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ",
        "about": "ಬಗ್ಗೆ / ಯೋಜನೆಗಳು",
        "list": "ಎಲ್ಲ ದೂರುಗಳನ್ನು ನೋಡಿ",
        "admin": "ನಿರ್ವಾಹಕ ಫಲಕ",
        "export": "JSON ರಫ್ತು",
        "reportTitle": "ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ",
        "reportDesc": "ಕೆಳಗಿನ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ — ದೂರು ಉಳಿಯುತ್ತದೆ ಮತ್ತು ವಾಟ್ಸಾಪ್ ಸ್ವಯಂ ತೆರೆಯುತ್ತದೆ.",
        "category": "ಸಮಸ್ಯೆಯ ವರ್ಗ",
        "desc": "ಸಮಸ್ಯೆಯನ್ನು ವಿವರಿಸಿ",
        "age": "ನಿಮ್ಮ ವಯೋಮಾನದ ಗುಂಪು",
        "contactMethod": "ಆದ್ಯತೆಯ ಸಂಪರ್ಕ ವಿಧಾನ (ಐಚ್ಛಿಕ)",
        "contactInfo": "ಸಂಪರ್ಕ ಮಾಹಿತಿ (ಐಚ್ಛಿಕ)",
        "uploadImg": "ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (ಐಚ್ಛಿಕ)",
        "uploadVid": "ವೀಡಿಯೊ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (ಐಚ್ಛಿಕ)",
        "submit": "ಉಳಿಸಿ ಮತ್ತು ವಾಟ್ಸಾಪ್‌ಗೆ ಕಳುಹಿಸಿ",
        "aboutTitle": "ಬಗ್ಗೆ",
        "aboutText": "ಈ ಪೋರ್ಟಲ್ ನಾಗರಿಕರಿಗೆ ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆಗಳನ್ನು ನೇರವಾಗಿ ಶಾಸಕರ ಕಚೇರಿಗೆ ವಾಟ್ಸಾಪ್ ಮೂಲಕ ವರದಿ ಮಾಡಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
        "noComplaints": "ಇನ್ನೂ ಯಾವುದೇ ದೂರುಗಳಿಲ್ಲ.",
        "status": "ಸ್ಥಿತಿ",
        "statusOptions": ["ಹೊಸದು", "ಪರಿಶೀಲನೆಯಲ್ಲಿ", "ಪರಿಹರಿಸಲಾಗಿದೆ"],
        "search": "ವಿವರಣೆ ಹುಡುಕು",
        "apply": "ಅನ್ವಯಿಸು",
        "clear": "ರಿಸೆಟ್",
        "login": "ನಿರ್ವಾಹಕ ಲಾಗಿನ್",
        "username": "ಬಳಕೆದಾರ ಹೆಸರು",
        "password": "ಪಾಸ್ವರ್ಡ್",
        "logout": "ಲಾಗ್ ಔಟ್",
        "errors": {
            "category": "ದಯವಿಟ್ಟು ಸಮಸ್ಯೆಯ ವರ್ಗವನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
            "description": "ದಯವಿಟ್ಟು ಸಮಸ್ಯೆಯನ್ನು ವಿವರಿಸಿ.",
            "image_type": "ಚಿತ್ರದ ಪ್ರಕಾರ ಬೆಂಬಲಿತವಲ್ಲ.",
            "video_type": "ವೀಡಿಯೊ ಪ್ರಕಾರ ಬೆಂಬಲಿತವಲ್ಲ.",
            "image_size": "ಚಿತ್ರದ ಗಾತ್ರ 1.6 MB ಮೀರಿದೆ.",
            "video_size": "ವೀಡಿಯೊ ಗಾತ್ರ 5 MB ಮೀರಿದೆ.",
            "auth": "ತಪ್ಪು ಬಳಕೆದಾರ ಹೆಸರು ಅಥವಾ ಪಾಸ್ವರ್ಡ್.",
        },
    },
}

CATEGORIES = ["Health", "Agriculture", "Education", "Infrastructure", "Other"]
AGE_GROUPS = ["18–30", "30–45", "45+"]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin'
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            age_group TEXT,
            contact_method TEXT,
            contact_info TEXT,
            status TEXT NOT NULL,
            image_path TEXT,
            video_path TEXT
        )
        """
    )
    existing = db.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)).fetchone()
    if existing is None:
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
            (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD)),
        )
    db.commit()
    db.close()


def query_complaints(category: str = "", search: str = "") -> list[dict]:
    db = get_db()
    sql = "SELECT * FROM complaints WHERE 1=1"
    params: list[str] = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    if search:
        sql += " AND lower(description) LIKE ?"
        params.append(f"%{search.lower()}%")
    sql += " ORDER BY datetime(created_at) DESC"
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def _validate_upload(file_storage, allowed_extensions: set[str], max_bytes: int) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    ext = Path(file_storage.filename).suffix.lower()
    if ext not in allowed_extensions:
        return "type"
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > max_bytes:
        return "size"
    return None


def save_upload(file_storage, prefix: str) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    safe_name = secure_filename(file_storage.filename)
    filename = f"{prefix}_{secrets.token_hex(4)}_{safe_name}"
    target = UPLOAD_DIR / filename
    file_storage.save(target)
    return f"uploads/{filename}"


def is_admin_logged_in() -> bool:
    return bool(session.get("admin_user"))


@app.get("/")
def index():
    lang = request.args.get("lang", "en")
    if lang not in LANG_DATA:
        lang = "en"
    section = request.args.get("section", "form")
    error = request.args.get("error", "")
    selected_category = request.args.get("category", "")
    search = request.args.get("search", "").strip()
    complaints = query_complaints(selected_category, search) if section in {"list", "admin"} else []

    return render_template(
        "index.html",
        t=LANG_DATA[lang],
        lang=lang,
        section=section,
        complaints=complaints,
        error=error,
        categories=CATEGORIES,
        age_groups=AGE_GROUPS,
        selected_category=selected_category,
        search=search,
        is_admin=is_admin_logged_in(),
        auto_wa=request.args.get("wa", ""),
    )


@app.post("/complaints")
def submit_complaint():
    lang = request.form.get("lang", "en")
    if lang not in LANG_DATA:
        lang = "en"

    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    if not category:
        return redirect(url_for("index", lang=lang, section="form", error=LANG_DATA[lang]["errors"]["category"]))
    if not description:
        return redirect(url_for("index", lang=lang, section="form", error=LANG_DATA[lang]["errors"]["description"]))

    image = request.files.get("image")
    video = request.files.get("video")

    image_err = _validate_upload(image, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_BYTES)
    if image_err == "type":
        return redirect(url_for("index", lang=lang, section="form", error=LANG_DATA[lang]["errors"]["image_type"]))
    if image_err == "size":
        return redirect(url_for("index", lang=lang, section="form", error=LANG_DATA[lang]["errors"]["image_size"]))

    video_err = _validate_upload(video, ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_BYTES)
    if video_err == "type":
        return redirect(url_for("index", lang=lang, section="form", error=LANG_DATA[lang]["errors"]["video_type"]))
    if video_err == "size":
        return redirect(url_for("index", lang=lang, section="form", error=LANG_DATA[lang]["errors"]["video_size"]))

    complaint = {
        "id": secrets.token_hex(4),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "description": description,
        "age_group": request.form.get("age_group", "").strip(),
        "contact_method": request.form.get("contact_method", "").strip(),
        "contact_info": request.form.get("contact_info", "").strip(),
        "status": LANG_DATA[lang]["statusOptions"][0],
        "image_path": save_upload(image, "img"),
        "video_path": save_upload(video, "vid"),
    }

    db = get_db()
    db.execute(
        """
        INSERT INTO complaints (
            id, created_at, category, description, age_group, contact_method,
            contact_info, status, image_path, video_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            complaint["id"],
            complaint["created_at"],
            complaint["category"],
            complaint["description"],
            complaint["age_group"],
            complaint["contact_method"],
            complaint["contact_info"],
            complaint["status"],
            complaint["image_path"],
            complaint["video_path"],
        ),
    )
    db.commit()

    lines = [
        f"Complaint ID: {complaint['id']}",
        f"Category: {complaint['category']}",
        f"Description: {complaint['description']}",
    ]
    if complaint["age_group"]:
        lines.append(f"Age: {complaint['age_group']}")
    if complaint["contact_method"]:
        lines.append(f"Contact via: {complaint['contact_method']}")
    if complaint["contact_info"]:
        lines.append(f"Contact info: {complaint['contact_info']}")
    if complaint["video_path"]:
        lines.append("(Video uploaded)")
    if complaint["image_path"]:
        lines.append("(Image uploaded)")
    lines.append(f"Submitted at: {complaint['created_at']}")
    lines.append("(Report sent from MLA Portal)")
    wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(chr(10).join(lines))}"
    return redirect(url_for("index", lang=lang, section="list", wa=wa_url))


@app.post("/login")
def login():
    lang = request.form.get("lang", "en")
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        session["admin_user"] = user["username"]
        return redirect(url_for("index", section="admin", lang=lang))

    return redirect(url_for("index", section="admin", lang=lang, error=LANG_DATA.get(lang, LANG_DATA["en"])["errors"]["auth"]))


@app.get("/logout")
def logout():
    lang = request.args.get("lang", "en")
    session.clear()
    return redirect(url_for("index", section="form", lang=lang))


@app.post("/complaints/<complaint_id>/status")
def update_status(complaint_id: str):
    if not is_admin_logged_in():
        return redirect(url_for("index", section="admin", lang=request.form.get("lang", "en")))

    lang = request.form.get("lang", "en")
    status = request.form.get("status", "")
    selected_category = request.form.get("category", "")
    search = request.form.get("search", "")

    db = get_db()
    db.execute("UPDATE complaints SET status = ? WHERE id = ?", (status, complaint_id))
    db.commit()
    return redirect(url_for("index", section="admin", lang=lang, category=selected_category, search=search))


@app.get("/complaints/export")
def export_complaints():
    return jsonify(query_complaints())


init_db()

if __name__ == "__main__":
    app.run(debug=True)
