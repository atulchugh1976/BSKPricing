import streamlit as st
import math
import pandas as pd
import fitz
from PIL import Image
import smtplib
import os
from dotenv import load_dotenv
load_dotenv()
from email.message import EmailMessage
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="BeyondSkool Pricing Wizard", layout="centered")

# ---------- BRANDING ----------
logo = Image.open("BeyondSkool_logo.png")
st.image(logo, use_container_width=True)
st.title("BeyondSkool Pricing Wizard")
st.markdown("Empowering Schools with Transformative Learning Programs")

# ---------- INPUT SECTION ----------
# Payment terms logic moved below post-confirmation.)
school_name = st.text_input("🏫 Name of the School")
your_email = st.text_input("📧 Your Email ID (BeyondSkool Creator)")
school_email = st.text_input("🏫 School's Email ID")
programs_selected = st.multiselect("📚 Select Program(s):", ["Communication", "Financial Literacy", "STEM"])
school_days = st.radio("📅 School operates:", ["5 days a week", "6 days a week"], horizontal=True)
max_sections_per_teacher = 27 if school_days == "5 days a week" else 32

student_info = {}
if programs_selected:
    for prog in programs_selected:
        students = st.number_input(f"🎓 Number of Students - {prog}", min_value=50, max_value=3000, step=50, key=f"students_{prog}")
        section_size = st.number_input(f"👩‍🏫 Students per Section - {prog}", min_value=10, max_value=60, step=5, value=30, key=f"section_{prog}")
        student_info[prog] = {"students": students, "section_size": section_size}

    if st.button("Calculate Pricing"):
        st.session_state.update({
            "school_name": school_name,
            "your_email": your_email,
            "school_email": school_email,
            "programs_selected": programs_selected,
            "student_info": student_info,
            "school_days": school_days,
            "calculate": True,
            "confirm": False
        })

# ---------- PRICING OUTPUT ----------
if st.session_state.get("calculate"):
    discount_percent = st.slider("🎯 Discount %", 0, 40, 0)

    student_info = st.session_state["student_info"]
    programs_selected = st.session_state["programs_selected"]
    school_name = st.session_state["school_name"]
    school_days = st.session_state["school_days"]
    max_sections_per_teacher = 27 if school_days == "5 days a week" else 32

    total_cost = 0
    total_students = 0
    total_final_price = 0
    program_blocks = []

    for prog in programs_selected:
        data = student_info[prog]
        students = data["students"]
        section_size = data["section_size"]
        sections = math.ceil(students / section_size)

        full_teachers = 0
        variable_teacher_days = 0
        teacher_day_cost = 0

        if sections < 20:
            full_teachers = 0
            variable_teacher_days = math.ceil(sections / 5)
            teacher_day_cost = variable_teacher_days * 2000 * 35
        else:
            full_teachers = sections // max_sections_per_teacher
            remaining = sections % max_sections_per_teacher
            if 0 < remaining < 20:
                variable_teacher_days = math.ceil(remaining / 5)
                teacher_day_cost = variable_teacher_days * 2000 * 35
            elif remaining >= 20:
                full_teachers += 1
                variable_teacher_days = 0
                teacher_day_cost = 0

            # Add 10% coverage for full-time teachers' absence via variable teachers
            full_time_sessions = full_teachers * max_sections_per_teacher * 35
            absent_sessions = math.ceil(full_time_sessions * 0.10)
            absent_days = math.ceil(absent_sessions / 5)
            teacher_day_cost += absent_days * 2000

        teacher_cost = 425000 if prog == "STEM" else 400000
        teacher_cost_total = full_teachers * teacher_cost
        book_cost = students * 200
        kit_cost = 115000 if prog == "STEM" else 0
        manager_cost = 50000

        program_cost = teacher_cost_total + teacher_day_cost + book_cost + kit_cost
        total_program_cost = program_cost + manager_cost

        base_price = total_program_cost / (1 - 0.4)
        final_price = base_price * (1 - discount_percent / 100)
        price_per_student = final_price / students

        total_cost += total_program_cost
        total_students += students
        total_final_price += final_price

        program_blocks.append({
            "Program": prog,
            "Students": students,
            "Sections": sections,
            "Full-Time Teachers": full_teachers,
            "Variable Teacher Days": variable_teacher_days,
            "Price per Student": round(price_per_student),
            "Total Program Price": round(final_price)
        })

    gross_margin = ((total_final_price - total_cost) / total_final_price) * 100
    st.markdown(f"""<div style='position:fixed; bottom:10px; right:10px; color:white; background-color:white; padding:5px; border-radius:5px; font-size:10px;'>Gross Margin: {gross_margin:.2f}%</div>""", unsafe_allow_html=True)

    if gross_margin < 30:
        st.error(" No Pricing can be offered.")
    else:
        st.header("📊 Pricing Summary")
        for block in program_blocks:
            st.markdown(f"""
            ### 📚 {block['Program']}
            - 🎓 Students: {block['Students']}
            - 📈 Sections: {block['Sections']}
            - 👩‍🏫 Full-Time Teachers: {block['Full-Time Teachers']}
            - 👨‍🏫 Variable Teacher Days: {block['Variable Teacher Days']}
            - 💰 Price per Student: Rs.{block['Price per Student']}
            - 💵 Total Program Price: Rs.{block['Total Program Price']:,}
            """)

        st.subheader(f"Total Price: Rs.{round(total_final_price):,}")
        st.subheader(f"Average Price per Student: Rs.{round(total_final_price / total_students)}")

        if not st.session_state.get("confirm"):
            if st.button("✅ Confirm Pricing"):
                st.session_state["confirm"] = True

