import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Pro CV Builder", layout="wide", page_icon="💼")

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #F7F8FC; }
h1 { font-size: 2rem !important; font-weight: 600 !important; }
.section-card {
    background: white;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 8px !important;
    border: 1.5px solid #E0E4EF !important;
    background: #FAFBFF !important;
}
.stButton > button {
    background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 14px rgba(79,70,229,0.35) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


def make_circle_png(img_file) -> bytes:
    img = Image.open(img_file).convert("RGBA")
    img = ImageOps.fit(img, (400, 400), centering=(0.5, 0.5))
    mask = Image.new("L", (400, 400), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 400, 400), fill=255)
    img.putalpha(mask)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def draw_rounded_rect(c, x, y, w, h, r, fill_color):
    """Draw a filled rounded rectangle on a reportlab canvas."""
    c.setFillColorRGB(*fill_color)
    c.roundRect(x, y, w, h, r, stroke=0, fill=1)


def wrap_text(c, text, x, y, max_width, font_name, font_size, line_height,
              color=(0.15, 0.15, 0.15), min_y=None):
    """Simple word-wrap renderer. Returns final y position."""
    c.setFont(font_name, font_size)
    c.setFillColorRGB(*color)
    words = text.split()
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width:
            line = test
        else:
            if min_y and y < min_y:
                return y
            c.drawString(x, y, line)
            y -= line_height
            line = word
    if line:
        if not (min_y and y < min_y):
            c.drawString(x, y, line)
        y -= line_height
    return y


def draw_section_header(c, label, x, y, width, accent_rgb):
    """Draw a section title with colored underline."""
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(*accent_rgb)
    c.drawString(x, y, label.upper())
    c.setStrokeColorRGB(*accent_rgb)
    c.setLineWidth(1.5)
    c.line(x, y - 3, x + width, y - 3)
    return y - 14


def draw_bullet_list(c, text, x, y, max_width, font_size=9.5, line_h=13,
                     accent_rgb=(0.31, 0.27, 0.9)):
    """Render bullet-separated or newline-separated list."""
    items = [t.strip() for t in text.replace("•", "\n").split("\n") if t.strip()]
    for item in items:
        if y < 30 * mm:
            break
        c.setFillColorRGB(*accent_rgb)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y + 1, "▸")
        c.setFillColorRGB(0.15, 0.15, 0.15)
        c.setFont("Helvetica", font_size)
        # word-wrap per bullet
        words = item.split()
        line = ""
        indent = x + 10
        first = True
        for word in words:
            test = (line + " " + word).strip()
            wrap_w = max_width - 10
            if c.stringWidth(test, "Helvetica", font_size) <= wrap_w:
                line = test
            else:
                c.drawString(indent, y, line)
                y -= line_h
                line = word
                indent = x + 10  # subsequent lines indent same
        if line:
            c.drawString(indent, y, line)
            y -= line_h
    return y


