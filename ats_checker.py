import re
import PyPDF2

# -----------------------------------------------------------------------------
# 1. REFERENCE DATA
# -----------------------------------------------------------------------------
BUZZWORDS = [
    "hardworking", "team player", "detail-oriented", "detail oriented", "go-getter",
    "synergy", "results-driven", "results oriented", "self-motivated", "dynamic",
    "passionate", "excellent communication skills", "think outside the box",
    "fast-paced environment", "proactive", "highly motivated", "people person",
    "outside the box", "value add", "self starter", "self-starter"
]

REQUIRED_SECTIONS = {
    "experience": [r'\bexperience\b', r'\bwork\s+history\b', r'\bemployment\b'],
    "education": [r'\beducation\b', r'\bacademic\b'],
    "skills": [r'\bskills\b', r'\btechnical\s+skills\b', r'\bcore\s+competencies\b'],
}

GENERIC_FILENAME_PATTERNS = [
    r'(?i)^resume\.pdf$',
    r'(?i)^cv\.pdf$',
    r'(?i)final',
    r'(?i)copy',
    r'(?i)draft',
    r'(?i)untitled',
    r'(?i)download',
    r'(?i)\(\d+\)',
    r'(?i)_v\d+',
    r'(?i)temp',
]

WEIGHTS = {
    "Text Extraction": 20,
    "Contact Information": 15,
    "Section Headers": 20,
    "Layout & Formatting": 15,
    "Resume Length": 10,
    "File Naming": 10,
    "Keyword Density": 10,
}

STATUS_MULTIPLIER = {"pass": 1.0, "warning": 0.5, "fail": 0.0}


def _check(name, status, message, fix):
    """Helper to build a single check-result dict."""
    return {"name": name, "status": status, "message": message, "fix": fix}


# -----------------------------------------------------------------------------
# 2. INDIVIDUAL CHECKS
# -----------------------------------------------------------------------------
def check_text_extraction(raw_text):
    word_count = len(raw_text.split()) if raw_text else 0
    if word_count < 30:
        return _check(
            "Text Extraction", "fail",
            f"Only {word_count} words were extracted — this file may be a scanned image or contain non-selectable text.",
            "Re-export your resume as a text-based PDF (e.g. 'Save as PDF' from Word/Google Docs) rather than scanning a printed copy."
        )
    elif word_count < 100:
        return _check(
            "Text Extraction", "warning",
            f"Only {word_count} words were extracted — that seems low for a complete resume.",
            "Confirm every section is selectable text and not embedded as an image or graphic."
        )
    return _check(
        "Text Extraction", "pass",
        f"Successfully extracted {word_count} words of readable, parseable text.",
        None
    )


