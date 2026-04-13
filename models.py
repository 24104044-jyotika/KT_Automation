
"""
models.py — SQLAlchemy ORM Models
Connects to Supabase via PostgreSQL connection string.
Compatible with all existing app.py routes.
"""
 
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
 
 
# ─── Helper ───────────────────────────────────────────────────────────────────
 
def get_utc_now():
    return datetime.utcnow()
 
 
# ─── User ─────────────────────────────────────────────────────────────────────
 
class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = (
        db.Index('idx_email', 'email'),
        db.Index('idx_role_created', 'role', 'created_at'),
    )
 
    id                  = db.Column(db.Integer, primary_key=True)
 
    # Profile
    name                = db.Column(db.String(100), nullable=False)
    email               = db.Column(db.String(150), unique=True, nullable=False)
    password_hash       = db.Column(db.String(255), nullable=False)
    phone               = db.Column(db.String(20), default='')
    role                = db.Column(db.String(20), default='student', index=True)
    caste_certificate   = db.Column(db.String(300), default='')
 
    # Academic
    department          = db.Column(db.String(100), default='')
    semester            = db.Column(db.String(10), default='')
    prn_number          = db.Column(db.String(50), unique=True, nullable=True)
 
    # Timestamps
    created_at          = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    updated_at          = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    last_login          = db.Column(db.DateTime, nullable=True)
 
    # Password Reset
    reset_token         = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry  = db.Column(db.DateTime, nullable=True)
 
    # OTP
    otp_code            = db.Column(db.String(6), nullable=True)
    otp_expiry          = db.Column(db.DateTime, nullable=True)
    otp_attempts        = db.Column(db.Integer, default=0)
 
    # Relationships
    reval_apps      = db.relationship('RevaluationApplication', backref='student',
                                      lazy='select', cascade='all, delete-orphan')
    photo_apps      = db.relationship('PhotocopyApplication', backref='student',
                                      lazy='select', cascade='all, delete-orphan')
    notifications   = db.relationship('Notification', backref='user',
                                      lazy='select', cascade='all, delete-orphan')
    result_uploads  = db.relationship('ResultUpload', backref='student',
                                      lazy='select', cascade='all, delete-orphan')
    rexam_reminders = db.relationship('ReExamReminder', backref='student',
                                      lazy='select', cascade='all, delete-orphan')
    failed_records  = db.relationship('FailedStudentRecord', backref='user',
                                      lazy='select')
    file_uploads    = db.relationship('FileUpload', backref='uploaded_by',
                                      lazy='select', cascade='all, delete-orphan')
 
    # ── Password ──────────────────────────────────────────────────────────────
 
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
 
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
 
    # ── OTP ───────────────────────────────────────────────────────────────────
 
    def set_otp(self, otp_code):
        self.otp_code     = otp_code
        self.otp_expiry   = datetime.utcnow() + timedelta(minutes=5)
        self.otp_attempts = 0
 
    def verify_otp(self, otp_code):
        if not self.otp_code or not self.otp_expiry:
            return False
        if self.otp_expiry < datetime.utcnow():
            self.clear_otp()
            return False
        if self.otp_code == otp_code:
            self.clear_otp()
            return True
        self.otp_attempts += 1
        if self.otp_attempts >= 3:
            self.clear_otp()
        return False
 
    def clear_otp(self):
        self.otp_code     = None
        self.otp_expiry   = None
        self.otp_attempts = 0
 
    # ── Password Reset ────────────────────────────────────────────────────────
 
    def set_reset_token(self, token_string):
        self.reset_token        = token_string
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
 
    def verify_reset_token(self, token_string):
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token_expiry < datetime.utcnow():
            return False
        return self.reset_token == token_string
 
    def clear_reset_token(self):
        self.reset_token        = None
        self.reset_token_expiry = None
 
    # ── Flask-Login ───────────────────────────────────────────────────────────
 
    @property
    def is_active(self):        return True
    @property
    def is_authenticated(self): return True
    @property
    def is_anonymous(self):     return False
    def get_id(self):           return str(self.id)
 
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
 
 
# ─── AcademicSemester ─────────────────────────────────────────────────────────
 
