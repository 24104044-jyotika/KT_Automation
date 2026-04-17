import os

class Config:
    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # ── Database ──────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Email (Brevo Transactional Email API) ─────────────────────────────
    BREVO_API_KEY        = os.environ.get('BREVO_API_KEY')
    BREVO_SENDER_EMAIL   = os.environ.get('BREVO_SENDER_EMAIL')
    BREVO_SENDER_NAME    = os.environ.get('BREVO_SENDER_NAME', 'MU Portal')

    # ── WhatsApp (Twilio) ─────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID   = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN    = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', '+14155238886')

    # ── Supabase ──────────────────────────────────────────────────────────
    SUPABASE_URL         = os.environ.get('SUPABASE_URL')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    # ── File Uploads ──────────────────────────────────────────────────────
    UPLOAD_FOLDER        = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH   = 10 * 1024 * 1024   # 10 MB
    ALLOWED_EXTENSIONS   = {'png', 'jpg', 'jpeg', 'pdf'}

    # ── Scheduler ─────────────────────────────────────────────────────────
    SCHEDULER_INTERVAL_HOURS = int(os.environ.get('SCHEDULER_INTERVAL_HOURS', 6))
    MU_RESULT_BASE_URL        = os.environ.get(
        'MU_RESULT_BASE_URL',
        'https://exam.mu.ac.in/ExamResult/frmResult.aspx'
    )

    @staticmethod
    def wa_cfg(app):
        """Return WhatsApp config dict for whatsapp_utils functions."""
        return {
            'sid':   app.config['TWILIO_ACCOUNT_SID'],
            'token': app.config['TWILIO_AUTH_TOKEN'],
            'from':  app.config['TWILIO_WHATSAPP_FROM'],
        }