# ---------- SPA GENERATION + PAYMENT TERMS + DOWNLOAD/EMAIL ----------

    # Payment terms (post-confirmation only)
    payment_options = ["Full Payment in Advance", "Half Yearly", "Quarterly"]
    payment_term = st.selectbox("💳 Payment Terms", payment_options)

    payment_months = []
    if payment_term == "Half Yearly":
        payment_months.append(st.selectbox("Select 1st Installment Month", ["April", "May", "June", "July", "August", "September"], key="half1"))
        payment_months.append(st.selectbox("Select 2nd Installment Month", ["October", "November", "December", "January", "February", "March"], key="half2"))
    elif payment_term == "Quarterly":
        payment_months.append(st.selectbox("Select 1st Installment Month", ["April", "May", "June"], key="q1"))
        payment_months.append(st.selectbox("Select 2nd Installment Month", ["July", "August", "September"], key="q2"))
        payment_months.append(st.selectbox("Select 3rd Installment Month", ["October", "November", "December", "January", "February", "March"], key="q3"))
    else:
        payment_months.append(st.selectbox("Select Payment Month", ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"], key="full"))
if st.session_state.get("confirm") and (gross_margin >= 30):
    spa_output_path = f"SPA_{school_name.replace(' ', '_')}.pdf"
    today = datetime.today().strftime('%d-%m-%Y')

    doc = fitz.open()
    page = doc.new_page()

    try:
        logo = Image.open("BeyondSkool_logo.png")
        rect = fitz.Rect(50, 30, 250, 80)
        page.insert_image(rect, filename="BeyondSkool_logo.png")
        y = 100
    except:
        y = 50

    page.insert_text((50, y), "School Partnership Agreement", fontsize=16)
    y += 30
    detailed_intro = f"This School partnership Agreement is entered on this {today} sets the terms and understanding between Ivy Minds Learning Solutions Private Ltd., through their proprietary brand “BeyondSkool” having their registered office at No 927, Summit Business Bay, Andheri East, CTC No 266 and 166 to 172 of Village Gundavali, Mumbai, Maharashtra 400093 referred to as the Party of the First Part and {school_name} hereinafter referred to as the Party of the Second part."
    rect = fitz.Rect(50, y, 550, y + 100)
    page.insert_textbox(rect, detailed_intro, fontsize=11, align=0)
    y += 100
    purpose = f"""Purpose
This School Partnership Agreement shall list the detailed working relationship between BeyondSkool and {school_name} setting the outline and all terms and conditions."""
    rect = fitz.Rect(50, y, 550, y + 60)
    page.insert_textbox(rect, purpose, fontsize=11, align=0)
    y += 70
    y += 40
    page.insert_text((50, y), f"This agreement is made on {today} between:", fontsize=12)
    y += 20
    page.insert_text((50, y), "Ivy Minds Learning Solutions Pvt Ltd  (\"BeyondSkool\")", fontsize=12)
    y += 20
    page.insert_text((50, y), f"and {school_name} (\"School\").", fontsize=12)
    y += 40

    page.insert_text((50, y), "Program Details:", fontsize=14)
    y += 30
    for block in program_blocks:
        prog_detail_text = f"""📘 {block['Program']}

🔹 **BeyondSkool Responsibility:**
1. Deliver the chosen program through trained teachers in the school
2. Conduct one session per week per class
3. Provide teachers: {block['Full-Time Teachers']} full-time and {block['Variable Teacher Days']} variable teacher days/week (approx.)
4. Provide all necessary teaching and learning materials
5. Provide LMS access for teachers and students
6. Conduct regular assessments and share digital reports
7. Support Parent-Teacher Meetings and Orientations
8. Conduct student showcase events as scheduled
9. Assign a program manager
10. Share bi-monthly progress reports.

🔹 **School Responsibility:**
1. Share time-table for program sessions
2. Provide student data for LMS setup
3. Ensure classrooms have projector/digital access
4. Allow BeyondSkool teacher for PTMs
5. Assign a school coordinator
6. Provide slots for quarterly review with BeyondSkool
7. Provide dates for showcases and extra class slots if needed
8. Share grade-wise book quantity (billing based on this)
9. Provide contacts for accounts/finance matters"""
        rect = fitz.Rect(50, y, 550, y + 300)
        page.insert_textbox(rect, prog_detail_text, fontsize=10, align=0)
        y += 310
    y += 30
    for block in program_blocks:
        page.insert_text((60, y), f"- {block['Program']} Program: {block['Students']} Students at Rs.{block['Price per Student']}/Student", fontsize=11)
        y += 20
    page.insert_text((50, y), f"Total Students: {total_students}", fontsize=11)
    y += 20
    page.insert_text((50, y), f"Total Price: **Rs {round(total_final_price):,}**", fontsize=11)
    y += 20
    page.insert_text((50, y), f"🔸 **Payment Terms:** {payment_term}", fontsize=11)
    y += 20
    page.insert_text((50, y), f"🔸 **Payment Months:** {', '.join(payment_months)}", fontsize=11)
    y += 40

    clauses = [
        "🔸 **1. Scope:** BeyondSkool will deliver the selected programs at School premises through qualified faculty.",
        "🔸 **2. Academic Year:** This Agreement is valid for the academic session 2025-26 unless extended by mutual consent.",
        "🔸 **3. Student Material:** BeyondSkool will provide kits, books, and other required material as applicable.",
        "🔸 **4. Payment Terms:** Payments are to be made against invoices as per mutually agreed schedules.",
        "🔸 **5. Taxes:** All taxes as applicable are extra unless explicitly mentioned as inclusive.",
        "🔸 **6. Confidentiality:** Both parties will maintain confidentiality of all shared proprietary information.",
        "🔸 **7. Indemnity:** Each party indemnifies the other against claims arising out of negligence or misconduct.",
        "🔸 **8. Termination:** Either party may terminate this Agreement with a 30-day written notice.",
        "🔸 **9. Jurisdiction:** All disputes will be subject to the exclusive jurisdiction of Mumbai courts."
    ]
    for clause in clauses:
        rect = fitz.Rect(50, y, 550, y + 40)
        page.insert_textbox(rect, clause, fontsize=11, align=0)
        y += 30

    y += 30
    page.insert_text((50, y), "Accepted and Agreed:", fontsize=14)
    y += 30
    page.insert_text((50, y), "For Ivy Minds Learning Solutions Pvt LTD ", fontsize=12)
    page.insert_text((300, y), f"For {school_name}", fontsize=12)

    # ---------- COMMERCIAL TABLE ----------
    spa_commercial_rows = []
    for block in program_blocks:
        prog = block["Program"]
        students = block["Students"]
        sections = block["Sections"]
        price_per_student = block["Price per Student"]

        book_base = 1200 if prog in ["Communication", "Financial Literacy"] else 1800
        if price_per_student <= book_base:
            book_price = price_per_student
            service_fee = 0
            gst = 0
        else:
            book_price = book_base
            service_fee = price_per_student - book_base
            gst = round(service_fee * 0.18)

        spa_commercial_rows.append({
            "Program": prog,
            "Students": students,
            "Sections": sections,
            "Book Price": book_price,
            "Service Fee": service_fee,
            "GST on Service": gst
        })

    y += 40
    page.insert_text((50, y), "🔹 **Commercial Terms:**", fontsize=14)
    y += 30
    page.insert_text((50, y), f"Payment Terms: **{payment_term}**", fontsize=11)
    y += 20
    page.insert_text((50, y), f"Payment Months: **{', '.join(payment_months)}**", fontsize=11)
    y += 30
    # Table header
    headers = ["Program", "Students", "Sections", "Book Price", "Service Fee", "GST"]
    col_widths = [110, 80, 80, 100, 100, 80]
    x_start = 50
    x = x_start
    for i, header in enumerate(headers):
        page.insert_text((x, y), header, fontsize=10)
        x += col_widths[i]
    y += 20
    # Table rows
    for row in spa_commercial_rows:
        x = x_start
        row_data = [
            row["Program"],
            str(row["Students"]),
            str(row["Sections"]),
            f"₹{row['Book Price']}",
            f"₹{row['Service Fee']}",
            f"₹{row['GST on Service']}"
        ]
        for i, cell in enumerate(row_data):
            page.insert_text((x, y), cell, fontsize=10)
            x += col_widths[i]
        y += 20
        if y > 750:
            page = doc.new_page()
            y = 50

    total_book_cost = sum(row['Book Price'] * row['Students'] for row in spa_commercial_rows)
    total_service_fee = sum(row['Service Fee'] * row['Students'] for row in spa_commercial_rows)
    total_gst = sum(row['GST on Service'] * row['Students'] for row in spa_commercial_rows)
    total_payable = total_book_cost + total_service_fee + total_gst

    y += 30
    page.insert_text((50, y), f"Total Book Cost: **Rs {total_book_cost:,}**", fontsize=11)
    y += 20
    page.insert_text((50, y), f"Total Service Fee: **Rs {total_service_fee:,}**", fontsize=11)
    y += 20
    page.insert_text((50, y), f"Total GST on Services: **Rs {total_gst:,}**", fontsize=11)
    y += 20
    page.insert_text((50, y), f"🔸 **Total Payable (Books + Services + GST): Rs {round(total_payable):,}**", fontsize=11)

    # Add a page break before signatures
    page = doc.new_page()
    y = 50
    page.insert_text((220, y), "🔏 Signatures", fontsize=14)
    y += 40
    page.insert_text((50, y), "For Ivy Minds Learning Solutions Pvt Ltd", fontsize=12)
    page.insert_text((350, y), f"For {school_name}", fontsize=12)
    y += 60
    page.insert_text((50, y), "Name: ___________________", fontsize=10)
    page.insert_text((350, y), "Name: ___________________", fontsize=10)
    y += 20
    page.insert_text((50, y), "Designation: _____________", fontsize=10)
    page.insert_text((350, y), "Designation: _____________", fontsize=10)
    y += 20
    page.insert_text((50, y), "Date: ____________________", fontsize=10)
    page.insert_text((350, y), "Date: ____________________", fontsize=10)

    doc.save(spa_output_path)
    doc.close()

    with open(spa_output_path, "rb") as file:
        pdf_data = file.read()

    st.download_button("📄 Download SPA", data=pdf_data, file_name=spa_output_path)

    
    if st.button("✉️ Email SPA"):
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
        message.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=spa_output_path)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
                smtp.send_message(message)
            st.success("🎉 SPA Created and Sent Successfully!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
