import os

class Config:
    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mu-portal-secret-key-2024')

    # ── Database ──────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres.gjnnrbbbqcpgarqpsjuk:Jyotika2611@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

    # ── Email (Flask-Mail via Gmail) ──────────────────────────────────────
    # Step 1: Enable 2-Factor Auth on your Gmail account
    # Step 2: Go to Google Account → Security → App Passwords → Generate
    # Step 3: Paste the 16-char app password below
    MAIL_SERVER          = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
    MAIL_PORT            = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS         = True
    MAIL_USERNAME        = os.environ.get('MAIL_USERNAME', 'jyotika.rao2006@gmail.com')   
    MAIL_PASSWORD        = os.environ.get('MAIL_PASSWORD', 'pwvdfjuozhrrkrom')   
    MAIL_DEFAULT_SENDER  = os.environ.get('MAIL_DEFAULT_SENDER', 'MU Portal <noreply@mu.ac.in>')

    # ── WhatsApp (Twilio) ─────────────────────────────────────────────────
    # Step 1: Sign up at https://www.twilio.com (free trial available)
    # Step 2: Go to Messaging → Try it out → Send a WhatsApp message
    # Step 3: Note your Account SID, Auth Token, and the sandbox number
    # Step 4: Students must send "join <sandbox-word>" to +1 415 523 8886
    TWILIO_ACCOUNT_SID   = os.environ.get('TWILIO_ACCOUNT_SID',  '')
    TWILIO_AUTH_TOKEN    = os.environ.get('TWILIO_AUTH_TOKEN',   '')
    TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', '+14155238886')  # Twilio sandbox

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
