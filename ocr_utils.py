"""
ocr_utils.py  —  MU Result PDF Parser  (APSIT Edition)
=======================================================

parse_mu_result_pdf(pdf_path)
  Returns:
    {
      exam_info    : { title, semester, exam_year, exam_type, programme }
      college      : str
      all_students : [ student_dict, ... ]   <- APSIT only
      failed       : [ student_dict, ... ]
      passed       : [ student_dict, ... ]
      atkt         : [ student_dict, ... ]   <- F in some subjects but overall not outright FAIL
      summary      : { total, failed, passed, atkt, unknown }
    }

Each student_dict:
    seat, name, gender, result ('FAILED'|'PASS'|'ATKT'|''),
    total_marks, percentage,
    failed_subjects: [ { code, subject, marks, grade, credits }, ... ]
    all_subjects:    [ { code, subject, marks, grade, credits }, ... ]

Extraction strategy (in order):
  1. pdftotext -layout   (best - preserves column positions)
  2. pdfplumber          (fallback)
  3. Pytesseract OCR     (last resort for scanned PDFs)
"""

import re
import os
import subprocess
from typing import Optional, Dict, List

# ─── Subject Master (NEP 2020, APSIT IT) ──────────────────────────────────────
COURSE_MAP: Dict[str, str] = {
    # Semester I
    '10511': 'Applied Mathematics-I',
    '10512': 'Applied Physics-I',
    '10513': 'Applied Chemistry-I',
    '10514': 'Engineering Mechanics',
    '10515': 'Basic Electrical Engineering',
    '10516': 'Engineering Drawing',
    '10517': 'Workshop Practice',
    '10518': 'Applied Physics-I Lab',
    '10519': 'Applied Chemistry-I Lab',
    '10520': 'Basic Electrical Engineering Lab',
    # Semester II
    '10521': 'Applied Mathematics-II',
    '10522': 'Engineering Graphics',
    '10523': 'Data Structure',
    '10524': 'Object Oriented Programming',
    '10525': 'Digital Electronics',
    '10531': 'Applied Mathematics-II Lab',
    '10532': 'Engineering Graphics Lab',
    '10533': 'Data Structure Lab',
    '10534': 'OOP Lab',
    '10535': 'Digital Electronics Lab',
    '10542': 'Social Science & Community Services',
    '10543': 'Indian Knowledge System',
    '10544': 'Engineering Workshop-II',
    '10545': 'Python Programming',
    '10551': 'Physics for Emerging Fields',
    '10552': 'Semiconductor Physics',
    '10553': 'Physics of Measurements and Sensors',
    '10554': 'Physics for Emerging Fields Lab',
    '10555': 'Semiconductor Physics Lab',
    '10556': 'Physics of Measurements and Sensors Lab',
    '10557': 'Engineering Materials',
    '10558': 'Environmental Chemistry & Non-conventional Energy Sources',
    '10559': 'Introduction to Computational Chemistry',
    '10560': 'Engineering Materials Lab',
    '10561': 'Env. Chemistry & Non-conv. Energy Sources Lab',
    '10562': 'Introduction to Computational Chemistry Lab',
    # Semester III
    '2343111': 'Applied Mathematics-III',
    '2343114': 'Automata Theory',
    '2343115': 'Database Management Systems',
    '2343116': 'Data Structures and Analysis',
    '2343117': 'Computer Organisation & Architecture',
    '2343118': 'Object Oriented Programming Methodology',
    '2343121': 'Applied Mathematics-III Lab',
    '2343122': 'DBMS Lab',
    '2343123': 'Data Structures Lab',
    '2343124': 'OOP Methodology Lab',
    '2343611': 'Mini-Project - Full Stack Java Programming',
    '2343116': 'SQL Lab',
    '2993511': 'Entrepreneurship Development',
    '2993512' : 'Environmental Science',
    '2343112': 'Advance Data Structure & Analysis',
    '1231311': 'Introduction to Banking',
    # Semester IV
    '2343131': 'Applied Mathematics-IV',
    '2343132': 'Analysis of Algorithms',
    '2343133': 'Computer Networks',
    '2343134': 'Operating System',
    '2343135': 'Microprocessor',
    '2343136': 'Computer Graphics',
    '2343141': 'Analysis of Algorithms Lab',
    '2343142': 'Computer Networks Lab',
    '2343143': 'OS Lab',
    '2343144': 'Microprocessor Lab',
    # Semester V
    '2343145': 'Software Engineering',
    '2343146': 'Internet Programming',
    '2343147': 'Information & Network Security',
    '2343148': 'Compiler Design',
    '2343149': 'Artificial Intelligence',
    '2343150': 'IP Lab',
    '2343151': 'INS Lab',
    '2343152': 'AI Lab',
    # Semester VI
    '2343153': 'Mobile Application Development',
    '2343154': 'Cloud Computing',
    '2343155': 'Data Warehousing & Mining',
    '2343156': 'Big Data Analytics',
    '2343157': 'MAD Lab',
    '2343158': 'Cloud Computing Lab',
    '2343159': 'DWM Lab',
    # Semester VII
    '2343160': 'Machine Learning',
    '2343161': 'Distributed Computing',
    '2343162': 'Deep Learning',
    '2343163': 'ML Lab',
    '2343164': 'Deep Learning Lab',
    # Semester VIII
    '2343165': 'Project',
}