class AcademicSemester(db.Model):
    __tablename__ = 'academic_semester'
    __table_args__ = (
        db.UniqueConstraint('year', 'semester', name='uq_year_semester'),
        db.Index('idx_active', 'is_active'),
    )
 
    id         = db.Column(db.Integer, primary_key=True)
    year       = db.Column(db.String(20), nullable=False)
    semester   = db.Column(db.String(20), nullable=False)
    is_active  = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
 
    def __repr__(self):
        return f'<Semester {self.year} - Sem {self.semester}>'
 
 
# ─── FileUpload ───────────────────────────────────────────────────────────────
 
class FileUpload(db.Model):
    __tablename__ = 'file_upload'
    __table_args__ = (
        db.Index('idx_user_type', 'user_id', 'file_type'),
        db.Index('idx_uploaded_at', 'uploaded_at'),
    )
 
    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    stored_filename   = db.Column(db.String(300), nullable=False)
    file_type         = db.Column(db.String(50), nullable=False)
    file_size         = db.Column(db.Integer)
    mime_type         = db.Column(db.String(100))
    extracted_text    = db.Column(db.Text, nullable=True)
    uploaded_at       = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    deleted_at        = db.Column(db.DateTime, nullable=True)
 
    def __repr__(self):
        return f'<FileUpload {self.original_filename} ({self.file_type})>'
 
 
# ─── RevaluationApplication ───────────────────────────────────────────────────
 
class RevaluationApplication(db.Model):
    __tablename__ = 'revaluation_application'
    __table_args__ = (
        db.Index('idx_student_status', 'student_id', 'status'),
        db.Index('idx_prn_year', 'prn_number', 'exam_year'),
    )
 
    id                = db.Column(db.Integer, primary_key=True)
    student_id        = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subject_name      = db.Column(db.String(200), nullable=False)
    exam_year         = db.Column(db.String(20), nullable=False)
    semester          = db.Column(db.String(20), nullable=False)
    prn_number        = db.Column(db.String(50), nullable=False)
    num_papers        = db.Column(db.Integer, default=1)
    fee_amount        = db.Column(db.Integer, default=200)
    marksheet_file    = db.Column(db.String(300), nullable=True)
    marksheet_file_id = db.Column(db.Integer, db.ForeignKey('file_upload.id', ondelete='SET NULL'), nullable=True)
    status            = db.Column(db.String(30), default='Applied', index=True)
    applied_at        = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    verified_at       = db.Column(db.DateTime, nullable=True)
    result_updated_at = db.Column(db.DateTime, nullable=True)
    updated_at        = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    admin_notes       = db.Column(db.Text, nullable=True)
    updated_result    = db.Column(db.String(200), nullable=True)
    last_page_hash    = db.Column(db.String(64), nullable=True)
 
    rexam_reminders   = db.relationship('ReExamReminder', backref='revaluation_app', lazy='select')
 
    def __repr__(self):
        return f'<RevalApp {self.prn_number} - {self.subject_name}>'
 
 
# ─── PhotocopyApplication ─────────────────────────────────────────────────────
 
class PhotocopyApplication(db.Model):
    __tablename__ = 'photocopy_application'
    __table_args__ = (
        db.Index('idx_student_status', 'student_id', 'status'),
    )
 
    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subject_name = db.Column(db.String(200), nullable=False)
    exam_year    = db.Column(db.String(20), nullable=False)
    semester     = db.Column(db.String(20), nullable=False)
    prn_number   = db.Column(db.String(50), nullable=False)
    num_papers   = db.Column(db.Integer, default=1)
    fee_amount   = db.Column(db.Integer, default=200)
    status       = db.Column(db.String(30), default='Applied', index=True)
    applied_at   = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    verified_at  = db.Column(db.DateTime, nullable=True)
    expected_by  = db.Column(db.DateTime, nullable=True)
    received_at  = db.Column(db.DateTime, nullable=True)
    updated_at   = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    admin_notes  = db.Column(db.Text, nullable=True)
 
    def __repr__(self):
        return f'<PhotocopyApp {self.prn_number} - {self.subject_name}>'
 
 
