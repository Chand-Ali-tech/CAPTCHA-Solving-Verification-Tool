from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_SECTION

OUT = 'output/CAPTCHA_Project_Solution_Overview.docx'
NAVY = '17324D'
TEAL = '087E8B'
INK = '243447'
MUTED = '5B6B7A'
PALE = 'EAF3F6'
PALE2 = 'F3F6F8'
WHITE = 'FFFFFF'


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_cell_margins(cell, top=90, start=115, bottom=90, end=115):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in('w:tcMar')
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    for m, v in [('top', top), ('start', start), ('bottom', bottom), ('end', end)]:
        node = tcMar.find(qn('w:' + m))
        if node is None:
            node = OxmlElement('w:' + m)
            tcMar.append(node)
        node.set(qn('w:w'), str(v))
        node.set(qn('w:type'), 'dxa')


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    tblHeader.set(qn('w:val'), 'true')
    trPr.append(tblHeader)


def set_cell_text(cell, text, bold=False, color=INK, size=9.2):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.04
    r = p.add_run(text)
    r.bold = bold
    r.font.name = 'Liberation Sans'
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell)


def format_table(table, header=True, widths=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for ri, row in enumerate(table.rows):
        if ri == 0 and header:
            set_repeat_table_header(row)
        for ci, cell in enumerate(row.cells):
            if widths and ci < len(widths):
                cell.width = Inches(widths[ci])
            if ri == 0 and header:
                shade(cell, NAVY)
            elif ri % 2 == 0:
                shade(cell, PALE2)
            else:
                shade(cell, WHITE)
            set_cell_margins(cell)


def add_table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    for i, h in enumerate(headers):
        set_cell_text(t.rows[0].cells[i], h, True, WHITE, 9.1)
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, False, INK, 8.8)
    format_table(t, True, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def add_bullet(doc, lead, body):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(lead)
    r.bold = True
    p.add_run(body)
    return p


def add_num(doc, lead, body):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(lead)
    r.bold = True
    p.add_run(body)
    return p


def add_callout(doc, label, text):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    shade(cell, PALE)
    set_cell_margins(cell, top=135, start=180, bottom=135, end=180)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(label + '  ')
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(TEAL)
    p.add_run(text)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = paragraph.add_run('CAPTCHA Tool  |  ')
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor.from_string(MUTED)
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), 'PAGE')
    paragraph._p.append(fld)


doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.65)
sec.bottom_margin = Inches(0.62)
sec.left_margin = Inches(0.72)
sec.right_margin = Inches(0.72)
sec.header_distance = Inches(0.28)
sec.footer_distance = Inches(0.3)

styles = doc.styles
normal = styles['Normal']
normal.font.name = 'Liberation Sans'
normal.font.size = Pt(9.6)
normal.font.color.rgb = RGBColor.from_string(INK)
normal.paragraph_format.space_after = Pt(5)
normal.paragraph_format.line_spacing = 1.08
for name, size, color in [('Title', 27, NAVY), ('Heading 1', 17, NAVY), ('Heading 2', 11.5, TEAL)]:
    st = styles[name]
    st.font.name = 'Liberation Sans'
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor.from_string(color)
    st.paragraph_format.keep_with_next = True
    st.paragraph_format.space_before = Pt(9 if name != 'Title' else 0)
    st.paragraph_format.space_after = Pt(4 if name != 'Title' else 7)
for name in ['List Bullet', 'List Number']:
    styles[name].font.name = 'Liberation Sans'
    styles[name].font.size = Pt(9.4)
    styles[name].paragraph_format.left_indent = Inches(0.24)
    styles[name].paragraph_format.first_line_indent = Inches(-0.14)

footer = sec.footer.paragraphs[0]
add_page_number(footer)

# Page 1: positioning and architecture
p = doc.add_paragraph(style='Title')
p.add_run('CAPTCHA Recognition, Solving and Verification')
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(10)
r = p.add_run('Project solution overview  |  Technical assessment presentation')
r.font.name = 'Liberation Sans'
r.font.size = Pt(12)
r.font.color.rgb = RGBColor.from_string(MUTED)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(8)
p.add_run(
    'This project is a local web application for recognizing supported CAPTCHA types, '
    'solving synthetic text challenges with OCR, and demonstrating official provider token '
    'verification. It follows the assessment scope: use synthetic or controlled test challenges '
    'and provider test keys, with no unrelated website automation.'
)
add_callout(doc, 'In one sentence', 'A Next.js interface sends challenge data to a FastAPI backend, where image processing, OCR, provider recognition, token verification and reporting are handled in separate modules.')