APSIT_COLLEGE_CODE = 'MU-0996'
APSIT_COLLEGE_NAME = 'A.P. Shah Institute of Technology'

# Status keywords that appear after the student name
STATUS_WORDS = ('Repeater', 'Regular', 'Fresh', 'Ex-Student', 'Ex Student', 'ex-student')

# ─── Compiled Regexes ─────────────────────────────────────────────────────────
SEAT_RE        = re.compile(r'^\s{0,20}(\d{7,10})\s{2,}')
GENDER_RE      = re.compile(r'\b(MALE|FEMALE)\b', re.IGNORECASE)
TOT_LINE_RE    = re.compile(r'^\s*TOT\s+\d', re.IGNORECASE)
COURSE_CODE_RE = re.compile(r'\b(\d{7}|\d{5})\s*[:\-]')
TABLE_HDR_RE   = re.compile(r'SEAT\s+NO\s+NAME', re.IGNORECASE)
COLLEGE_RE     = re.compile(re.escape(APSIT_COLLEGE_CODE))
PCT_RE         = re.compile(r'(\d{1,3}\.\d{1,2})\s*%')
MARKS_PAREN_RE = re.compile(r'\((\d{2,4})\)')

# Combined result detector: "(420) FAILED", "(524) PASS", "(312) ATKT"
RESULT_RE       = re.compile(r'\(\s*(\d{2,4})\s*\)\s*(FAILED|PASS|ATKT)', re.IGNORECASE)
FAIL_WORD_RE    = re.compile(r'\bFAILED\b', re.IGNORECASE)
PASS_WORD_RE    = re.compile(r'\bPASS\b(?!\s*ED)', re.IGNORECASE)
ATKT_WORD_RE    = re.compile(r'\bATKT\b', re.IGNORECASE)

# TOT continuation: a line of digits / grades / spaces — no seat or college marker
TOT_CONT_RE = re.compile(r'^[\d\s\w.+$~*]+$')


# ─── Text Extraction ──────────────────────────────────────────────────────────

def _pdftotext(pdf_path: str) -> str:
    try:
        r = subprocess.run(
            ['pdftotext', '-layout', '-enc', 'UTF-8', pdf_path, '-'],
            capture_output=True, text=True, timeout=300, errors='replace'
        )
        if r.returncode == 0 and len(r.stdout.strip()) > 200:
            return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ''


def _pdfplumber(pdf_path: str) -> str:
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text(x_tolerance=3, y_tolerance=3)
                if t:
                    pages.append(t)
        return '\n'.join(pages)
    except Exception:
        return ''


def _tesseract(pdf_path: str) -> str:
    """Last-resort OCR — requires PyMuPDF + pytesseract."""
    try:
        import fitz
        from PIL import Image
        import pytesseract
        import io
        doc   = fitz.open(pdf_path)
        texts = []
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes('png')))
            texts.append(pytesseract.image_to_string(img, config='--psm 6'))
        return '\n'.join(texts)
    except Exception:
        return ''


def extract_text(pdf_path: str) -> str:
    text = _pdftotext(pdf_path)
    if not text:
        text = _pdfplumber(pdf_path)
    if not text:
        text = _tesseract(pdf_path)
    if not text:
        raise RuntimeError(
            "Cannot extract text from PDF.\n"
            "Install poppler-utils (pdftotext) or pdfplumber.\n"
            "For scanned PDFs: PyMuPDF + pytesseract."
        )
    return text


# ─── Header Parser ────────────────────────────────────────────────────────────