def generate_cv_pdf(data: dict, theme_hex: str, photo_buf) -> bytes:
    PAGE_W, PAGE_H = A4
    SIDEBAR_W = 68 * mm
    MARGIN_LEFT_MAIN = SIDEBAR_W + 10 * mm
    MARGIN_RIGHT = 12 * mm
    MAIN_W = PAGE_W - MARGIN_LEFT_MAIN - MARGIN_RIGHT
    TOP_BANNER_H = 48 * mm

    accent = hex_to_rgb(theme_hex)
    # Derive a lighter version for gradient feel
    light_accent = tuple(min(1.0, v + 0.22) for v in accent)
    dark_accent  = tuple(max(0.0, v - 0.12) for v in accent)

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    # ── SIDEBAR background ──────────────────────────────────────────────────────
    c.setFillColorRGB(*accent)
    c.rect(0, 0, SIDEBAR_W, PAGE_H, fill=1, stroke=0)

    # Subtle diagonal stripe texture on sidebar
    c.setStrokeColorRGB(*(min(1, v + 0.1) for v in accent))
    c.setLineWidth(0.3)
    for i in range(-20, 80, 6):
        c.line(i * mm, 0, i * mm + 20 * mm, PAGE_H)

    # ── TOP BANNER (right side) ─────────────────────────────────────────────────
    c.setFillColorRGB(*dark_accent)
    c.rect(SIDEBAR_W, PAGE_H - TOP_BANNER_H, PAGE_W - SIDEBAR_W, TOP_BANNER_H, fill=1, stroke=0)
    # Accent corner decoration
    c.setFillColorRGB(*light_accent)
    c.circle(PAGE_W - 10 * mm, PAGE_H - 5 * mm, 30 * mm, fill=1, stroke=0)
    c.setFillColorRGB(*accent)
    c.circle(PAGE_W - 5 * mm, PAGE_H, 18 * mm, fill=1, stroke=0)

    # ── PHOTO ───────────────────────────────────────────────────────────────────
    if photo_buf:
        photo_buf.seek(0)
        img_reader = ImageReader(photo_buf)
        photo_d = 38 * mm
        photo_x = (SIDEBAR_W - photo_d) / 2
        photo_y = PAGE_H - photo_d - 14 * mm
        # White border ring
        c.setFillColorRGB(1, 1, 1)
        c.circle(SIDEBAR_W / 2, photo_y + photo_d / 2, photo_d / 2 + 2.5 * mm, fill=1, stroke=0)
        c.drawImage(img_reader, photo_x, photo_y, photo_d, photo_d, mask="auto")

    # ── NAME & TITLE (banner area) ──────────────────────────────────────────────
    name_x = MARGIN_LEFT_MAIN
    name_y = PAGE_H - 18 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(name_x, name_y, data["name"])
    c.setFont("Helvetica", 13)
    c.setFillColorRGB(0.92, 0.92, 1.0)
    c.drawString(name_x, name_y - 10 * mm, data["job_title"])

    # Thin separator
    c.setStrokeColorRGB(1, 1, 1, 0.4)
    c.setLineWidth(0.8)
    c.line(name_x, name_y - 14 * mm, PAGE_W - MARGIN_RIGHT, name_y - 14 * mm)

    # ── SIDEBAR CONTENT ─────────────────────────────────────────────────────────
    sb_x = 6 * mm
    sb_w = SIDEBAR_W - 12 * mm
    sy = PAGE_H - 60 * mm   # Start below photo

    def sidebar_label(label, y):
        c.setFont("Helvetica-Bold", 8)
        c.setFillColorRGB(1, 1, 1, 0.65)
        c.drawString(sb_x, y, label.upper())
        return y - 5

    def sidebar_value(value, y, font_size=9):
        c.setFont("Helvetica", font_size)
        c.setFillColorRGB(1, 1, 1)
        # word-wrap
        words = value.split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, "Helvetica", font_size) <= sb_w:
                line = test
            else:
                c.drawString(sb_x, y, line)
                y -= 5 * mm
                line = w
        if line:
            c.drawString(sb_x, y, line)
            y -= 5 * mm
        return y

    # Contact section
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(sb_x, sy, "CONTACT")
    c.setStrokeColorRGB(1, 1, 1, 0.3)
    c.setLineWidth(0.7)
    c.line(sb_x, sy - 2, SIDEBAR_W - 6 * mm, sy - 2)
    sy -= 10

    icons = {"📞": data["phone"], "✉": data["email"],
             "📍": data["address"], "🌐": data["website"]}
    for icon, val in icons.items():
        if val:
            sy = sidebar_label(icon + "  " + val[:28], sy)
            sy -= 3

    sy -= 6

    # Skills section
    if data["skills"]:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(sb_x, sy, "SKILLS")
        c.line(sb_x, sy - 2, SIDEBAR_W - 6 * mm, sy - 2)
        sy -= 10
        skill_list = [s.strip() for s in data["skills"].split(",") if s.strip()]
        for skill in skill_list:
            if sy < 30 * mm:
                break
            # Pill background
            pill_w = min(sb_w, c.stringWidth(skill, "Helvetica", 9) + 10)
            draw_rounded_rect(c, sb_x, sy - 1, pill_w, 6.5 * mm, 3,
                              tuple(min(1.0, v + 0.18) for v in accent))
            c.setFont("Helvetica", 9)
            c.setFillColorRGB(1, 1, 1)
            c.drawString(sb_x + 5, sy + 1, skill)
            sy -= 9

    # Languages section
    if data.get("languages"):
        sy -= 4
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(sb_x, sy, "LANGUAGES")
        c.line(sb_x, sy - 2, SIDEBAR_W - 6 * mm, sy - 2)
        sy -= 10
        for lang in [l.strip() for l in data["languages"].split(",") if l.strip()]:
            c.setFont("Helvetica", 9)
            c.setFillColorRGB(1, 1, 1)
            c.drawString(sb_x + 4, sy, f"• {lang}")
            sy -= 7

    # ── MAIN CONTENT ────────────────────────────────────────────────────────────
    my = PAGE_H - TOP_BANNER_H - 8 * mm
    main_x = MARGIN_LEFT_MAIN

    # ── SUMMARY ─────────────────────────────────────────────────────────────────
    if data["summary"]:
        my = draw_section_header(c, "Profile", main_x, my, MAIN_W, accent)
        my = wrap_text(c, data["summary"], main_x, my, MAIN_W,
                       "Helvetica", 9.5, 13, color=(0.2, 0.2, 0.2))
        my -= 6

    # ── EXPERIENCE ──────────────────────────────────────────────────────────────
    if data["experience"]:
        my = draw_section_header(c, "Work Experience", main_x, my, MAIN_W, accent)
        entries = [e.strip() for e in data["experience"].split("\n\n") if e.strip()]
        for entry in entries:
            if my < 30 * mm:
                break
            lines = entry.split("\n")
            # First line = role/company (bold)
            if lines:
                c.setFont("Helvetica-Bold", 10)
                c.setFillColorRGB(*accent)
                c.drawString(main_x, my, lines[0])
                my -= 11
            # Second line = date/location (italic)
            if len(lines) > 1:
                c.setFont("Helvetica-Oblique", 8.5)
                c.setFillColorRGB(0.45, 0.45, 0.55)
                c.drawString(main_x, my, lines[1])
                my -= 10
            # Rest = description
            body = "\n".join(lines[2:]) if len(lines) > 2 else ""
            if body:
                my = draw_bullet_list(c, body, main_x + 2, my,
                                      MAIN_W - 2, 9, 12, accent)
            my -= 5

    # ── EDUCATION ───────────────────────────────────────────────────────────────
    if data["education"]:
        my -= 2
        my = draw_section_header(c, "Education", main_x, my, MAIN_W, accent)
        edu_entries = [e.strip() for e in data["education"].split("\n\n") if e.strip()]
        for edu in edu_entries:
            if my < 30 * mm:
                break
            lines = edu.split("\n")
            if lines:
                c.setFont("Helvetica-Bold", 10)
                c.setFillColorRGB(*accent)
                c.drawString(main_x, my, lines[0])
                my -= 11
            if len(lines) > 1:
                c.setFont("Helvetica-Oblique", 8.5)
                c.setFillColorRGB(0.45, 0.45, 0.55)
                c.drawString(main_x, my, lines[1])
                my -= 10
            if len(lines) > 2:
                c.setFont("Helvetica", 9)
                c.setFillColorRGB(0.2, 0.2, 0.2)
                my = wrap_text(c, " ".join(lines[2:]), main_x + 4, my,
                               MAIN_W - 4, "Helvetica", 9, 12)
            my -= 5

    # ── PROJECTS / EXTRA ────────────────────────────────────────────────────────
    if data.get("projects"):
        my -= 2
        my = draw_section_header(c, "Projects & Achievements", main_x, my, MAIN_W, accent)
        my = draw_bullet_list(c, data["projects"], main_x + 2, my,
                              MAIN_W - 2, 9.5, 13, accent)

    # ── FOOTER BAR ──────────────────────────────────────────────────────────────
    c.setFillColorRGB(*dark_accent)
    c.rect(0, 0, PAGE_W, 8 * mm, fill=1, stroke=0)
    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(1, 1, 1, 0.7)
    footer_text = f"{data['name']}  ·  {data['email']}  ·  {data['phone']}"
    c.drawCentredString(PAGE_W / 2, 2.5 * mm, footer_text)

    c.save()
    buf.seek(0)
    return buf.read()


