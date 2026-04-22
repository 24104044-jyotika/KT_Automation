"""email_utils.py — HTML email templates via Brevo Transactional Email API (HTTP)
Replaces Flask-Mail/SMTP entirely — works on Railway with no port issues.
"""
import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

_STYLE = """
body{font-family:'Segoe UI',sans-serif;background:#eef2f0;margin:0;padding:32px}
.wrap{max-width:560px;margin:0 auto;background:#fff;border-radius:16px;
      box-shadow:0 4px 24px rgba(26,138,122,.12);overflow:hidden}
.header{background:#1a8a7a;padding:28px 36px;color:#fff}
.header h1{margin:0;font-size:1.4rem;font-weight:700}
.header p{margin:6px 0 0;opacity:.85;font-size:.9rem}
.body{padding:28px 36px}
.body p{color:#4a6360;line-height:1.7;font-size:.92rem}
.fee-box{background:#e8f5f3;border:2px solid #1a8a7a;border-radius:10px;
         padding:16px 20px;margin:16px 0;text-align:center}
.fee-box .amount{font-size:2rem;font-weight:700;color:#1a8a7a}
.fee-box .label{font-size:.82rem;color:#4a6360;margin-top:4px}
.detail-box{background:#e8f5f3;border-radius:10px;padding:16px 20px;margin:16px 0}
.detail-box h3{margin:0 0 10px;font-size:.85rem;color:#136b5e;text-transform:uppercase}
.detail-box table{width:100%;border-collapse:collapse;font-size:.88rem}
.detail-box td{padding:5px 0;color:#1a2e2a}
.detail-box td:first-child{color:#4a6360;width:140px}
.warning-box{background:#fff3e0;border:1px solid #fde68a;border-radius:10px;
             padding:16px 20px;margin:16px 0}
.warning-box h3{color:#92400e;margin:0 0 8px;font-size:.9rem}
.urgent-box{background:#fce8e8;border:2px solid #e05252;border-radius:10px;
            padding:16px 20px;margin:16px 0}
.urgent-box h3{color:#c0392b;margin:0 0 8px;font-size:.95rem}
.footer{background:#f5f8f7;padding:16px 36px;font-size:.78rem;color:#7a9997;border-top:1px solid #d0e4e1}
"""


def _send(subject, recipients, html_body):
    """
    Send email via Brevo Transactional Email API (HTTP POST).
    `recipients` can be a single email string or a list of email strings.
    """
    api_key = current_app.config.get('BREVO_API_KEY')
    sender_email = current_app.config.get('BREVO_SENDER_EMAIL')
    sender_name = current_app.config.get('BREVO_SENDER_NAME', 'MU Portal')

    if not api_key:
        logger.warning(f"[EMAIL not configured] BREVO_API_KEY missing | To:{recipients} | {subject}")
        print(f"[EMAIL not configured] To:{recipients} | {subject}")
        return

    if isinstance(recipients, str):
        recipients = [recipients]

    to_list = [{"email": addr} for addr in recipients]

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": to_list,
        "subject": subject,
        "htmlContent": html_body,
    }

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        print(f"[EMAIL sent] {recipients} | messageId: {response.json().get('messageId','')}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[EMAIL HTTP error] {e} | response: {e.response.text if e.response else 'N/A'}")
        print(f"[EMAIL HTTP error] {e}")
    except Exception as e:
        logger.error(f"[EMAIL error] {e}")
        print(f"[EMAIL error] {e}")


# ─── NOTE: All functions below keep the same signatures as before ─────────────
# The only change is: `mail` parameter is accepted but IGNORED (kept for
# backward compatibility so you don't need to change any call sites in app.py
# or scheduler.py).
# ─────────────────────────────────────────────────────────────────────────────