def _extract_exam_info(text: str) -> dict:
    info = {'title': '', 'semester': '', 'exam_year': '', 'exam_type': '', 'programme': ''}
    m = re.search(
        r'OFFICE\s+REGISTER\s+FOR\s+THE\s+(.+?)\s*\(\s*Semester\s*[:\-]?\s*(\w+)\s*\)',
        text, re.IGNORECASE | re.DOTALL
    )
    if m:
        info['title']     = ' '.join(m.group(1).split())
        info['semester']  = m.group(2).strip()
        info['programme'] = info['title']
    m2 = re.search(r'EXAMINATION\s+HELD\s+IN\s+([A-Z]+\s+\d{4})', text, re.IGNORECASE)
    if m2:
        info['exam_year'] = m2.group(1).strip()
    if re.search(r'\bSUPPLEMENTARY\b', text, re.IGNORECASE):
        info['exam_type'] = 'SUPPLEMENTARY'
    elif re.search(r'\bREGULAR\b', text, re.IGNORECASE):
        info['exam_type'] = 'REGULAR'
    return info


# ─── TOT Line Subject Parser ──────────────────────────────────────────────────

def _parse_tot_line(tot_line: str, course_codes: List[str]) -> List[dict]:
    """
    Parse TOT line.  Each subject occupies 5 tokens:
        marks   GP   grade   credits   GP*C
    Strips decoration (+, $, ~, #, @, *) from marks and grade.
    Returns list of ALL subjects — caller filters failed ones.
    """
    clean  = re.sub(r'^\s*TOT\s+', '', tot_line, flags=re.IGNORECASE).strip()
    tokens = clean.split()
    out    = []
    chunk  = 5

    for idx, code in enumerate(course_codes):
        s = idx * chunk
        if s + chunk > len(tokens):
            break
        seg      = tokens[s: s + chunk]
        marks    = seg[0].rstrip('+$~#@*') if len(seg) > 0 else ''
        gp       = seg[1]                   if len(seg) > 1 else ''
        grade    = seg[2].upper().rstrip('+$~#@*') if len(seg) > 2 else ''
        credits  = seg[3]                   if len(seg) > 3 else ''

        out.append({
            'code':    code,
            'subject': COURSE_MAP.get(code, f'Subject {code}'),
            'marks':   marks,
            'grade':   grade,
            'credits': credits,
            'gp':      gp,
            'failed':  grade == 'F',
        })

    return out


# ─── Student Finaliser ────────────────────────────────────────────────────────

def _flush_student(st: dict) -> dict:
    """Resolve TOT buffer → subject lists, infer result if missing."""
    if st is None:
        return st
    tot          = st.pop('_tot', '')
    course_order = st.pop('_course_order', [])

    all_subj  = []
    failed_subj = []

    if tot and course_order:
        all_subj    = _parse_tot_line(tot, course_order)
        failed_subj = [s for s in all_subj if s['failed']]

    st['all_subjects']    = all_subj
    st['failed_subjects'] = failed_subj

    # Infer result when the result line was not found
    if not st['result']:
        if failed_subj:
            st['result'] = 'ATKT'
        elif all_subj:
            st['result'] = 'PASS'

    return st


# ─── Main Parser ─────────────────────────────────────────────────────────────

