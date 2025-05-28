# Streamlit-Based BeyondSkool Pricing Wizard (Refactored Version)

import streamlit as st
import math
import fitz  # PyMuPDF
from PIL import Image
import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# ---------- CONFIG ----------
st.set_page_config(page_title="BeyondSkool Pricing Wizard", layout="centered")

# ---------- HEADER ----------
logo = Image.open("BeyondSkool_logo.png")
st.image(logo, use_container_width=True)
st.title("BeyondSkool Pricing Wizard")
st.markdown("Empowering Schools with Transformative Learning Programs")

# ---------- INPUTS ----------
school_name = st.text_input("🏫 Name of the School")
your_email = st.text_input("📧 Your Email ID (BeyondSkool Creator)")
school_email = st.text_input("🏫 School's Email ID")

programs_selected = st.multiselect("📚 Select Program(s):", ["Communication", "Financial Literacy", "STEM"])
school_days = st.radio("📅 School operates:", ["5 days a week", "6 days a week"], horizontal=True)
max_sections_per_teacher = 27 if school_days == "5 days a week" else 32

# ---------- VALIDATION BEFORE CALCULATE ----------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

validation_errors = []
if st.button("Calculate Pricing"):
    if not school_name.strip():
        validation_errors.append("School name is required.")
    if not your_email.strip() or not is_valid_email(your_email):
        validation_errors.append("Valid creator email is required.")
    if not school_email.strip() or not is_valid_email(school_email):
        validation_errors.append("Valid school email is required.")
    if not programs_selected:
        validation_errors.append("At least one program must be selected.")

    if validation_errors:
        for error in validation_errors:
            st.error(error)
    else:
        st.session_state.update({
            "school_name": school_name,
            "your_email": your_email,
            "school_email": school_email,
            "programs_selected": programs_selected,
            "school_days": school_days,
            "calculate": True,
            "confirm": False
        })

# ---------- HELPER FUNCTIONS ----------

def calculate_pricing(programs_selected, student_info, school_days):
    # ... unchanged ...
    pass

def generate_spa_pdf(school_name, program_blocks, total_students, total_final_price, payment_term, payment_months):
    # ... unchanged ...
    pass

def show_success_toast(message):
    timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    st.success(f"{message} ✅\n\n*{timestamp}*")

def send_email_with_attachment(school_name, your_email, school_email, pdf_path):
    message = EmailMessage()
    message['Subject'] = f"BeyondSkool - School Partnership Agreement - {school_name}"
    message['From'] = os.getenv("EMAIL_USER")
    message['To'] = [school_email]
    message['Cc'] = [your_email, "adesh.koli@beyondskool.in", "accounts@beyondskool.in"]
    message['Bcc'] = ["atul@beyondskool.in"]
    message.set_content(f"""
Dear {school_name} Team,

Please find attached the School Partnership Agreement prepared by BeyondSkool.

Warm Regards,
BeyondSkool Partnerships Team
    """)

    with open(pdf_path, "rb") as file:
        message.add_attachment(file.read(), maintype='application', subtype='pdf', filename=pdf_path)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            smtp.send_message(message)
        show_success_toast("SPA emailed successfully")
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# ---------- SPA DOWNLOAD AND EMAIL FLOW ----------
if st.session_state.get("calculate") and st.session_state.get("confirm"):
    if st.button("📄 Generate SPA"):
        pdf_path = generate_spa_pdf(
            st.session_state["school_name"],
            [],  # placeholder for program_blocks
            0,   # placeholder for total_students
            0.0, # placeholder for total_final_price
            "Full Payment in Advance",
            ["April"]
        )
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download SPA PDF", data=f.read(), file_name=pdf_path)
            show_success_toast("SPA downloaded successfully")

    if st.button("✉️ Email SPA"):
        pdf_path = f"SPA_{st.session_state['school_name'].replace(' ', '_')}.pdf"
        send_email_with_attachment(
            st.session_state["school_name"],
            st.session_state["your_email"],
            st.session_state["school_email"],
            pdf_path
        )

# (Other functions remain unchanged)