def send_welcome(mail, name, email):
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header"><h1>Welcome to MU Automation Portal</h1><p>Your account is ready</p></div>
    <div class="body"><p>Hi <strong>{name}</strong>,</p>
    <p>Welcome! You can now apply for Revaluation &amp; Photocopy requests and track them.</p>
    </div><div class="footer">University of Mumbai Student Portal</div></div></body></html>"""
    _send("Welcome to MU Automation Portal!", [email], html)


def send_application_submitted(mail, name, email, app_type, subject, app_id, fee):
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header"><h1>Application Submitted</h1><p>{app_type} request received</p></div>
    <div class="body">
    <p>Hi <strong>{name}</strong>,</p>
    <p>Your <strong>{app_type}</strong> application has been submitted successfully.</p>
    <div class="detail-box"><h3>Application Details</h3><table>
    <tr><td>App ID</td><td><strong>#{app_id}</strong></td></tr>
    <tr><td>Subject</td><td>{subject}</td></tr>
    <tr><td>Status</td><td>Applied — Pending Verification</td></tr>
    </table></div>
    <div class="fee-box">
    <div class="amount">₹{fee}</div>
    <div class="label">Fee Payable (₹200 per paper)<br>Pay at the college exam section with App ID #{app_id}</div>
    </div>
    <p>You will be notified once admin verifies your request.</p>
    </div><div class="footer">University of Mumbai Student Portal</div></div></body></html>"""
    _send(f"{app_type} Application Submitted – ₹{fee} Fee", [email], html)


def send_reval_verified(mail, name, email, subject, app_id, fee):
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header"><h1>Revaluation Verified</h1><p>Monitoring started</p></div>
    <div class="body">
    <p>Hi <strong>{name}</strong>,</p>
    <p>Your revaluation application has been <strong>verified</strong> by admin.</p>
    <div class="detail-box"><h3>Details</h3><table>
    <tr><td>App ID</td><td><strong>#{app_id}</strong></td></tr>
    <tr><td>Subject</td><td>{subject}</td></tr>
    <tr><td>Status</td><td>Monitoring MU Result Page</td></tr>
    </table></div>
    <div class="fee-box">
    <div class="amount">₹{fee}</div>
    <div class="label">Fee Payable (₹200 per paper)<br>Please pay if not done yet.</div>
    </div>
    <p>The system will auto-notify you the moment your result is updated. No action needed!</p>
    </div><div class="footer">University of Mumbai Student Portal</div></div></body></html>"""
    _send(f"Revaluation Verified – Now Monitoring | {subject}", [email], html)


def send_result_updated(mail, name, email, subject, result, app_id):
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header"><h1>Revaluation Result Updated!</h1><p>Check your result below</p></div>
    <div class="body">
    <p>Hi <strong>{name}</strong>,</p>
    <p>Your revaluation result for <strong>{subject}</strong> has been updated!</p>
    <div class="detail-box"><h3>Result Details</h3><table>
    <tr><td>App ID</td><td><strong>#{app_id}</strong></td></tr>
    <tr><td>Subject</td><td>{subject}</td></tr>
    <tr><td>Result</td><td><strong style="color:#1a8a7a;font-size:1.1rem">{result}</strong></td></tr>
    </table></div>
    <p>Please verify on the official MU exam portal as well.</p>
    </div><div class="footer">University of Mumbai Student Portal</div></div></body></html>"""
    _send(f"Revaluation Result Updated – {subject}", [email], html)


def send_photocopy_verified(mail, name, email, subject, expected_by, app_id, fee):
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header"><h1>Photocopy Request Verified</h1><p>Processing started</p></div>
    <div class="body">
    <p>Hi <strong>{name}</strong>,</p>
    <p>Your photocopy request has been verified and is now being processed.</p>
    <div class="detail-box"><h3>Details</h3><table>
    <tr><td>App ID</td><td><strong>#{app_id}</strong></td></tr>
    <tr><td>Subject</td><td>{subject}</td></tr>
    <tr><td>Expected By</td><td>{expected_by}</td></tr>
    </table></div>
    <div class="fee-box">
    <div class="amount">₹{fee}</div>
    <div class="label">Fee Payable (₹200 per paper)<br>Pay at the college exam section.</div>
    </div>
    <p>Photocopies take 15–20 days. You'll get a reminder before delivery.</p>
    </div><div class="footer">University of Mumbai Student Portal</div></div></body></html>"""
    _send(f"Photocopy Verified – ₹{fee} Fee | {subject}", [email], html)


def send_photocopy_reminder(mail, name, email, subject, expected_by, app_id):
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header"><h1>Photocopy Delivery Reminder</h1></div>
    <div class="body">
    <p>Hi <strong>{name}</strong>,</p>
    <p>Your photocopy for <strong>{subject}</strong> is expected by <strong>{expected_by}</strong>.</p>
    <p>Once received, please mark it as received on the portal.</p>
    </div><div class="footer">University of Mumbai Student Portal</div></div></body></html>"""
    _send(f"Photocopy Reminder – {subject}", [email], html)