def parse_mu_result_pdf(pdf_path: str,
                        college_filter: str = APSIT_COLLEGE_CODE) -> dict:
    """
    Parse a Mumbai University result register PDF.
    Returns structured data filtered to the given college (default APSIT).
    """
    raw_text = extract_text(pdf_path)
    lines    = raw_text.splitlines()

    exam_info = _extract_exam_info(raw_text)

    students:        List[dict]        = []
    current:         Optional[dict]    = None
    header_courses:  List[str]         = []
    tot_buffer:      str               = ''
    last_marks_line: str               = ''

    for line in lines:

        # ── New table header resets course list ───────────────────────────
        if TABLE_HDR_RE.search(line):
            header_courses = []
            continue

        # ── Collect course codes from header rows ─────────────────────────
        for c in COURSE_CODE_RE.findall(line):
            if c not in header_courses:
                header_courses.append(c)

        # ── Detect start of an APSIT student row ──────────────────────────
        if college_filter in line:
            seat_m = SEAT_RE.match(line)
            if seat_m:
                # Flush previous student
                if current is not None:
                    if tot_buffer:
                        current['_tot'] = tot_buffer
                        tot_buffer = ''
                    students.append(_flush_student(current))

                # Extract student name (text before first status keyword)
                rest = line[seat_m.end():]
                name = ''
                rest_upper = rest.upper()
                earliest = len(rest)
                for sw in STATUS_WORDS:
                    idx = rest_upper.find(sw.upper())
                    if idx != -1 and idx < earliest:
                        earliest = idx
                if earliest < len(rest):
                    name = rest[:earliest].strip()
                if not name:
                    nm = re.match(r'([A-Z][A-Z\s\'\.]{2,50}?)\s{3,}', rest)
                    if nm:
                        name = nm.group(1).strip()

                gender_m = GENDER_RE.search(line)
                gender   = gender_m.group(1).upper() if gender_m else ''

                current = {
                    'seat':          seat_m.group(1).strip(),
                    'name':          ' '.join(name.split()),
                    'gender':        gender,
                    'result':        '',
                    'total_marks':   '',
                    'percentage':    '',
                    '_tot':          '',
                    '_course_order': list(header_courses),
                    'failed_subjects': [],
                    'all_subjects':    [],
                }
                tot_buffer      = ''
                last_marks_line = ''
                continue

        if current is None:
            continue

        # ── TOT line detection ─────────────────────────────────────────────
        if TOT_LINE_RE.match(line):
            tot_buffer = line
            continue

        # ── TOT continuation line ──────────────────────────────────────────
        if tot_buffer:
            stripped = line.strip()
            if (stripped
                    and TOT_CONT_RE.match(stripped)
                    and not SEAT_RE.match(line)
                    and college_filter not in line):
                tot_buffer += ' ' + stripped
                continue
            else:
                # TOT is complete
                if not current['_tot']:
                    current['_tot'] = tot_buffer
                tot_buffer = ''

        # ── Result detection ──────────────────────────────────────────────
        if not current['result']:
            rm = RESULT_RE.search(line)
            if rm:
                current['total_marks'] = rm.group(1)
                current['result']      = rm.group(2).upper()
            elif FAIL_WORD_RE.search(line):
                current['result'] = 'FAILED'
                if not current['total_marks']:
                    mm = MARKS_PAREN_RE.search(last_marks_line + ' ' + line)
                    if mm:
                        current['total_marks'] = mm.group(1)
            elif ATKT_WORD_RE.search(line):
                current['result'] = 'ATKT'
                if not current['total_marks']:
                    mm = MARKS_PAREN_RE.search(last_marks_line + ' ' + line)
                    if mm:
                        current['total_marks'] = mm.group(1)
            elif PASS_WORD_RE.search(line):
                current['result'] = 'PASS'
                if not current['total_marks']:
                    mm = MARKS_PAREN_RE.search(last_marks_line + ' ' + line)
                    if mm:
                        current['total_marks'] = mm.group(1)

        # Track last marks line for split-result recovery
        if MARKS_PAREN_RE.search(line):
            last_marks_line = line
            if not current['total_marks']:
                mm = MARKS_PAREN_RE.search(line)
                if mm:
                    current['total_marks'] = mm.group(1)

        # Percentage
        if not current['percentage']:
            pm = PCT_RE.search(line)
            if pm:
                current['percentage'] = pm.group(1)

    # ── Flush last student ────────────────────────────────────────────────
    if current is not None:
        if tot_buffer and not current['_tot']:
            current['_tot'] = tot_buffer
        students.append(_flush_student(current))

    students = [s for s in students if s]

    failed = [s for s in students if s['result'] == 'FAILED']
    passed = [s for s in students if s['result'] == 'PASS']
    atkt   = [s for s in students if s['result'] == 'ATKT']

    return {
        'exam_info':    exam_info,
        'college':      APSIT_COLLEGE_NAME,
        'all_students': students,
        'failed':       failed,
        'passed':       passed,
        'atkt':         atkt,
        'summary': {
            'total':   len(students),
            'failed':  len(failed),
            'passed':  len(passed),
            'atkt':    len(atkt),
            'unknown': len([s for s in students
                            if s['result'] not in ('FAILED', 'PASS', 'ATKT')]),
        },
    }


# ─── Legacy shims ─────────────────────────────────────────────────────────────

def extract_text_from_image(image_path: str) -> str:
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, config='--psm 6')
    except ImportError:
        raise RuntimeError("Install Pillow + pytesseract for image OCR.")


def extract_text_from_pdf(pdf_path: str) -> str:
    return extract_text(pdf_path)


def parse_result_text(raw_text: str) -> dict:
    return {'subjects': [], 'sgpa': None, 'cgpa': None, 'raw': raw_text}


def process_upload(file_path: str) -> dict:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return parse_mu_result_pdf(file_path)
    raise RuntimeError(f"Unsupported file type: {ext}. Use parse_mu_result_pdf() for PDFs.")