def check_contact_info(raw_text):
    email_found = bool(re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', raw_text or ""))
    phone_found = bool(re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', raw_text or ""))
    linkedin_found = bool(re.search(r'(?i)linkedin\.com', raw_text or ""))

    missing = [n for n, found in [("email address", email_found), ("phone number", phone_found)] if not found]

    if not missing:
        msg = "Email and phone number were both found."
        if linkedin_found:
            msg += " A LinkedIn/portfolio link was also detected."
        return _check("Contact Information", "pass", msg, None)
    elif len(missing) == 1:
        return _check(
            "Contact Information", "warning",
            f"Could not find a {missing[0]}.",
            f"Add your {missing[0]} near the top of the resume so recruiters and ATS parsers can find it easily."
        )
    return _check(
        "Contact Information", "fail",
        "No email address or phone number was detected.",
        "Add a clear contact block at the top of your resume with your email and phone number."
    )


def check_section_headers(raw_text):
    text_lower = (raw_text or "").lower()
    missing = []
    for section, patterns in REQUIRED_SECTIONS.items():
        if not any(re.search(p, text_lower) for p in patterns):
            missing.append(section)

    if not missing:
        return _check("Section Headers", "pass", "Standard sections (Experience, Education, Skills) were all found.", None)
    elif len(missing) == 1:
        label = missing[0].title()
        return _check(
            "Section Headers", "warning",
            f"Could not find a clearly labeled '{label}' section.",
            f"Add a clearly labeled '{label}' heading — ATS parsers rely on conventional section names to categorize content."
        )
    labels = ", ".join(m.title() for m in missing)
    return _check(
        "Section Headers", "fail",
        f"Missing standard section headers: {labels}.",
        f"Add clearly labeled headings for: {labels}. Use conventional names (e.g. 'Experience') rather than creative titles."
    )


def check_formatting(uploaded_file):
    """Inspects PDF structure for images and excessive font variety."""
    has_images = False
    font_count = 0
    num_pages = 0
    try:
        uploaded_file.seek(0)
        reader = PyPDF2.PdfReader(uploaded_file)
        num_pages = len(reader.pages)
        fonts = set()
        for page in reader.pages:
            resources = page.get("/Resources")
            if not resources:
                continue
            xobjects = resources.get("/XObject")
            if xobjects:
                for obj_name in xobjects:
                    try:
                        if xobjects[obj_name].get("/Subtype") == "/Image":
                            has_images = True
                    except Exception:
                        pass
            font_res = resources.get("/Font")
            if font_res:
                for f in font_res:
                    fonts.add(f)
        font_count = len(fonts)
    except Exception:
        pass

    issues = []
    if has_images:
        issues.append("embedded images or graphics were detected (icons, photos, or logos)")
    if font_count > 6:
        issues.append(f"{font_count} different fonts were detected, which can signal inconsistent styling")

    if not issues:
        check = _check("Layout & Formatting", "pass", "No major layout red flags (embedded images or excessive font variety) detected.", None)
    elif len(issues) == 1:
        check = _check(
            "Layout & Formatting", "warning",
            issues[0].capitalize() + ".",
            "Avoid images, icons, or decorative graphics in the resume body — stick to plain text and simple bullet formatting for the best ATS compatibility."
        )
    else:
        check = _check(
            "Layout & Formatting", "fail",
            "; ".join(issues).capitalize() + ".",
            "Simplify to plain text formatting: avoid tables, text boxes, columns, and images, and limit yourself to 1-2 standard fonts."
        )
    return check, num_pages


def check_length(num_pages, word_count):
    if num_pages == 0:
        return _check("Resume Length", "warning", "Could not determine page count.", None)
    if word_count < 150:
        return _check(
            "Resume Length", "warning",
            f"Only {word_count} words detected across {num_pages} page(s) — this may be too sparse.",
            "Expand on your experience, projects, and skills with specific, quantified achievements."
        )
    if num_pages >= 3:
        return _check(
            "Resume Length", "warning",
            f"{num_pages} pages detected — longer than the typical 1-2 pages recommended for early-to-mid career roles.",
            "Trim to the most relevant experience and consider condensing to 1-2 pages unless applying for a senior/executive role."
        )
    return _check("Resume Length", "pass", f"{num_pages} page(s), {word_count} words — a reasonable length.", None)


def check_filename(filename):
    if not filename:
        return _check("File Naming", "warning", "Filename unavailable.", None)
    name_lower = filename.lower()
    for pattern in GENERIC_FILENAME_PATTERNS:
        if re.search(pattern, name_lower):
            return _check(
                "File Naming", "warning",
                f"Filename '{filename}' looks generic or auto-generated.",
                "Rename the file to something professional and unique, e.g. 'FirstName_LastName_Resume.pdf'."
            )
    return _check("File Naming", "pass", f"Filename '{filename}' looks professional.", None)


def check_keyword_density(raw_text):
    text_lower = (raw_text or "").lower()
    found = []
    for phrase in BUZZWORDS:
        count = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower))
        if count > 0:
            found.append((phrase, count))

    total_hits = sum(c for _, c in found)
    phrase_list = ", ".join(p for p, _ in found)

    if total_hits == 0:
        return _check("Keyword Density", "pass", "No overused generic buzzwords detected.", None)
    elif total_hits <= 2:
        return _check(
            "Keyword Density", "warning",
            f"Found {total_hits} generic buzzword(s): {phrase_list}.",
            "Replace vague buzzwords with specific, quantified achievements instead of generic self-descriptions."
        )
    return _check(
        "Keyword Density", "fail",
        f"Found {total_hits} instances of generic buzzwords: {phrase_list}.",
        "Remove generic buzzwords throughout and replace them with concrete accomplishments and metrics."
    )


# -----------------------------------------------------------------------------
# 3. ORCHESTRATOR
# -----------------------------------------------------------------------------
def run_ats_analysis(uploaded_file, raw_text, filename):
    """
    Runs the full suite of ATS-compatibility checks on a resume.

    Parameters:
    - uploaded_file: file-like object (e.g. Streamlit's UploadedFile) for structural inspection.
    - raw_text: already-extracted raw text of the resume.
    - filename: original filename of the uploaded resume.

    Returns:
    - (overall_score: int 0-100, checks: list of check-result dicts)
    """
    word_count = len(raw_text.split()) if raw_text else 0

    checks = [
        check_text_extraction(raw_text),
        check_contact_info(raw_text),
        check_section_headers(raw_text),
    ]

    formatting_check, num_pages = check_formatting(uploaded_file)
    checks.append(formatting_check)

    checks.append(check_length(num_pages, word_count))
    checks.append(check_filename(filename))
    checks.append(check_keyword_density(raw_text))

    total_score = 0.0
    for check in checks:
        weight = WEIGHTS.get(check["name"], 0)
        total_score += weight * STATUS_MULTIPLIER[check["status"]]

    return round(total_score), checks