def send_rexam_reminder(mail, name, email, subject, semester, prn, reminder_num):
    urgency_color = ["#e09820", "#c05621", "#e05252", "#c0392b"][min(reminder_num - 1, 3)]
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header" style="background:{urgency_color}">
    <h1>Re-Exam Form Alert – Reminder #{reminder_num}</h1>
    <p>Action required: Fill the re-exam form</p></div>
    <div class="body">
    <p>Hi <strong>{name}</strong>,</p>
    <div class="urgent-box">
    <h3>You Failed {subject} After Revaluation</h3>
    <p style="margin:0;color:#c0392b;font-size:.9rem">
    You must fill the <strong>Re-Exam (KT) Form</strong> on the MU portal before the deadline.
    Missing this will result in losing your chance to appear in the re-exam.
    </p></div>
    <div class="detail-box"><h3>Details</h3><table>
    <tr><td>Subject</td><td><strong>{subject}</strong></td></tr>
    <tr><td>Semester</td><td>{semester}</td></tr>
    <tr><td>PRN</td><td>{prn}</td></tr>
    <tr><td>Reminder</td><td>#{reminder_num}</td></tr>
    </table></div>
    <div class="warning-box">
    <h3>Steps to Fill Re-Exam Form</h3>
    <ol style="color:#92400e;font-size:.88rem;margin:0;padding-left:18px;line-height:1.8">
    <li>Visit <strong>mu.ac.in</strong> → Student Login</li>
    <li>Go to Exam → Re-Exam / KT Form</li>
    <li>Select subject and pay the fee</li>
    <li>Submit and download acknowledgement</li>
    <li>Mark as done on MU Portal</li>
    </ol></div>
    </div><div class="footer">University of Mumbai Student Portal — This is an automated reminder.</div>
    </div></body></html>"""
    _send(f"Re-Exam Form Reminder #{reminder_num} – {subject}", [email], html)


def send_password_reset(mail, name, email, token):
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    reset_url = f"{base_url}/reset-password/{token}"
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header"><h1>Password Reset Request</h1><p>Reset your MU Portal password</p></div>
    <div class="body">
    <p>Hi <strong>{name}</strong>,</p>
    <p>We received a request to reset your password. Click the button below to create a new password.</p>
    <div style="text-align:center;margin:24px 0">
      <a href="{reset_url}" style="background:#1a8a7a;color:white;padding:14px 28px;
         border-radius:8px;text-decoration:none;font-weight:700;font-size:0.95rem;
         display:inline-block">Reset My Password</a>
    </div>
    <div class="warning-box">
      <h3>Important</h3>
      <p>This link expires in <strong>1 hour</strong>. If you didn't request this, ignore this email — your password won't change.</p>
    </div>
    <p style="font-size:0.82rem;color:#7a9997">Paste this link in your browser:<br>
    <span style="color:#1a8a7a;word-break:break-all">{reset_url}</span></p>
    </div><div class="footer">University of Mumbai Student Portal</div></div></body></html>"""
    _send("Reset Your MU Portal Password", [email], html)


