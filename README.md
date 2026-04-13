# MU Portal — KT Revaluation & Photocopy Tracker

Full-stack Flask portal for Mumbai University students with automated Email + WhatsApp notifications.

---

##  Quick Start

```bash
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:5000
```

Default admin login: `admin@mu.ac.in` / `admin123`

---

##  Email Setup (Gmail)

1. Go to **Google Account → Security → 2-Step Verification → App Passwords**
2. Generate a 16-character App Password for "Mail"
3. Open `config.py` and fill in:

```python
MAIL_USERNAME = 'yourname@gmail.com'
MAIL_PASSWORD = 'xxxx xxxx xxxx xxxx'   # 16-char App Password
MAIL_DEFAULT_SENDER = 'MU Portal <yourname@gmail.com>'
```

---

##  WhatsApp Setup (Twilio Sandbox — Free)

### Step 1: Create Twilio Account
- Sign up free at https://www.twilio.com
- Free trial gives ~$15 credit (enough for hundreds of messages)

### Step 2: Get Credentials
- Go to **Twilio Console → Account Info**
- Copy your **Account SID** and **Auth Token**

### Step 3: Activate WhatsApp Sandbox
- Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
- Note the sandbox **join word** (e.g. "join blue-mango")

### Step 4: Update config.py
```python
TWILIO_ACCOUNT_SID   = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN    = 'your_auth_token_here'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'   # Twilio sandbox number
```

### Step 5: Students Must Join Once
Each student sends this WhatsApp message once:
```
join <sandbox-word>
```
To number: **+1 415 523 8886**

After this, they receive all automated notifications automatically.

---

##  Notification Events

| Event | Email | WhatsApp |
|-------|-------|----------|
| Registration |  |  |
| Application submitted (Reval/Photocopy) |  |  |
| Admin verifies revaluation |  |  |
| Revaluation result updated |  |  |
| Admin verifies photocopy |  |  |
| Photocopy delivery reminder (3 days before) |  |  |
| Auto-detected MU page change (scheduler) |  |  |

---

##  Project Structure

```
mu_portal/
├── app.py                   # Flask app, routes, models
├── config.py                # Email & WhatsApp credentials
├── email_utils.py           # HTML email templates
├── whatsapp_utils.py        # Twilio WhatsApp messages
├── scheduler.py             # Background monitoring jobs
├── ocr_utils.py             # OCR result simplification
├── requirements.txt
├── static/css/main.css
├── static/js/main.js
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html         ← includes phone number field
    ├── student_dashboard.html
    ├── student_profile.html  ← update WhatsApp number anytime
    ├── apply_revaluation.html
    ├── apply_photocopy.html
    ├── admin_dashboard.html
    ├── admin_reval_list.html
    ├── admin_photo_list.html
    └── admin_students.html
```

##  All URLs

| Page | URL |
|------|-----|
| Login | http://127.0.0.1:5000/login |
| Register | http://127.0.0.1:5000/register |
| Student Dashboard | http://127.0.0.1:5000/student/dashboard |
| Student Profile | http://127.0.0.1:5000/student/profile |
| Admin Dashboard | http://127.0.0.1:5000/admin/dashboard |
| Admin Revaluation | http://127.0.0.1:5000/admin/revaluation |
| Admin Photocopy | http://127.0.0.1:5000/admin/photocopy |
| Admin Students | http://127.0.0.1:5000/admin/students |

Shortcuts: `/admin` and `/student` also redirect correctly.
