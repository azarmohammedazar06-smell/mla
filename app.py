from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

WHATSAPP_NUMBER = "919483927300"
DATA_DIR = Path("data")
UPLOAD_DIR = Path("static/uploads")
COMPLAINTS_FILE = DATA_DIR / "complaints.json"

MAX_IMAGE_BYTES = int(1.6 * 1024 * 1024)
MAX_VIDEO_BYTES = int(5 * 1024 * 1024)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".ogg"}

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

LANG_DATA = {
    "en": {
        "title": "YOUR MLA — Public Help Portal",
        "subtitle": "Report public issues — saved on server & sent via WhatsApp",
        "report": "Report an Issue",
        "about": "About / Plans",
        "list": "View All Complaints",
        "export": "Export JSON",
        "reportTitle": "Report a Public Issue",
        "reportDesc": "Fill details below — you can save & send via WhatsApp.",
        "category": "Issue Category",
        "desc": "Describe the Issue",
        "age": "Your Age Group",
        "contactMethod": "Preferred Contact Method (optional)",
        "contactInfo": "Contact Info (optional)",
        "uploadImg": "Upload Image (optional)",
        "uploadVid": "Upload Video (optional)",
        "submit": "Save & Register Your Complaint",
        "aboutTitle": "About",
        "aboutText": "This portal helps citizens report public issues directly to MLA’s office through WhatsApp.",
        "noComplaints": "No complaints yet.",
        "saved": "Complaint saved. Open WhatsApp?",
        "status": "Status",
        "statusOptions": ["New", "In Review", "Resolved"],
    }
}

CATEGORIES = ["Health", "Agriculture", "Education", "Infrastructure", "Other"]
AGE_GROUPS = ["18–30", "30–45", "45+"]


def load_complaints() -> list[dict]:
    if not COMPLAINTS_FILE.exists():
        return []
    try:
        return json.loads(COMPLAINTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_complaints(items: list[dict]) -> None:
    COMPLAINTS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def validate_upload(file_storage, allowed_extensions, max_bytes):
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


def save_upload(file_storage, prefix: str):
    if not file_storage or not file_storage.filename:
        return None

    safe_name = secure_filename(file_storage.filename)
    filename = f"{prefix}_{secrets.token_hex(4)}_{safe_name}"

    target = UPLOAD_DIR / filename
    file_storage.save(target)

    return f"uploads/{filename}"


@app.route("/")
def index():

    lang = request.args.get("lang", "en")
    section = request.args.get("section", "form")

    complaints = load_complaints() if section == "list" else []

    return render_template(
        "index.html",
        t=LANG_DATA["en"],
        lang=lang,
        section=section,
        complaints=complaints,
    )


@app.route("/complaints", methods=["POST"])
def submit_complaint():

    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    if not category or not description:
        return redirect(url_for("index"))

    image = request.files.get("image")
    video = request.files.get("video")

    complaint = {
        "id": secrets.token_hex(4),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "description": description,
        "age_group": request.form.get("age_group", ""),
        "contact_method": request.form.get("contact_method", ""),
        "contact_info": request.form.get("contact_info", ""),
        "status": "New",
        "image_path": save_upload(image, "img"),
        "video_path": save_upload(video, "vid"),
    }

    items = load_complaints()
    items.insert(0, complaint)

    save_complaints(items)

    message = quote(
        f"Complaint ID: {complaint['id']}\n"
        f"Category: {complaint['category']}\n"
        f"Description: {complaint['description']}"
    )

    wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={message}"

    return redirect(wa_url)


@app.route("/complaints/export")
def export_complaints():
    return jsonify(load_complaints())


if __name__ == "__main__":
    app.run(debug=True)