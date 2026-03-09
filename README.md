# MLA Public Help Portal (Python)

This project is now a **Python Flask web app** version of the MLA Public Help Portal.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask
python app.py
```

Open: http://127.0.0.1:5000

## Features

- English / Kannada language toggle
- Report a public issue with optional image and video upload
- Complaints are saved on the server in `data/complaints.json`
- Uploaded files are saved to `static/uploads/`
- After submit, user is prompted to open WhatsApp with a prefilled message
