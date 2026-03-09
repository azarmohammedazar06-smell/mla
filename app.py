from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

WHATSAPP_NUMBER = "919483927300"
DATA_DIR = Path("data")
UPLOAD_DIR = Path("static/uploads")
COMPLAINTS_FILE = DATA_DIR / "complaints.json"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

LANG_DATA = {
    "en": {
        "title": "YOUR MLA — Public Help Portal",
        "subtitle": "Report public issues — saved on server & sent via WhatsApp",
        "report": "Report an Issue",
        "about": "About / Plans",
        "list": "View All Complaints",
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
    },
    "kn": {
        "title": "ನಿಮ್ಮ ಶಾಸಕರು — ಸಾರ್ವಜನಿಕ ಸಹಾಯ ಪೋರ್ಟಲ್",
        "subtitle": "ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆಗಳನ್ನು ವರದಿ ಮಾಡಿ — ಸರ್ವರ್‌ನಲ್ಲಿ ಉಳಿಸಿ ಮತ್ತು ವಾಟ್ಸಾಪ್ ಮೂಲಕ ಕಳುಹಿಸಿ",
        "report": "ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ",
        "about": "ಬಗ್ಗೆ / ಯೋಜನೆಗಳು",
        "list": "ಎಲ್ಲ ದೂರುಗಳನ್ನು ನೋಡಿ",
        "reportTitle": "ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ",
        "reportDesc": "ಕೆಳಗಿನ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ — ನೀವು ಉಳಿಸಿ ವಾಟ್ಸಾಪ್ ಮೂಲಕ ಕಳುಹಿಸಬಹುದು.",
        "category": "ಸಮಸ್ಯೆಯ ವರ್ಗ",
        "desc": "ಸಮಸ್ಯೆಯನ್ನು ವಿವರಿಸಿ",
        "age": "ನಿಮ್ಮ ವಯೋಮಾನದ ಗುಂಪು",
        "contactMethod": "ಆದ್ಯತೆಯ ಸಂಪರ್ಕ ವಿಧಾನ (ಐಚ್ಛಿಕ)",
        "contactInfo": "ಸಂಪರ್ಕ ಮಾಹಿತಿ (ಐಚ್ಛಿಕ)",
        "uploadImg": "ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (ಐಚ್ಛಿಕ)",
        "uploadVid": "ವೀಡಿಯೊ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (ಐಚ್ಛಿಕ)",
        "submit": "ಉಳಿಸಿ ಮತ್ತು ವಾಟ್ಸಾಪ್ ತೆರೆಯಿರಿ",
        "aboutTitle": "ಬಗ್ಗೆ",
        "aboutText": "ಈ ಪೋರ್ಟಲ್ ನಾಗರಿಕರಿಗೆ ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆಗಳನ್ನು ನೇರವಾಗಿ ಶಾಸಕರ ಕಚೇರಿಗೆ ವಾಟ್ಸಾಪ್ ಮೂಲಕ ವರದಿ ಮಾಡಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
        "noComplaints": "ಇನ್ನೂ ಯಾವುದೇ ದೂರುಗಳಿಲ್ಲ.",
        "saved": "ದೂರು ಉಳಿಸಲಾಗಿದೆ. ವಾಟ್ಸಾಪ್ ತೆರೆಯುವಿರಾ?",
    },
}


def load_complaints() -> list[dict]:
    if not COMPLAINTS_FILE.exists():
        return []
    try:
        return json.loads(COMPLAINTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_complaints(items: list[dict]) -> None:
    COMPLAINTS_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def save_upload(file_storage, prefix: str) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    safe_name = secure_filename(file_storage.filename)
    filename = f"{prefix}_{secrets.token_hex(4)}_{safe_name}"
    target = UPLOAD_DIR / filename
    file_storage.save(target)
    return f"uploads/{filename}"


@app.get("/")
def index():
    lang = request.args.get("lang", "en")
    if lang not in LANG_DATA:
        lang = "en"
    section = request.args.get("section", "form")
    wa = request.args.get("wa", "")
    complaints = load_complaints() if section == "list" else []
    return render_template(
        "index.html",
        t=LANG_DATA[lang],
        lang=lang,
        section=section,
        complaints=complaints,
        wa=wa,
    )


@app.post("/complaints")
def submit_complaint():
    lang = request.form.get("lang", "en")
    if lang not in LANG_DATA:
        lang = "en"

    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    if not category or not description:
        return redirect(url_for("index", lang=lang, section="form"))

    complaint = {
        "id": secrets.token_hex(4),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "description": description,
        "age_group": request.form.get("age_group", "").strip(),
        "contact_method": request.form.get("contact_method", "").strip(),
        "contact_info": request.form.get("contact_info", "").strip(),
        "image_path": save_upload(request.files.get("image"), "img"),
        "video_path": save_upload(request.files.get("video"), "vid"),
    }

    items = load_complaints()
    items.insert(0, complaint)
    save_complaints(items)

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
    msg = "\n".join(lines)
    wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={msg}"

    return redirect(url_for("index", lang=lang, section="list", wa=wa_url))


if __name__ == "__main__":
    app.run(debug=True)
