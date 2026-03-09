# MLA Public Help Portal (Python + Flask + SQLite)

A modern public-help portal with bilingual support, complaint tracking, and admin workflows.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask
python app.py
```

Open: http://127.0.0.1:5000

## New Features

- SQLite database (`data/portal.db`) for persistent complaints and users
- Login system for admin users
- Admin panel with complaint status management
- Auto-open WhatsApp message after complaint submission
- Image preview before upload
- Modern UI inspired by clean marketplace/government portals
- JSON export endpoint at `/complaints/export`

## Admin Credentials

By default:
- Username: `admin`
- Password: `admin123`

Override with environment variables:

```bash
export ADMIN_USERNAME="your_admin"
export ADMIN_PASSWORD="strong_password"
```
