"""whatsapp_utils.py — Twilio WhatsApp messages"""
import logging
logger = logging.getLogger(__name__)

def _client(app):
    sid   = app.config.get('TWILIO_ACCOUNT_SID','')
    token = app.config.get('TWILIO_AUTH_TOKEN','')
    if not sid or not token: return None
    try:
        from twilio.rest import Client
        return Client(sid, token)
    except ImportError:
        logger.warning("[WA] twilio not installed. Run: pip install twilio")
        return None

def _fmt(phone):
    phone = phone.strip().replace(' ','').replace('-','')
    if not phone.startswith('+'): phone = '+91' + phone
    if not phone.startswith('whatsapp:'): phone = 'whatsapp:' + phone
    return phone

def _send(app, to, body):
    if not to: return
    client = _client(app)
    if not client:
        logger.info(f"[WA not configured] To:{to}\n{body}"); return
    try:
        m = client.messages.create(
            from_=app.config['TWILIO_WHATSAPP_FROM'],
            to=_fmt(to), body=body)
        logger.info(f"[WA sent] {m.sid}")
    except Exception as e:
        logger.error(f"[WA error] {e}")

# ── Message functions ──────────────────────────────────────────────────────────

def wa_welcome(app, phone, name):
    _send(app, phone,
        f" *Welcome to MU Portal!*\n\nHi {name} \n"
        f"Your account is ready. Apply for Revaluation & Photocopy from the portal.\n"
        f"_University of Mumbai_")

def wa_application_submitted(app, phone, name, app_type, subject, app_id, fee):
    _send(app, phone,
        f" *Application Submitted*\n\n"
        f"Hi {name},\nYour *{app_type}* application is received.\n\n"
        f" Details:\n"
        f"• App ID: #{app_id}\n"
        f"• Subject: {subject}\n"
        f"• Status:  Applied\n\n"
        f" *Fee Payable: ₹{fee}* (₹200 per paper)\n"
        f"Pay at the college exam section with this App ID.\n\n"
        f"_MU Portal_")

def wa_reval_verified(app, phone, name, subject, app_id, fee):
    _send(app, phone,
        f" *Revaluation Verified!*\n\n"
        f"Hi {name},\nYour revaluation for *{subject}* is verified.\n\n"
        f" App ID: #{app_id}\n"
        f" *Fee: ₹{fee}* — Please pay if not done yet.\n"
        f" Status: Monitoring MU result page...\n\n"
        f"You'll be auto-notified when result is updated! \n"
        f"_MU Portal_")

def wa_result_updated(app, phone, name, subject, result, app_id):
    _send(app, phone,
        f" *Revaluation Result Updated!*\n\n"
        f"Hi {name},\nYour result for *{subject}* is updated.\n\n"
        f" Result: *{result}*\n"
        f" App ID: #{app_id}\n\n"
        f"Check official portal: https://exam.mu.ac.in\n"
        f"_MU Portal_")

def wa_photocopy_verified(app, phone, name, subject, expected_by, app_id, fee):
    _send(app, phone,
        f" *Photocopy Request Verified!*\n\n"
        f"Hi {name},\nYour photocopy for *{subject}* is being processed.\n\n"
        f" App ID: #{app_id}\n"
        f" *Fee: ₹{fee}* — Pay at exam section.\n"
        f" Expected By: {expected_by}\n\n"
        f"You'll get a reminder before the delivery date.\n"
        f"_MU Portal_")

def wa_photocopy_reminder(app, phone, name, subject, expected_by, app_id):
    _send(app, phone,
        f" *Photocopy Delivery Reminder*\n\n"
        f"Hi {name},\nYour photocopy for *{subject}* is expected by *{expected_by}*.\n\n"
        f" App ID: #{app_id}\n\n"
        f"Once received, mark it as received on the portal.\n"
        f"_MU Portal_")

def wa_rexam_reminder(app, phone, name, subject, semester, prn, reminder_num):
    urgency = ["", "", "", ""][min(reminder_num, 3)]
    msg_variants = [
        f"Hi {name}, you have *failed {subject}* after revaluation.\n"
        f" Please fill the *Re-Exam Form* immediately on the MU portal.\n"
        f"Don't miss the deadline!",
        f"Hi {name}, this is *Reminder #{reminder_num}*.\n"
        f"You still need to fill the *Re-Exam Form* for *{subject}*.\n"
        f" Deadlines are approaching — act now!",
        f"Hi {name}, *URGENT REMINDER #{reminder_num}*!\n"
        f"Re-exam form for *{subject}* is still UNFILLED.\n"
        f" Please fill it TODAY to avoid losing your chance.",
    ]
    body_idx = min(reminder_num - 1, len(msg_variants) - 1)
    _send(app, phone,
        f"{urgency} *Re-Exam Form Alert*\n\n"
        f"{msg_variants[body_idx]}\n\n"
        f" Details:\n"
        f"• Subject: {subject}\n"
        f"• Semester: {semester}\n"
        f"• PRN: {prn}\n\n"
        f" mu.ac.in → Student Login → Re-Exam Form\n"
        f"Once filled, mark it done on MU Portal.\n"
        f"_MU Portal_")