doc.add_heading('Solution at a glance', level=1)
add_table(doc, ['Layer', 'Technology', 'Role in the solution'], [
    ('Web interface', 'Next.js 14, React 18, TypeScript', 'Four feature tabs, upload preview, provider test widgets and result displays.'),
    ('API and application logic', 'Python, FastAPI, Uvicorn', 'Receives uploads and form data, routes requests and returns structured JSON.'),
    ('Image recognition and OCR', 'Pillow, NumPy, OpenCV, Tesseract via pytesseract', 'Classifies image shape, preprocesses text images and returns an OCR reading with confidence and timing.'),
    ('Provider verification', 'httpx and provider siteverify APIs', 'Validates tokens on the server using provider secrets kept in the backend environment.'),
], [1.32, 2.12, 3.24])

doc.add_heading('Request path', level=2)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(3)
p.add_run('Browser UI  ').bold = True
p.add_run('→  Next.js /api proxy  →  FastAPI routes  →  recognition, solver, verification or stats modules')
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(4)
p.add_run('The proxy keeps browser requests on the frontend origin. The backend owns image processing, provider calls, secret keys and the running statistics.')

# Page 2: UI workflows

doc.add_page_break()
doc.add_heading('User workflows', level=1)
p = doc.add_paragraph('The home screen separates the main functions into four tabs so a reviewer can follow a challenge from input to result.')
p.paragraph_format.space_after = Pt(8)
add_table(doc, ['Tab', 'What the user does', 'What the application does'], [
    ('1. Recognize and Solve', 'Generate a sample or upload an image; set expected text length.', 'Displays the exact generated or uploaded image, classifies supported uploads, runs OCR, then shows prediction, confidence, method, time and correctness when ground truth is known.'),
    ('2. Provider Recognition', 'Paste owned or test-page HTML, or run a built-in provider example.', 'Checks provider-specific script URLs, widget classes and response field names. Reports the match and distinguishes Cloudflare managed challenge pages from Turnstile widgets.'),
    ('3. Token Verification', 'Complete a provider test widget or try missing/invalid-token cases.', 'Sends the token to FastAPI, calls the provider siteverify endpoint using a server-side secret and displays a structured status.'),
    ('4. Batch and Dashboard', 'Run a batch of generated samples and open the statistics view.', 'Compares OCR output with known labels and summarizes attempts, successes, failures, accuracy, average time, cost estimate and method counts.'),
], [1.32, 2.28, 3.08])

doc.add_heading('Text CAPTCHA solving flow', level=2)
add_num(doc, 'Generate or upload. ', 'The sample flow creates a local synthetic image with known text. The upload flow accepts an image file and expected length.')
add_num(doc, 'Recognize the image. ', 'Pillow decodes the file; NumPy-based measurements use aspect ratio and edge density to identify likely text, image-grid or unknown challenges.')
add_num(doc, 'Preprocess and read. ', 'For supported text images, OpenCV enlarges, pads and enhances contrast, then supplies grayscale and thresholded variants to Tesseract in several line/word modes.')
add_num(doc, 'Rank and report. ', 'The solver selects a candidate using OCR confidence and an expected-length bonus. Generated samples are compared to the answer used to render them; uploaded images have no known answer for automatic scoring.')

add_callout(doc, 'Accuracy note', 'The classifier is a heuristic and Tesseract can still misread distorted images. The batch view is the evidence for measured accuracy; confidence is an estimate, not a guarantee.')

# Page 3: provider, security and reliability

doc.add_page_break()
doc.add_heading('Provider recognition and token verification', level=1)
doc.add_heading('Provider recognition in tab 2', level=2)
p = doc.add_paragraph(
    'Provider recognition is intentionally lightweight. It inspects the supplied HTML for known provider signatures; it does not load or execute the page. Test buttons exercise local HTML fixtures for reCAPTCHA, hCaptcha, Turnstile and a Cloudflare managed challenge page. Multiple provider signals are reported as ambiguous rather than silently selecting one.'
)
p.paragraph_format.space_after = Pt(6)
doc.add_heading('Official token flow in tab 3', level=2)
add_num(doc, 'Render test widgets. ', 'The browser loads each provider SDK using the public site key returned by /api/config.')
add_num(doc, 'Acquire a token. ', 'When the provider widget calls its success callback, the frontend sends the provider name and token to POST /api/verify.')
add_num(doc, 'Validate on the server. ', 'FastAPI selects the provider endpoint and secret key from server/app/config.py, then httpx posts the token to the official siteverify API with a 10-second timeout.')
add_num(doc, 'Return a safe result. ', 'The API returns verified, missing, invalid, expired_or_reused or error status, provider error codes and a short SHA-256 token fingerprint. It does not return the secret or raw token.')

