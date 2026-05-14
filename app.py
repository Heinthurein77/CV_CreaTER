import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageOps, ImageDraw
import io

# --- Page Setup ---
st.set_page_config(page_title="Pro CV Builder", layout="wide")

def make_circle(img_file):
    """Crop user image into a circle"""
    img = Image.open(img_file).convert("RGBA")
    img = ImageOps.fit(img, (300, 300), centering=(0.5, 0.5))
    mask = Image.new('L', (300, 300), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 300, 300), fill=255)
    img.putalpha(mask)
    return img

st.title("💼 Professional CV Generator")
st.write("Create a high-quality, Canvas-style CV in seconds (English Version)")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Profile Photo")
    user_photo = st.file_uploader("Upload your photo", type=['jpg', 'png', 'jpeg'])
    st.header("Customization")
    theme_color = st.color_picker("Pick Sidebar Color", "#2C3E50")
    
# --- Main Form ---
with st.form("cv_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", placeholder="John Doe")
        job_title = st.text_input("Job Title", placeholder="AI Business Analyst")
        email = st.text_input("Email", placeholder="example@gmail.com")
    with col2:
        phone = st.text_input("Phone", placeholder="+959...")
        address = st.text_input("Address", placeholder="Yangon, Myanmar")
        website = st.text_input("Website/LinkedIn", placeholder="linkedin.com/in/username")

    st.divider()
    summary = st.text_area("Professional Summary", placeholder="Briefly describe your career goals and expertise...")
    education = st.text_area("Education", placeholder="B.C.Sc (Computer University), 2025")
    experience = st.text_area("Work Experience", placeholder="Describe your previous roles and achievements...")
    skills = st.text_input("Skills", placeholder="Python, Docker, SQL, Project Management")

    submit = st.form_submit_button("Generate Premium CV")

if submit:
    if not name or not user_photo:
        st.error("Please provide both Name and Profile Photo.")
    else:
        # Create PDF object
        pdf = FPDF()
        pdf.add_page()
        
        # --- Sidebar (Rectangle) ---
        r, g, b = tuple(int(theme_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 0, 70, 297, 'F')

        # --- User Photo ---
        circular_img = make_circle(user_photo)
        img_byte_arr = io.BytesIO()
        circular_img.save(img_byte_arr, format='PNG')
        pdf.image(img_byte_arr, x=15, y=15, w=40)

        # --- Sidebar Content (White Text) ---
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", '', 10)
        pdf.set_xy(5, 65)
        contact_info = f"Phone:\n{phone}\n\nEmail:\n{email}\n\nAddress:\n{address}\n\nWeb:\n{website}"
        pdf.multi_cell(60, 7, txt=contact_info, align='L')
        
        # Skills in Sidebar
        pdf.ln(10)
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_x(5)
        pdf.cell(60, 10, "SKILLS", ln=True)
        pdf.set_font("helvetica", '', 10)
        for skill in skills.split(','):
            pdf.set_x(5)
            pdf.cell(60, 7, f"- {skill.strip()}", ln=True)

        # --- Main Content (Right Side) ---
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(75, 20)
        
        # Name & Title
        pdf.set_font("helvetica", 'B', 26)
        pdf.cell(0, 15, txt=name, ln=True)
        pdf.set_font("helvetica", 'B', 16)
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 10, txt=job_title.upper(), ln=True)
        
        pdf.ln(5)
        pdf.set_text_color(40, 40, 40)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, txt=summary)

        # Education Section
        pdf.ln(10)
        pdf.set_font("helvetica", 'B', 14)
        pdf.set_draw_color(r, g, b)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "EDUCATION", ln=True, border='B')
        pdf.ln(2)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, txt=education)

        # Experience Section
        pdf.ln(10)
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, "WORK EXPERIENCE", ln=True, border='B')
        pdf.ln(2)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, txt=experience)

        # --- Output & Download ---
        pdf_output = pdf.output()
        st.success("Your Professional CV is ready!")
        st.download_button(
            label="📥 Download CV (PDF)",
            data=bytes(pdf_output),
            file_name=f"{name.replace(' ', '_')}_CV.pdf",
            mime="application/pdf"
        )
