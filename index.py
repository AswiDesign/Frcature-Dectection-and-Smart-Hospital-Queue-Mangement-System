import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime
import time

# =====================================================
# MUST BE FIRST STREAMLIT COMMAND
# =====================================================
st.set_page_config(
    page_title="AI Fracture Detection & Hospital Queue",
    layout="wide"
)

# =====================================================
# APP TITLE
# =====================================================
st.title("🏥 AI-Based Fracture Detection & Smart Queue System")

# =====================================================
# SIDEBAR NAVIGATION
# =====================================================
menu = st.sidebar.radio(
    "Select Module",
    ["🦴 Fracture Detection AI", "📋 Hospital Queue Management"]
)

# =====================================================
# SESSION STATE INITIALIZATION (QUEUE)
# =====================================================
if "queue" not in st.session_state:
    st.session_state.queue = []

if "token_counter" not in st.session_state:
    st.session_state.token_counter = 1000

if "current_token" not in st.session_state:
    st.session_state.current_token = None


# =====================================================
# 🔔 REMINDER (APP NOTIFICATION – SMS SIMULATION)
# =====================================================
def send_reminder(phone, token):
    reminder_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    st.toast(
        f"📩 Reminder to {phone}\n"
        f"Your token #{token} is NEXT\n"
        f"Date & Time: {reminder_time}",
        icon="🔔"
    )


# =====================================================
# 🦴 FRACTURE DETECTION MODULE
# =====================================================
def fracture_module():
    st.header("🦴 Fracture Detection & Recovery Analysis")

    st.sidebar.subheader("Detection Mode")
    mode = st.sidebar.radio(
        "Choose Input Method:",
        ["Upload Image", "Real-time Camera"]
    )

    col1, col2 = st.columns(2)

    def analyze_fracture(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        fracture_percentage = min(len(contours), 100)
        return fracture_percentage

    def estimate_recovery(fracture_percentage):
        if fracture_percentage < 30:
            return "Mild", 3, 0.75
        elif fracture_percentage < 70:
            return "Moderate", 6, 1.5
        else:
            return "Severe", 12, 3

    if mode == "Upload Image":
        with col1:
            uploaded_file = st.file_uploader(
                "Upload X-ray Image",
                type=["jpg", "jpeg", "png"]
            )

            if uploaded_file:
                image = Image.open(uploaded_file)
                image_np = np.array(image)

                if len(image_np.shape) == 2:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)

                st.image(image, use_column_width=True)

                if st.button("🔍 Analyze"):
                    fracture_pct = analyze_fracture(image_np)
                    severity, weeks, months = estimate_recovery(fracture_pct)

                    with col2:
                        st.subheader("📊 Results")
                        st.metric("Fracture Severity", f"{fracture_pct}%")
                        st.progress(fracture_pct / 100)

                        st.info(
                            f"""
                            **Severity:** {severity}  
                            **Recovery Time:**  
                            • Weeks: {weeks}  
                            • Months: {months}
                            """
                        )

    else:
        st.subheader("📹 Real-time Camera")
        if st.button("Start Camera"):
            cap = cv2.VideoCapture(0)
            frame = st.empty()

            for _ in range(100):
                ret, img = cap.read()
                if not ret:
                    break
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                frame.image(img, use_column_width=True)

            cap.release()
            st.success("Camera capture complete")


# =====================================================
# 📋 HOSPITAL QUEUE MANAGEMENT MODULE
# =====================================================
def queue_module():
    st.header("📋 Hospital Queue Management System")

    admin_menu = st.sidebar.radio(
        "Admin Panel",
        ["Patient Registration", "Queue Status", "Call Next Patient"]
    )

    # ===============================
    # PATIENT REGISTRATION
    # ===============================
    if admin_menu == "Patient Registration":
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Patient Name")
            phone = st.text_input("Phone Number")

        with col2:
            department = st.selectbox(
                "Department",
                ["Orthopedics", "Cardiology", "Neurology", "General"]
            )
            doctor = st.text_input("Doctor Name")

        if st.button("Generate Token"):
            if name and phone:
                token = st.session_state.token_counter
                st.session_state.queue.append({
                    "Token": token,
                    "Name": name,
                    "Phone": phone,
                    "Department": department,
                    "Doctor": doctor,
                    "Status": "Waiting",
                    "Time": datetime.now().strftime("%H:%M:%S")
                })
                st.session_state.token_counter += 1
                st.success(f"Token Generated: {token}")
            else:
                st.error("All fields required")

    # ===============================
    # QUEUE STATUS
    # ===============================
    elif admin_menu == "Queue Status":
        if st.session_state.queue:
            df = pd.DataFrame(st.session_state.queue)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No patients in queue")

    # ===============================
    # CALL NEXT PATIENT + REMINDER
    # ===============================
    elif admin_menu == "Call Next Patient":
        waiting = [p for p in st.session_state.queue if p["Status"] == "Waiting"]

        if waiting:
            current = waiting[0]
            st.warning(f"Calling Token: {current['Token']}")

            if st.button("Call Patient"):
                current["Status"] = "Called"
                st.success(f"Token {current['Token']} Called")

                # 🔔 Send reminder to NEXT patient
                idx = st.session_state.queue.index(current)
                if idx + 1 < len(st.session_state.queue):
                    next_patient = st.session_state.queue[idx + 1]
                    if next_patient["Status"] == "Waiting":
                        send_reminder(
                            next_patient["Phone"],
                            next_patient["Token"]
                        )
        else:
            st.success("All patients served")

    # ===============================
    # PATIENT VIEW
    # ===============================
    st.sidebar.markdown("---")
    st.sidebar.subheader("Patient Status")

    token_input = st.sidebar.number_input(
        "Enter Token Number",
        min_value=1000,
        step=1
    )

    if token_input:
        patient = next(
            (p for p in st.session_state.queue if p["Token"] == token_input),
            None
        )

        if patient:
            st.sidebar.write(f"Status: **{patient['Status']}**")
            if patient["Status"] == "Called":
                st.sidebar.success("🎉 Your turn!")
        else:
            st.sidebar.error("Token not found")


# =====================================================
# ROUTER
# =====================================================
if menu == "🦴 Fracture Detection AI":
    fracture_module()
else:
    queue_module()

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption(
    "⚠️ Educational project only. Not for real medical diagnosis."
)
