import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime
from PIL import Image
import io

# Streamlit page configuration
st.set_page_config(page_title="AI-Powered Skin Outbreak Tracker", layout="wide")

# Backend API URL
API_URL = "http://localhost:8000"

# Sidebar for navigation
st.sidebar.title("Skin Outbreak Tracker")
page = st.sidebar.radio("Navigate", ["Profile", "Photo Upload", "Lifestyle Tracking", "Dashboard"])

# Mock user ID (replace with auth in production)
USER_ID = "user_1"

# Profile Page
if page == "Profile":
    st.header("User Profile")
    with st.form("profile_form"):
        name = st.text_input("Full Name")
        dob = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1))
        height = st.number_input("Height (cm)", min_value=100, max_value=250)
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200)
        gender = st.selectbox("Gender (Optional)", ["Not Specified", "Male", "Female"])
        submit = st.form_submit_button("Save Profile")
        if submit:
            profile_data = {
                "name": name,
                "dob": dob.isoformat(),
                "height": height,
                "weight": weight,
                "gender": gender
            }
            try:
                response = requests.post(f"{API_URL}/profile/", json=profile_data)
                response.raise_for_status()
                st.success("Profile saved!")
            except requests.RequestException as e:
                st.error(f"Failed to save profile: {e}")

    # Display current profile
    try:
        response = requests.get(f"{API_URL}/profile/{USER_ID}")
        if response.status_code == 200:
            profile = response.json()
            st.write("Current Profile:")
            st.json(profile)
        else:
            st.write("No profile found.")
    except requests.RequestException:
        st.error("Failed to fetch profile.")

# Photo Upload Page
elif page == "Photo Upload":
    st.header("Upload Face Photo")
    upload_method = st.radio("Choose upload method", ["File Upload", "Webcam"])
    
    if upload_method == "File Upload":
        uploaded_file = st.file_uploader("Upload a face photo (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Photo", use_column_width=True)
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=image.format)
            img_byte_arr = img_byte_arr.getvalue()
            try:
                response = requests.post(f"{API_URL}/photo/", files={"file": (uploaded_file.name, img_byte_arr)})
                response.raise_for_status()
                result = response.json()
                st.write(f"Severity Score: {result['severity_score']}/100")
                st.write("Heatmap overlay (to be implemented)")
            except requests.RequestException as e:
                st.error(f"Failed to process photo: {e}")
    
    else:
        photo = st.camera_input("Take a photo")
        if photo:
            image = Image.open(photo)
            st.image(image, caption="Captured Photo", use_column_width=True)
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()
            try:
                response = requests.post(f"{API_URL}/photo/", files={"file": ("photo.png", img_byte_arr)})
                response.raise_for_status()
                result = response.json()
                st.write(f"Severity Score: {result['severity_score']}/100")
            except requests.RequestException as e:
                st.error(f"Failed to process photo: {e}")

# Lifestyle Tracking Page
elif page == "Lifestyle Tracking":
    st.header("Lifestyle Tracking")
    with st.form("lifestyle_form"):
        date = st.date_input("Date", value=datetime.now())
        diet_sugar = st.slider("Sugar Intake (1-10)", 1, 10)
        diet_dairy = st.slider("Dairy Intake (1-10)", 1, 10)
        sleep_hours = st.number_input("Sleep Hours", min_value=0.0, max_value=24.0, step=0.5)
        stress_level = st.slider("Stress Level (1-10)", 1, 10)
        product_used = st.text_input("Skincare Products Used (e.g., sunscreen, face wash)")
        sunlight_hours = st.number_input("Sunlight Exposure (hours)", min_value=0.0, max_value=24.0, step=0.5)
        menstrual_cycle = st.checkbox("Menstrual Cycle Active (if applicable)")
        travel_location = st.text_input("Travel Location (City, optional)")
        submit = st.form_submit_button("Log Data")
        if submit:
            lifestyle_data = {
                "date": date.isoformat(),
                "sugar": diet_sugar,
                "dairy": diet_dairy,
                "sleep": sleep_hours,
                "stress": stress_level,
                "product": product_used,
                "sunlight": sunlight_hours,
                "menstrual": menstrual_cycle,
                "travel": travel_location
            }
            try:
                response = requests.post(f"{API_URL}/lifestyle/", json=lifestyle_data)
                response.raise_for_status()
                st.success("Lifestyle data logged!")
            except requests.RequestException as e:
                st.error(f"Failed to log data: {e}")

# Dashboard Page
elif page == "Dashboard":
    st.header("Skin Health Dashboard")
    try:
        response = requests.get(f"{API_URL}/lifestyle/")
        response.raise_for_status()
        lifestyle_data = response.json()
        if lifestyle_data:
            df = pd.DataFrame(lifestyle_data)
            df["date"] = pd.to_datetime(df["date"])
            
            # Severity over time
            fig1 = px.line(df, x="date", y="severity", title="Skin Severity Over Time")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Dairy vs Severity
            fig2 = px.scatter(df, x="dairy", y="severity", title="Dairy Intake vs. Severity", trendline="ols")
            st.plotly_chart(fig2, use_container_width=True)
            
            # Sleep vs Severity
            fig3 = px.scatter(df, x="sleep", y="severity", title="Sleep Hours vs. Severity", trendline="ols")
            st.plotly_chart(fig3, use_container_width=True)
            
            # Insights
            st.subheader("Insights")
            if df["dairy"].corr(df["severity"]) > 0.5:
                st.write("High dairy intake may be associated with increased skin severity.")
            if df["sleep"].corr(df["severity"]) < -0.5:
                st.write("More sleep may be associated with reduced skin severity.")
        else:
            st.write("No data available. Please log lifestyle data or upload photos.")
    except requests.RequestException as e:
        st.error(f"Failed to fetch data: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Built for Global MIT AI Hackathon, May 2-3, 2025")