# ── UI ─────────────────────────────────────────────────────────────────────────
st.title("💼 Professional CV Builder")
st.caption("Craft a Canva-quality CV in seconds — download as PDF instantly.")

with st.sidebar:
    st.markdown("### 🎨 Design")
    theme_color = st.color_picker("Accent color", "#4F46E5")
    st.markdown("---")
    st.markdown("### 📷 Photo")
    user_photo = st.file_uploader("Upload profile photo", type=["jpg", "jpeg", "png"])
    if user_photo:
        st.image(user_photo, width=140, caption="Preview")
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("Use `\\n\\n` between multiple experience/education entries to separate them. "
            "First line = role, second = dates, rest = description.")

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("#### 👤 Personal Details")
col1, col2, col3 = st.columns(3)
with col1:
    name      = st.text_input("Full Name *", placeholder="Alexandra Chen")
    email     = st.text_input("Email *",     placeholder="alex@email.com")
with col2:
    job_title = st.text_input("Job Title *",  placeholder="Senior Product Designer")
    phone     = st.text_input("Phone",        placeholder="+65 9123 4567")
with col3:
    address   = st.text_input("Location",     placeholder="Singapore")
    website   = st.text_input("LinkedIn / Website", placeholder="linkedin.com/in/alexchen")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("#### 📝 Summary & Skills")
