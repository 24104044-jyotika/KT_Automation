"""scheduler.py — Background monitoring + reminder jobs (email only)"""
import hashlib, logging
from datetime import datetime, timedelta
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from email_utils import send_result_updated, send_photocopy_reminder, send_rexam_reminder

logger = logging.getLogger(__name__)
_hash_cache = {}

def _fetch_hash(url):
    try:
        r = requests.get(url, headers={"User-Agent": "MU-Portal-Monitor"}, timeout=15)
        r.raise_for_status()
        return hashlib.md5(r.text.encode()).hexdigest()
    except Exception as e:
        logger.warning(f"[Scheduler] fetch failed: {e}")
        return None


def check_mu_results(app):
    with app.app_context():
        from extensions import db, mail
        from app import add_notification
        from app import RevaluationApplication, PhotocopyApplication, ReExamReminder

        apps = RevaluationApplication.query.filter_by(status='Monitoring').all()
        for obj in apps:
            url = f"{app.config['MU_RESULT_BASE_URL']}?prn={obj.prn_number}"
            h   = _fetch_hash(url)
            if h is None:
                continue
            old = _hash_cache.get(obj.id)
            if old is None:
                _hash_cache[obj.id] = h
                continue
            if old != h:
                _hash_cache[obj.id] = h
                obj.status = 'Result Updated'
                obj.result_updated_at = datetime.utcnow()
                obj.updated_result = 'Result updated on MU portal – check official site'
                db.session.commit()
                s = obj.student
                add_notification(s.id, 'Result Updated',
                                 f'Result for {obj.subject_name} updated.', 'success')
                try:
                    send_result_updated(mail, s.name, s.email,
                                        obj.subject_name, obj.updated_result, obj.id)
                except Exception as e:
                    logger.error(f"[Email result] {e}")


def photocopy_reminders(app):
    with app.app_context():
        from app import db, mail, add_notification, PhotocopyApplication

        now  = datetime.utcnow()
        apps = PhotocopyApplication.query.filter(
            PhotocopyApplication.status == 'In Progress',
            PhotocopyApplication.expected_by <= now + timedelta(days=3),
            PhotocopyApplication.expected_by >= now
        ).all()
        for obj in apps:
            s   = obj.student
            exp = obj.expected_by.strftime('%d %b %Y')
            add_notification(s.id, 'Photocopy Reminder',
                             f'Your photocopy for {obj.subject_name} expected by {exp}.', 'warning')
            try:
                send_photocopy_reminder(mail, s.name, s.email, obj.subject_name, exp, obj.id)
            except Exception as e:
                logger.error(f"[Email photo] {e}")


def send_rexam_reminders(app):
    with app.app_context():
        from app import db, mail, add_notification, ReExamReminder

        now    = datetime.utcnow()
        active = ReExamReminder.query.filter_by(is_active=True).all()
        logger.info(f"[Scheduler] Re-exam reminders: {len(active)} active")

        for rem in active:
            if rem.last_reminded and (now - rem.last_reminded).days < 3:
                continue

            rem.reminder_count += 1
            rem.last_reminded   = now
            db.session.commit()

            s = rem.student
            add_notification(s.id,
                             f' Re-Exam Form Reminder #{rem.reminder_count}',
                             f'Please fill the re-exam form for {rem.subject_name}. '
                             f'You have been reminded {rem.reminder_count} time(s).',
                             'warning')
            try:
                send_rexam_reminder(mail, s.name, s.email, rem.subject_name,
                                    rem.semester, rem.prn_number, rem.reminder_count)
            except Exception as e:
                logger.error(f"[Email rexam] {e}")

            logger.info(f"[Scheduler] Reminder #{rem.reminder_count} sent to {s.name}")


def start_scheduler(app):
    hours = app.config.get('SCHEDULER_INTERVAL_HOURS', 6)
    s = BackgroundScheduler(daemon=True)
    s.add_job(check_mu_results,     IntervalTrigger(hours=hours), args=[app],
              id='mu_check',        replace_existing=True)
    s.add_job(photocopy_reminders,  IntervalTrigger(hours=24),    args=[app],
              id='photo_remind',    replace_existing=True)
    s.add_job(send_rexam_reminders, IntervalTrigger(hours=72),    args=[app],
              id='rexam_remind',    replace_existing=True)
    s.start()
    logger.info(f"[Scheduler] Started — MU check every {hours}h, photocopy daily, re-exam every 3 days")
    return s