doc.add_heading('Failure handling', level=2)
add_table(doc, ['Case', 'Handling'], [
    ('Missing token', 'Rejected locally before making a provider network call.'),
    ('Invalid token', 'Provider error response becomes a structured invalid status.'),
    ('Expired or reused token', 'Provider-specific error codes map to expired_or_reused. Some providers use one code for both cases.'),
    ('Provider/network/configuration error', 'Returned as an error status; provider calls have a timeout and do not crash the API.'),
], [2.05, 4.63])

doc.add_heading('Secret handling', level=2)
add_bullet(doc, 'Public site keys ', 'are sent to the browser so provider widgets can render.')
add_bullet(doc, 'Secret keys ', 'remain in server/.env and are used only by the backend. The .env file is excluded from version control.')
add_bullet(doc, 'Token data ', 'is not printed to application logs; only a short non-reversible fingerprint is shown in results and stats.')

doc.add_heading('Known limits', level=2)
add_bullet(doc, 'Recognition uses heuristics. ', 'Image shape and edges do not reliably classify every real-world challenge; unknown and unsupported types are declined.')
add_bullet(doc, 'OCR is not perfect. ', 'Tesseract is a conventional OCR engine, not a CAPTCHA-specific trained model. The generator is tuned for controlled OCR evaluation.')
add_bullet(doc, 'Provider HTML detection is signature based. ', 'Dynamic, obfuscated or server-rendered markup that omits known signatures may be missed.')
add_bullet(doc, 'Statistics are in memory. ', 'They reset when the backend restarts; the dashboard is intended for a live demonstration.')
add_bullet(doc, 'Test credentials are not production protection. ', 'Use official test keys only for controlled demos. Real deployments require keys registered for the owned domain and production security review.')

# Page 4: operations, limits, talk track

doc.add_page_break()
doc.add_heading('Configuration and demonstration', level=1)
doc.add_heading('Environment configuration', level=2)
p = doc.add_paragraph('The current server/.env already contains all provider test key entries and matches the project example file. No additional values are required for the local demo.')
p.paragraph_format.space_after = Pt(4)
add_table(doc, ['Variable pair', 'Purpose'], [
    ('RECAPTCHA_SITE_KEY / RECAPTCHA_SECRET_KEY', 'Google reCAPTCHA widget and server validation.'),
    ('HCAPTCHA_SITE_KEY / HCAPTCHA_SECRET_KEY', 'hCaptcha widget and server validation.'),
    ('TURNSTILE_SITE_KEY / TURNSTILE_SECRET_KEY', 'Cloudflare Turnstile widget and server validation.'),
], [3.38, 3.30])
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(6)
p.add_run('For a fresh setup, copy server/.env.example to server/.env. ').bold = True
p.add_run('For a candidate-owned production site, get a site key and secret from that provider’s admin console; keep each secret only on the backend and use development keys/domains separately from production.')

doc.add_heading('Run locally', level=2)
add_table(doc, ['Service', 'Commands'], [
    ('Backend', 'cd server\nsource .venv/bin/activate\nuvicorn app.main:app --reload'),
    ('Frontend', 'cd client\nnpm install\nnpm run dev'),
], [1.35, 5.33])
p = doc.add_paragraph('Open the Next.js app on http://localhost:3000. The frontend proxies /api requests to FastAPI on port 8000 by default.')
p.paragraph_format.space_after = Pt(4)

# Set document metadata and save.
doc.core_properties.title = 'CAPTCHA Recognition, Solving and Verification - Project Solution Overview'
doc.core_properties.subject = 'HR presentation guide and technical solution summary'
doc.core_properties.author = 'Project team'
doc.core_properties.keywords = 'CAPTCHA, OCR, FastAPI, Next.js, token verification'
# The built-in Title style carries a default blue bottom border. Remove it to
# keep the title block clean and consistent with the document design.
title_ppr = styles['Title']._element.pPr
title_border = title_ppr.find(qn('w:pBdr')) if title_ppr is not None else None
if title_border is not None:
    title_ppr.remove(title_border)
doc.save(OUT)
print(OUT)