summary  = st.text_area("Professional Summary",
    placeholder="A results-driven product designer with 6+ years crafting user-centred digital experiences…",
    height=100)
skills   = st.text_input("Skills (comma-separated)",
    placeholder="Figma, User Research, Prototyping, HTML/CSS, Agile")
languages = st.text_input("Languages (comma-separated)",
    placeholder="English (Fluent), Mandarin (Native)")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("#### 💼 Experience")
st.caption("Separate jobs with a blank line. Format: **Line 1** = Job Title @ Company | **Line 2** = Dates | **Lines 3+** = Description")
experience = st.text_area("Work Experience",
    placeholder="Product Designer @ Grab\nJan 2022 – Present\nLed end-to-end redesign of checkout flow, reducing drop-off by 23%.\nManaged cross-functional team of 5 designers.\n\nUX Designer @ Shopee\nMar 2019 – Dec 2021\nCreated component library adopted across 12 product teams.",
    height=180)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("#### 🎓 Education")
st.caption("Same format: Line 1 = Degree, Line 2 = Institution & Year")
education = st.text_area("Education",
    placeholder="B.Sc. in Human-Computer Interaction\nNational University of Singapore · 2019\nDean's List, Undergraduate Research Award",
    height=120)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("#### 🏆 Projects & Achievements *(optional)*")
projects = st.text_area("Projects / Certifications / Awards",
    placeholder="Redesigned NUS campus app — 50k downloads in first month.\nGoogle UX Design Certificate, 2023.",
    height=100)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
generate = st.button("✨ Generate My Professional CV")

if generate:
    if not name or not email or not job_title:
        st.error("Please fill in at least Name, Email, and Job Title.")
    else:
        photo_buf = make_circle_png(user_photo) if user_photo else None

        data = {
            "name": name, "job_title": job_title, "email": email,
            "phone": phone, "address": address, "website": website,
            "summary": summary, "skills": skills, "languages": languages,
            "experience": experience, "education": education, "projects": projects,
        }

        with st.spinner("Crafting your professional CV…"):
            pdf_bytes = generate_cv_pdf(data, theme_color, photo_buf)

        st.success("✅ Your CV is ready!")
        col_prev, col_dl = st.columns([3, 1])
        with col_dl:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"{name.replace(' ', '_')}_CV.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        st.balloons()