# ─── ReExamReminder ───────────────────────────────────────────────────────────
 
class ReExamReminder(db.Model):
    __tablename__ = 're_exam_reminder'
    __table_args__ = (
        db.Index('idx_student_active', 'student_id', 'is_active'),
        db.Index('idx_last_reminded', 'last_reminded'),
    )
 
    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    reval_app_id   = db.Column(db.Integer, db.ForeignKey('revaluation_application.id', ondelete='CASCADE'), nullable=True)
    subject_name   = db.Column(db.String(200), nullable=False)
    semester       = db.Column(db.String(20), nullable=True)
    exam_year      = db.Column(db.String(20), nullable=True)
    prn_number     = db.Column(db.String(50), nullable=True)
    is_active      = db.Column(db.Boolean, default=True, index=True)
    reminder_count = db.Column(db.Integer, default=0)
    last_reminded  = db.Column(db.DateTime, nullable=True)
    form_filled_at = db.Column(db.DateTime, nullable=True)
    created_at     = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    updated_at     = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
 
    def __repr__(self):
        return f'<ReExamReminder {self.prn_number} - {self.subject_name}>'
 
 
# ─── Notification ─────────────────────────────────────────────────────────────
 
class Notification(db.Model):
    __tablename__ = 'notification'
    __table_args__ = (
        db.Index('idx_user_read', 'user_id', 'is_read'),
        db.Index('idx_created_at', 'created_at'),
    )
 
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    notif_type = db.Column(db.String(30), default='info')
    is_read    = db.Column(db.Boolean, default=False, index=True)
    read_at    = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)
 
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
 
    def __repr__(self):
        return f'<Notification {self.title} ({self.notif_type})>'
 
 
# ─── ResultUpload ─────────────────────────────────────────────────────────────
 
class ResultUpload(db.Model):
    __tablename__ = 'result_upload'
    __table_args__ = (
        db.Index('idx_student_uploaded', 'student_id', 'uploaded_at'),
    )
 
    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    file_id        = db.Column(db.Integer, db.ForeignKey('file_upload.id', ondelete='SET NULL'), nullable=True)
    filename       = db.Column(db.String(300), nullable=True)
    extracted_text = db.Column(db.Text, nullable=True)
    parsed_json    = db.Column(db.Text, nullable=True)
    sgpa           = db.Column(db.String(10), nullable=True)
    cgpa           = db.Column(db.String(10), nullable=True)
    uploaded_at    = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    parsed_at      = db.Column(db.DateTime, nullable=True)
 
    def __repr__(self):
        return f'<ResultUpload {self.student_id} - {self.sgpa} SGPA>'
 
 
# ─── FailedStudentRecord ──────────────────────────────────────────────────────
 
class FailedStudentRecord(db.Model):
    __tablename__ = 'failed_student_record'
    __table_args__ = (
        db.Index('idx_student_subject', 'student_name', 'subject_name'),
        db.Index('idx_exam_form_filed', 'exam_form_filed'),
        db.Index('idx_created_at', 'created_at'),
    )
 
    id              = db.Column(db.Integer, primary_key=True)
    student_name    = db.Column(db.String(200), nullable=False)
    seat_number     = db.Column(db.String(50), nullable=True)
    email           = db.Column(db.String(150), nullable=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    semester        = db.Column(db.String(20), nullable=False)
    exam_year       = db.Column(db.String(20), nullable=True)
    subject_name    = db.Column(db.String(200), nullable=False)
    marks           = db.Column(db.String(20), nullable=True)
    grade           = db.Column(db.String(10), nullable=True)
    exam_form_filed = db.Column(db.Boolean, default=False, index=True)
    form_filed_at   = db.Column(db.DateTime, nullable=True)
    mail_sent_count = db.Column(db.Integer, default=0)
    last_mail_sent  = db.Column(db.DateTime, nullable=True)
    pdf_source      = db.Column(db.String(300), nullable=True)
    created_at      = db.Column(db.DateTime, default=get_utc_now, nullable=False)
    updated_at      = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
 
    def __repr__(self):
        return f'<FailedRecord {self.student_name} | {self.subject_name} | Sem {self.semester}>'
 