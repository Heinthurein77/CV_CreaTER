"""
Professional CV Builder — Canva-style, clean two-column PDF
Run:  streamlit run cv_builder_pro.py
"""

import io
import streamlit as st
from PIL import Image, ImageOps, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Pro CV Builder", layout="wide", page_icon="💼")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.stApp { background: #F0F2F8; }

.cv-header {
    background: linear-gradient(135deg, #1E1B4B 0%, #312E81 60%, #4338CA 100%);
    border-radius: 18px;
    padding: 32px 36px 28px;
    margin-bottom: 24px;
    color: white;
}
.cv-header h1 { color: white !important; font-size: 2rem !important; margin: 0 !important; }
.cv-header p  { color: rgba(255,255,255,0.75); margin: 6px 0 0; font-size: 0.95rem; }

.card {
    background: white;
    border-radius: 14px;
    padding: 26px 30px;
    margin-bottom: 16px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.07);
    border: 1px solid #EEF0F8;
}
.card-title {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6366F1;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.card-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E8EAFF;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 9px !important;
    border: 1.5px solid #E2E5F0 !important;
    background: #FAFBFF !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 11px !important;
    padding: 0.65rem 2.4rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 5px 18px rgba(79,70,229,0.38) !important;
}

section[data-testid="stSidebar"] { background: #1E1B4B !important; }
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #A5B4FC !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}

label { font-weight: 500 !important; font-size: 0.87rem !important; color: #374151 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  COLOR UTILS
# ══════════════════════════════════════════════════════════════════════════════

def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

def lighten(rgb, a=0.20): return tuple(min(1.0, v + a) for v in rgb)
def darken(rgb,  a=0.12): return tuple(max(0.0, v - a) for v in rgb)


# ══════════════════════════════════════════════════════════════════════════════
#  IMAGE HELPER
# ══════════════════════════════════════════════════════════════════════════════

def make_circle_png(img_file) -> io.BytesIO:
    img  = Image.open(img_file).convert("RGBA")
    img  = ImageOps.fit(img, (500, 500), centering=(0.5, 0.5))
    mask = Image.new("L", (500, 500), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 500, 500), fill=255)
    img.putalpha(mask)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
#  PDF DRAWING PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════

def rr(c, x, y, w, h, r, rgb):
    c.setFillColorRGB(*rgb)
    c.roundRect(x, y, w, h, r, stroke=0, fill=1)


def word_wrap(c, text, x, y, max_w, font, size, leading, rgb=(0.15, 0.15, 0.2)):
    c.setFont(font, size)
    c.setFillColorRGB(*rgb)
    for raw in text.split("\n"):
        words, line = raw.split(), ""
        for w in words:
            trial = (line + " " + w).strip()
            if c.stringWidth(trial, font, size) <= max_w:
                line = trial
            else:
                if line:
                    c.drawString(x, y, line)
                    y -= leading
                line = w
        if line:
            c.drawString(x, y, line)
            y -= leading
    return y


def sidebar_section_title(c, label, x, y, width):
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColorRGB(1, 1, 1, 0.50)
    c.drawString(x, y, label.upper())
    c.setStrokeColorRGB(1, 1, 1, 0.15)
    c.setLineWidth(0.5)
    c.line(x, y - 2.5, x + width, y - 2.5)
    return y - 11


def main_section_title(c, label, x, y, width, accent):
    bar_h = 10
    rr(c, x, y - bar_h + 2, 3, bar_h, 1, accent)
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColorRGB(*darken(accent, 0.05))
    c.drawString(x + 7, y - 0.5, label.upper())
    c.setStrokeColorRGB(*lighten(accent, 0.40))
    c.setLineWidth(0.7)
    c.line(x, y - bar_h + 1, x + width, y - bar_h + 1)
    return y - bar_h - 5


def draw_skill_tag(c, text, x, y, accent):
    fs     = 8
    pad_x  = 7
    tag_h  = 5.5 * mm
    tw     = c.stringWidth(text, "Helvetica", fs)
    w      = tw + pad_x * 2
    rr(c, x, y - 1.5, w, tag_h, 2.5, lighten(accent, 0.32))
    c.setFont("Helvetica", fs)
    c.setFillColorRGB(*darken(accent, 0.10))
    c.drawString(x + pad_x, y + 2, text)
    return w + 3


def draw_contact_row(c, label, value, x, y, avail_w, fs=8.2):
    if not value:
        return y
    c.setFont("Helvetica-Bold", fs)
    c.setFillColorRGB(1, 1, 1, 0.60)
    lbl_w = c.stringWidth(label, "Helvetica-Bold", fs) + 3
    c.drawString(x, y, label)
    c.setFont("Helvetica", fs)
    c.setFillColorRGB(1, 1, 1, 0.95)
    val = value
    while val and c.stringWidth(val, "Helvetica", fs) > avail_w - lbl_w:
        val = val[:-1]
    c.drawString(x + lbl_w, y, val)
    return y - 6 * mm


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PDF GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_cv_pdf(data: dict, theme_hex: str, photo_buf) -> bytes:
    PAGE_W, PAGE_H = A4

    SB_W          = 66 * mm
    SB_PAD        = 7 * mm
    SB_CONTENT_W  = SB_W - SB_PAD * 2

    MN_X          = SB_W + 11 * mm
    MN_PAD        = 11 * mm
    MN_W          = PAGE_W - MN_X - MN_PAD

    HEADER_H      = 44 * mm

    accent  = hex_to_rgb(theme_hex)
    acc_dk  = darken(accent, 0.14)
    acc_lt  = lighten(accent, 0.18)
    sb_bg   = darken(accent, 0.22)
    sb_bg2  = darken(accent, 0.30)

    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)

    # ── SIDEBAR BG ────────────────────────────────────────────────────────────
    c.setFillColorRGB(*sb_bg)
    c.rect(0, 0, SB_W, PAGE_H, fill=1, stroke=0)
    c.setFillColorRGB(*sb_bg2)
    c.rect(0, PAGE_H - 80 * mm, SB_W, 80 * mm, fill=1, stroke=0)
    c.setFillColorRGB(*darken(accent, 0.35))
    c.circle(SB_W / 2, 18 * mm, 28 * mm, fill=1, stroke=0)

    # ── HEADER BANNER (right) ─────────────────────────────────────────────────
    c.setFillColorRGB(*acc_dk)
    c.rect(SB_W, PAGE_H - HEADER_H, PAGE_W - SB_W, HEADER_H, fill=1, stroke=0)
    c.setFillColorRGB(*lighten(accent, 0.10))
    c.circle(PAGE_W + 5 * mm, PAGE_H + 5 * mm, 42 * mm, fill=1, stroke=0)
    c.setFillColorRGB(*accent)
    c.circle(PAGE_W - 18 * mm, PAGE_H - 8 * mm, 22 * mm, fill=1, stroke=0)

    # ── PROFILE PHOTO ─────────────────────────────────────────────────────────
    PHOTO_D = 36 * mm
    px = SB_W / 2
    py = PAGE_H - 22 * mm - PHOTO_D / 2

    if photo_buf:
        photo_buf.seek(0)
        c.setFillColorRGB(*lighten(accent, 0.28))
        c.circle(px, py, PHOTO_D / 2 + 3.5 * mm, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.circle(px, py, PHOTO_D / 2 + 1.8 * mm, fill=1, stroke=0)
        c.drawImage(ImageReader(photo_buf),
                    px - PHOTO_D / 2, py - PHOTO_D / 2,
                    PHOTO_D, PHOTO_D, mask="auto")
    else:
        c.setFillColorRGB(*lighten(accent, 0.20))
        c.circle(px, py, PHOTO_D / 2 + 1.8 * mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 22)
        c.setFillColorRGB(1, 1, 1)
        initials = "".join(p[0].upper() for p in data["name"].split()[:2])
        c.drawCentredString(px, py - 4, initials)

    # ── NAME & JOB TITLE ──────────────────────────────────────────────────────
    name_y = PAGE_H - 14 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(MN_X, name_y, data["name"])
    c.setFont("Helvetica", 11.5)
    c.setFillColorRGB(*lighten(accent, 0.52))
    c.drawString(MN_X, name_y - 9 * mm, data["job_title"].upper())
    c.setStrokeColorRGB(1, 1, 1, 0.22)
    c.setLineWidth(0.6)
    c.line(MN_X, name_y - 12.5 * mm, PAGE_W - MN_PAD, name_y - 12.5 * mm)

    # Compact contact strip inside banner
    strip_y = name_y - 19 * mm
    strip_items = []
    if data["phone"]:   strip_items.append(("Tel:", data["phone"]))
    if data["email"]:   strip_items.append(("Email:", data["email"]))
    if data["website"]: strip_items.append(("Web:", data["website"]))

    cx = MN_X
    for lbl, val in strip_items:
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColorRGB(1, 1, 1, 0.52)
        c.drawString(cx, strip_y, lbl)
        lbl_w = c.stringWidth(lbl, "Helvetica-Bold", 7.5) + 2.5
        c.setFont("Helvetica", 7.5)
        c.setFillColorRGB(1, 1, 1, 0.92)
        c.drawString(cx + lbl_w, strip_y, val)
        cx += lbl_w + c.stringWidth(val, "Helvetica", 7.5) + 10
        if cx > PAGE_W - MN_PAD - 8 * mm:
            break

    # ── SIDEBAR CONTENT ───────────────────────────────────────────────────────
    sy = PAGE_H - 68 * mm
    sx = SB_PAD
    sw = SB_CONTENT_W

    # Contact
    sy = sidebar_section_title(c, "Contact", sx, sy, sw)
    for lbl, val in [
        ("Ph:",   data["phone"]),
        ("Mail:", data["email"]),
        ("Loc:",  data["address"]),
        ("Web:",  data["website"]),
    ]:
        if val and sy > 20 * mm:
            sy = draw_contact_row(c, lbl, val, sx, sy, sw)

    sy -= 6

    # Skills
    if data["skills"] and sy > 60 * mm:
        sy = sidebar_section_title(c, "Skills", sx, sy, sw)
        tags = [s.strip() for s in data["skills"].split(",") if s.strip()]
        tx = sx
        for tag in tags:
            if sy < 35 * mm:
                break
            tw_px = c.stringWidth(tag, "Helvetica", 8) + 17
            if tx + tw_px > sx + sw + 2:
                tx = sx
                sy -= 6.5 * mm
            draw_skill_tag(c, tag, tx, sy, accent)
            tx += tw_px
        sy -= 8 * mm

    # Languages
    if data.get("languages") and sy > 50 * mm:
        sy = sidebar_section_title(c, "Languages", sx, sy, sw)
        for lang in [l.strip() for l in data["languages"].split(",") if l.strip()]:
            if sy < 25 * mm:
                break
            c.setFont("Helvetica", 8.5)
            c.setFillColorRGB(1, 1, 1, 0.90)
            c.drawString(sx, sy, lang)
            sy -= 6 * mm

    # ── MAIN CONTENT ──────────────────────────────────────────────────────────
    my = PAGE_H - HEADER_H - 7 * mm

    # Profile
    if data["summary"]:
        my = main_section_title(c, "Profile", MN_X, my, MN_W, accent)
        my = word_wrap(c, data["summary"], MN_X + 7, my, MN_W - 7,
                       "Helvetica", 9.2, 13.5, rgb=(0.18, 0.18, 0.28))
        my -= 7

    # Experience
    if data["experience"]:
        my = main_section_title(c, "Work Experience", MN_X, my, MN_W, accent)
        for entry in [e.strip() for e in data["experience"].split("\n\n") if e.strip()]:
            if my < 28 * mm:
                break
            lines = entry.split("\n")
            # Role
            c.setFillColorRGB(*accent)
            c.circle(MN_X + 3, my + 3, 2, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColorRGB(*darken(accent, 0.08))
            c.drawString(MN_X + 10, my, lines[0] if lines else "")
            my -= 11
            # Date tag
            if len(lines) > 1:
                date_txt = lines[1]
                tag_w = c.stringWidth(date_txt, "Helvetica", 8) + 10
                rr(c, MN_X + 10, my - 1, tag_w, 5 * mm, 2, lighten(accent, 0.42))
                c.setFont("Helvetica", 8)
                c.setFillColorRGB(*darken(accent, 0.15))
                c.drawString(MN_X + 15, my + 1, date_txt)
                my -= 8
            # Bullets
            if len(lines) > 2:
                for bullet in lines[2:]:
                    bullet = bullet.strip()
                    if not bullet or my < 28 * mm:
                        continue
                    c.setFillColorRGB(*lighten(accent, 0.15))
                    c.circle(MN_X + 13, my + 3, 1.5, fill=1, stroke=0)
                    my = word_wrap(c, bullet, MN_X + 19, my, MN_W - 19,
                                   "Helvetica", 9, 12.5, rgb=(0.22, 0.22, 0.32))
            my -= 2
            c.setStrokeColorRGB(*lighten(accent, 0.38))
            c.setLineWidth(0.5)
            c.setDash(2, 3)
            c.line(MN_X + 3, my + 2, MN_X + 3, my - 3)
            c.setDash()
            my -= 5

    # Education
    if data["education"]:
        my -= 2
        my = main_section_title(c, "Education", MN_X, my, MN_W, accent)
        for edu in [e.strip() for e in data["education"].split("\n\n") if e.strip()]:
            if my < 28 * mm:
                break
            lines = edu.split("\n")
            c.setFillColorRGB(*accent)
            c.circle(MN_X + 3, my + 3, 2, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColorRGB(*darken(accent, 0.08))
            c.drawString(MN_X + 10, my, lines[0] if lines else "")
            my -= 11
            if len(lines) > 1:
                c.setFont("Helvetica-Oblique", 8.5)
                c.setFillColorRGB(0.42, 0.42, 0.55)
                c.drawString(MN_X + 10, my, lines[1])
                my -= 10
            if len(lines) > 2:
                my = word_wrap(c, " ".join(lines[2:]), MN_X + 10, my, MN_W - 10,
                               "Helvetica", 8.8, 12, rgb=(0.30, 0.30, 0.42))
            my -= 6

    # Projects
    if data.get("projects") and my > 28 * mm:
        my -= 2
        my = main_section_title(c, "Projects & Certifications", MN_X, my, MN_W, accent)
        for item in [p.strip() for p in data["projects"].split("\n") if p.strip()]:
            if my < 28 * mm:
                break
            c.setFillColorRGB(*accent)
            c.circle(MN_X + 13, my + 3, 1.8, fill=1, stroke=0)
            my = word_wrap(c, item, MN_X + 20, my, MN_W - 20,
                           "Helvetica", 9, 13, rgb=(0.22, 0.22, 0.32))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    footer_h = 9 * mm
    c.setFillColorRGB(*sb_bg2)
    c.rect(0, 0, PAGE_W, footer_h, fill=1, stroke=0)
    c.setFillColorRGB(*accent)
    c.rect(0, footer_h - 2, PAGE_W, 2, fill=1, stroke=0)
    parts = [data["name"]]
    if data["phone"]:   parts.append(data["phone"])
    if data["email"]:   parts.append(data["email"])
    if data["address"]: parts.append(data["address"])
    c.setFont("Helvetica", 7.2)
    c.setFillColorRGB(1, 1, 1, 0.65)
    c.drawCentredString(PAGE_W / 2, 3 * mm, "  \u00b7  ".join(parts))

    c.save()
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════════════════════
#  STREAMLIT UI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="cv-header">
  <h1>💼 Professional CV Builder</h1>
  <p>Create a recruiter-ready, Canva-style CV and download it as a PDF in seconds.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎨 Accent Colour")
    theme_color = st.color_picker("", "#4338CA", label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### 📷 Profile Photo")
    user_photo = st.file_uploader("", type=["jpg", "jpeg", "png"],
                                  label_visibility="collapsed")
    if user_photo:
        st.image(user_photo, width=130)
    st.markdown("---")
    st.markdown("### 💡 Formatting Tips")
    st.markdown("""
- Separate multiple roles with a **blank line**
- **Line 1** → Role & Company
- **Line 2** → Date range
- **Lines 3+** → Bullet points
""")

# ── Personal Details ──────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">👤 Personal Details</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    name      = st.text_input("Full Name *",          placeholder="Alexandra Chen")
    job_title = st.text_input("Job Title *",           placeholder="Senior Product Designer")
with c2:
    email     = st.text_input("Email Address *",       placeholder="alex@email.com")
    phone     = st.text_input("📞 Phone Number",       placeholder="+65 9123 4567")
with c3:
    address   = st.text_input("📍 Location / City",    placeholder="Singapore")
    website   = st.text_input("🌐 LinkedIn / Website", placeholder="linkedin.com/in/alexchen")
st.markdown('</div>', unsafe_allow_html=True)

# ── Summary & Skills ──────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">📋 Summary & Skills</div>', unsafe_allow_html=True)
summary = st.text_area("Professional Summary",
    placeholder="Results-driven product designer with 6+ years crafting user-centred digital experiences for high-growth tech companies across Southeast Asia.",
    height=95)
col_sk, col_ln = st.columns(2)
with col_sk:
    skills    = st.text_input("🛠 Skills (comma-separated)",
        placeholder="Figma, User Research, Prototyping, Agile, HTML/CSS")
with col_ln:
    languages = st.text_input("🗣 Languages (comma-separated)",
        placeholder="English (Fluent), Mandarin (Native)")
st.markdown('</div>', unsafe_allow_html=True)

# ── Experience ────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">💼 Work Experience</div>', unsafe_allow_html=True)
st.caption("Separate roles with a blank line  ·  Line 1 = Role @ Company  ·  Line 2 = Dates  ·  Lines 3+ = Achievements")
experience = st.text_area("",
    placeholder=(
        "Senior Product Designer @ Grab\n"
        "Jan 2022 – Present · Singapore\n"
        "Led end-to-end redesign of checkout flow, reducing drop-off by 23%.\n"
        "Managed a cross-functional team of 5 designers across 3 time-zones.\n\n"
        "UX Designer @ Shopee\n"
        "Mar 2019 – Dec 2021 · Singapore\n"
        "Built a component library adopted across 12 product teams."
    ),
    height=190,
    label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# ── Education ─────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">🎓 Education</div>', unsafe_allow_html=True)
st.caption("Line 1 = Degree  ·  Line 2 = Institution & Year  ·  Line 3+ = Notes / Awards")
education = st.text_area("",
    placeholder=(
        "B.Sc. Human-Computer Interaction\n"
        "National University of Singapore · 2019\n"
        "Dean's List · Undergraduate Research Award"
    ),
    height=120,
    label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# ── Projects ──────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">🏆 Projects & Certifications  <span style="font-weight:400;opacity:.55">(optional)</span></div>', unsafe_allow_html=True)
projects = st.text_area("",
    placeholder=(
        "Redesigned NUS campus app — 50 k downloads within first month.\n"
        "Google UX Design Certificate · 2023\n"
        "Best Innovation Award — Tech Hackathon Singapore 2022"
    ),
    height=100,
    label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# ── Generate ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_btn, col_note = st.columns([2, 3])
with col_btn:
    generate = st.button("✨  Generate My Professional CV", use_container_width=True)
with col_note:
    st.caption("Your data stays in your browser — nothing is stored on any server.")

if generate:
    missing = [f for f, v in [("Full Name", name), ("Email", email), ("Job Title", job_title)] if not v]
    if missing:
        st.error(f"Please fill in: {', '.join(missing)}")
    else:
        photo_buf = make_circle_png(user_photo) if user_photo else None
        payload = dict(
            name=name, job_title=job_title, email=email,
            phone=phone, address=address, website=website,
            summary=summary, skills=skills, languages=languages,
            experience=experience, education=education, projects=projects,
        )
        with st.spinner("Crafting your CV…"):
            pdf_bytes = generate_cv_pdf(payload, theme_color, photo_buf)

        st.success("✅  Your CV is ready!")
        dl, _ = st.columns([1, 2])
        with dl:
            st.download_button(
                label="📥  Download PDF",
                data=pdf_bytes,
                file_name=f"{name.replace(' ', '_')}_CV.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        st.balloons()
