import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageOps, ImageDraw
import io

# --- Page Setup ---
st.set_page_config(page_title="Professional Burmese CV Builder", layout="wide")

def make_circle(img_file):
    """User ပုံကို ဝိုင်းဝိုင်းလေး ဖြစ်အောင် လုပ်ပေးတဲ့ function"""
    img = Image.open(img_file).convert("RGBA")
    img = ImageOps.fit(img, (300, 300), centering=(0.5, 0.5))
    mask = Image.new('L', (300, 300), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 300, 300), fill=255)
    img.putalpha(mask)
    return img

st.title("🎨 Premium Burmese CV Builder")
st.write("Canvas Style Professional CV များကို အခမဲ့ ဖန်တီးပါ")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("ကိုယ်ရေးအချက်အလက်")
    user_photo = st.file_uploader("ဓာတ်ပုံတင်ပါ", type=['jpg', 'png', 'jpeg'])
    bg_color = st.color_picker("Sidebar အရောင်ရွေးပါ", "#2C3E50")
    
# --- Main Form ---
with st.form("cv_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("အမည်အပြည့်အစုံ")
        job_title = st.text_input("ရာထူး/အလုပ်အကိုင်")
        email = st.text_input("အီးမေးလ်")
    with col2:
        phone = st.text_input("ဖုန်းနံပါတ်")
        address = st.text_input("နေရပ်လိပ်စာ")
        website = st.text_input("Portfolio/Social Link")

    st.divider()
    summary = st.text_area("မိမိအကြောင်း အကျဉ်းချုပ် (Professional Summary)")
    education = st.text_area("ပညာအရည်အချင်း (စာကြောင်းတစ်ကြောင်းချင်းစီ ခွဲရေးပါ)")
    experience = st.text_area("လုပ်ငန်းအတွေ့အကြုံ")
    skills = st.text_input("ကျွမ်းကျင်မှုများ (ကော်မာ ခြားရေးပါ - ဥပမာ Python, Design, Management)")

    submit = st.form_submit_button("Premium CV ထုတ်မည်")

if submit:
    if not name or not user_photo:
        st.error("အမည်နဲ့ ဓာတ်ပုံ ထည့်ပေးဖို့ လိုပါတယ်ခင်ဗျာ။")
    else:
        pdf = FPDF()
        pdf.add_page()
        
        # Unicode Font (Pyidaungsu.ttf ရှိရပါမယ်)
        try:
            pdf.add_font('Pyidaungsu', '', 'Pyidaungsu.ttf', uni=True)
            pdf.add_font('Pyidaungsu', 'B', 'Pyidaungsu.ttf', uni=True) # Bold အဖြစ်လည်း သုံးမယ်
        except:
            st.error("Font ဖိုင် ရှာမတွေ့ပါ။ Pyidaungsu.ttf ကို Folder ထဲ ထည့်ပေးပါ။")
            st.stop()

        # --- Sidebar Design (Rectangle) ---
        r, g, b = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 0, 70, 297, 'F')

        # --- User Photo ---
        circular_img = make_circle(user_photo)
        img_byte_arr = io.BytesIO()
        circular_img.save(img_byte_arr, format='PNG')
        pdf.image(img_byte_arr, x=15, y=15, w=40)

        # --- Sidebar Content (White Text) ---
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Pyidaungsu', '', 10)
        pdf.set_xy(5, 65)
        pdf.multi_cell(60, 7, txt=f"📞 {phone}\n📧 {email}\n📍 {address}\n🌐 {website}", align='L')
        
        pdf.ln(10)
        pdf.set_font('Pyidaungsu', 'B', 12)
        pdf.set_x(5)
        pdf.cell(60, 10, "SKILLS", ln=True)
        pdf.set_font('Pyidaungsu', '', 10)
        for skill in skills.split(','):
            pdf.set_x(5)
            pdf.cell(60, 7, f"• {skill.strip()}", ln=True)

        # --- Main Content (Right Side) ---
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(75, 20)
        
        # Name & Title
        pdf.set_font('Pyidaungsu', 'B', 24)
        pdf.cell(0, 15, txt=name, ln=True)
        pdf.set_font('Pyidaungsu', '', 16)
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 10, txt=job_title.upper(), ln=True)
        
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Pyidaungsu', '', 11)
        pdf.multi_cell(0, 7, txt=summary)

        # Education
        pdf.ln(10)
        pdf.set_font('Pyidaungsu', 'B', 14)
        pdf.set_draw_color(r, g, b)
        pdf.cell(0, 10, "EDUCATION", ln=True, border='B')
        pdf.ln(2)
        pdf.set_font('Pyidaungsu', '', 11)
        pdf.multi_cell(0, 7, txt=education)

        # Experience
        pdf.ln(10)
        pdf.set_font('Pyidaungsu', 'B', 14)
        pdf.cell(0, 10, "WORK EXPERIENCE", ln=True, border='B')
        pdf.ln(2)
        pdf.set_font('Pyidaungsu', '', 11)
        pdf.multi_cell(0, 7, txt=experience)

        # --- Download Button ---
        pdf_output = pdf.output()
        st.success("Professional CV ထွက်လာပါပြီ!")
        st.download_button(
            label="📥 Download High-Quality CV",
            data=bytes(pdf_output),
            file_name=f"{name}_Premium_CV.pdf",
            mime="application/pdf"
        )