def send_login_otp(mail, name, email, otp_code):
    html = f"""<html><head><style>
    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 40px; border: 1px solid #ddd; }}
    .header {{ border-bottom: 2px solid #1a8a7a; padding-bottom: 20px; margin-bottom: 30px; }}
    .header h1 {{ margin: 0; color: #1a8a7a; font-size: 24px; }}
    .header p {{ margin: 5px 0 0; color: #666; font-size: 14px; }}
    .content {{ color: #333; line-height: 1.6; font-size: 14px; }}
    .content p {{ margin: 0 0 15px; }}
    .otp-box {{ background-color: #f0f8f7; border-left: 4px solid #1a8a7a; padding: 20px; margin: 25px 0; text-align: center; }}
    .otp-code {{ font-size: 32px; font-weight: bold; color: #1a8a7a; letter-spacing: 6px; font-family: 'Courier New', monospace; }}
    .otp-validity {{ color: #666; font-size: 12px; margin-top: 10px; }}
    .security-warning {{ background-color: #fff8f0; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; font-size: 13px; }}
    .security-warning strong {{ color: #ff9800; }}
    .footer {{ border-top: 1px solid #ddd; margin-top: 30px; padding-top: 20px; text-align: center; color: #888; font-size: 12px; }}
    </style></head><body>
    <div class="container">
        <div class="header">
            <h1>Login Verification Code</h1>
            <p>MU Automation Portal</p>
        </div>
        <div class="content">
            <p>Hello <strong>{name}</strong>,</p>
            <p>You have requested to access your account. Please use the One-Time Password (OTP) below to complete your login:</p>
            <div class="otp-box">
                <div class="otp-code">{otp_code}</div>
                <div class="otp-validity">Valid for 5 minutes only</div>
            </div>
            <p style="margin-top: 25px;">If you did not attempt to log in, please disregard this email and verify your account security immediately.</p>
            <div class="security-warning">
                <strong>Security Notice:</strong> Never share this code with anyone. Our support staff will never ask you for this code via email or phone.
            </div>
            <p>Best regards,<br><strong>MU Automation Portal Team</strong></p>
        </div>
        <div class="footer">
            <p>© University of Mumbai Student Portal | This is an automated message, please do not reply</p>
        </div>
    </div>
    </body></html>"""
    _send("Your MU Portal Login Verification Code", [email], html)


def send_exam_form_reminder(mail, name, email, subject, semester, exam_year, seat, mail_count):
    """Remind a failed student to fill the KT/re-exam form."""
    urgency_colors = ['#e09820', '#c05621', '#e05252', '#c0392b']
    color = urgency_colors[min(mail_count - 1, 3)]
    ordinal = {1: '1st', 2: '2nd', 3: '3rd'}.get(mail_count, f'{mail_count}th')
    html = f"""<html><head><style>{_STYLE}</style></head><body><div class="wrap">
    <div class="header" style="background:{color}">
        <h1>Exam Form Filing Reminder — {ordinal} Notice</h1>
        <p>A.P. Shah Institute of Technology | Mumbai University</p>
    </div>
    <div class="body">
        <p>Dear <strong>{name}</strong>,</p>
        <p>Our records from the latest Mumbai University result sheet show that you have
        <strong>not yet filed the re-exam (KT) form</strong> for the following subject:</p>

        <div class="urgent-box">
            <h3>Subject: {subject}</h3>
            <p style="margin:0;color:#c0392b;font-size:.9rem">
                Semester <strong>{semester}</strong> &nbsp;·&nbsp; Exam Year: <strong>{exam_year or 'N/A'}</strong>
                {f'&nbsp;·&nbsp; Seat/PRN: <strong>{seat}</strong>' if seat else ''}
            </p>
        </div>

        <div class="warning-box">
            <h3>Steps to File the Re-Exam Form</h3>
            <ol style="color:#92400e;font-size:.88rem;margin:0;padding-left:18px;line-height:1.9">
                <li>Visit <strong>mu.ac.in</strong> → Student Login</li>
                <li>Go to <strong>Exam → Re-Exam / KT Form</strong></li>
                <li>Select subject <strong>{subject}</strong> and pay the required fee</li>
                <li>Submit and download your acknowledgement slip</li>
                <li>Submit the slip at the exam section of APSIT</li>
            </ol>
        </div>

        <p style="color:#c0392b;font-weight:600;font-size:.92rem">
            Missing the deadline means losing your chance to appear in the re-exam.
            Please act immediately.
        </p>

        <p>If you have already filed the form, please ignore this email or inform the
        examination section at APSIT so your record can be updated.</p>
    </div>
    <div class="footer">
        A.P. Shah Institute of Technology, Mumbai &nbsp;|&nbsp; MU Automation Portal &nbsp;|&nbsp;
        This is an automated reminder — Reminder #{mail_count}
    </div>
    </div></body></html>"""
    _send(
        f"[APSIT] Exam Form Not Filed — {subject} (Sem {semester}) — Reminder #{mail_count}",
        [email],
        html
    )
