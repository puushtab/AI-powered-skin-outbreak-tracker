import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import base64

# Streamlit page configuration
st.set_page_config(page_title="AI-Powered Skin Outbreak Tracker", layout="wide")

# Backend API URL
API_URL = "http://localhost:8000"

# Mock user ID (replace with auth in production)
USER_ID = "user_1"

# Function to fetch and display diagnosis and LLM suggestion for a given plot type
def display_diagnosis_and_suggestion(plot_type):
    st.subheader(f"Diagnosis for {plot_type.replace('_', ' ')}")
    try:
        response = requests.get(f"{API_URL}/diagnosis/{plot_type}/{USER_ID}")
        if response.status_code == 200:
            diagnosis = response.json().get("diagnosis", "No diagnosis available.")
            st.write(diagnosis)
        else:
            st.write("Unable to fetch diagnosis.")
    except requests.RequestException as e:
        st.error(f"Failed to fetch diagnosis: {e}")
    
    st.subheader(f"LLM Suggestion for {plot_type.replace('_', ' ')}")
    try:
        response = requests.get(f"{API_URL}/suggestion/{plot_type}/{USER_ID}")
        if response.status_code == 200:
            suggestion = response.json().get("suggestion", "No suggestion available.")
            st.write(suggestion)
        else:
            st.write("Unable to fetch suggestion.")
    except requests.RequestException as e:
        st.error(f"Failed to fetch suggestion: {e}")

# Sidebar for navigation
st.sidebar.title("Skin Outbreak Tracker")
page = st.sidebar.radio("Navigate", ["Profile", "Photo Upload", "Lifestyle Tracking", "Dashboard"])

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
                response = requests.post(f"{API_URL}/detect/", files={"file": (uploaded_file.name, img_byte_arr)})
                response.raise_for_status()
                result = response.json()
                st.write(f"Severity Score: {result['severity_score']}/100")
                if result.get('percentage_area') is not None:
                    st.write(f"Percentage Area Affected: {result['percentage_area']}%")
                if result.get('average_intensity') is not None:
                    st.write(f"Average Intensity: {result['average_intensity']}")
                if result.get('lesion_count') is not None:
                    st.write(f"Lesion Count: {result['lesion_count']}")
                if result.get('heatmap_image_base64'):
                    heatmap_bytes = base64.b64decode(result['heatmap_image_base64'])
                    heatmap_image = Image.open(io.BytesIO(heatmap_bytes))
                    st.image(heatmap_image, caption="Heatmap Overlay", use_column_width=True)
                else:
                    st.write("No heatmap available.")
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
                response = requests.post(f"{API_URL}/detect/", files={"file": ("photo.png", img_byte_arr)})
                response.raise_for_status()
                result = response.json()
                st.write(f"Severity Score: {result['severity_score']}/100")
                if result.get('percentage_area') is not None:
                    st.write(f"Percentage Area Affected: {result['percentage_area']}%")
                if result.get('average_intensity') is not None:
                    st.write(f"Average Intensity: {result['average_intensity']}")
                if result.get('lesion_count') is not None:
                    st.write(f"Lesion Count: {result['lesion_count']}")
                if result.get('heatmap_image_base64'):
                    heatmap_bytes = base64.b64decode(result['heatmap_image_base64'])
                    heatmap_image = Image.open(io.BytesIO(heatmap_bytes))
                    st.image(heatmap_image, caption="Heatmap Overlay", use_column_width=True)
                else:
                    st.write("No heatmap available.")
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

    # Fetches recent lifestyle entries to show a summary of the last 5 logs
    try:
        response = requests.get(f"{API_URL}/lifestyle/recent/{USER_ID}?limit=5")
        if response.status_code == 200:
            recent_logs = response.json()
            st.subheader("Recent Lifestyle Logs")
            if recent_logs:
                recent_df = pd.DataFrame(recent_logs)
                recent_df["date"] = pd.to_datetime(recent_df["date"])
                st.dataframe(recent_df[["date", "sugar", "dairy", "sleep", "stress"]].sort_values(by="date", ascending=False))
            else:
                st.write("No recent lifestyle logs found.")
        else:
            st.write("Unable to fetch recent logs.")
    except requests.RequestException as e:
        st.error(f"Failed to fetch recent logs: {e}")

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
            display_diagnosis_and_suggestion("severity_over_time")
            
            # Dairy vs Severity
            fig2 = px.scatter(df, x="dairy", y="severity", title="Dairy Intake vs. Severity", trendline="ols")
            st.plotly_chart(fig2, use_container_width=True)
            display_diagnosis_and_suggestion("dairy_vs_severity")
            
            # Sleep vs Severity
            fig3 = px.scatter(df, x="sleep", y="severity", title="Sleep Hours vs. Severity", trendline="ols")
            st.plotly_chart(fig3, use_container_width=True)
            display_diagnosis_and_suggestion("sleep_vs_severity")
            
            # Insights
            st.subheader("Insights")
            if df["dairy"].corr(df["severity"]) > 0.5:
                st.write("High dairy intake may be associated with increased skin severity.")
            if df["sleep"].corr(df["severity"]) < -0.5:
                st.write("More sleep may be associated with reduced skin severity.")

            # Fetches aggregated insights from a new endpoint
            try:
                response = requests.get(f"{API_URL}/lifestyle/insights/{USER_ID}")
                if response.status_code == 200:
                    insights = response.json()
                    st.subheader("Aggregated Insights")
                    if insights:
                        st.write(f"Average severity with high dairy (>7): {insights.get('avg_severity_high_dairy', 'N/A')}")
                        st.write(f"Average severity with low sleep (<6 hours): {insights.get('avg_severity_low_sleep', 'N/A')}")
                    else:
                        st.write("No aggregated insights available.")
                else:
                    st.write("Unable to fetch insights.")
            except requests.RequestException as e:
                st.error(f"Failed to fetch insights: {e}")
        else:
            st.write("No data available. Please log lifestyle data or upload photos.")
    except requests.RequestException as e:
        st.error(f"Failed to fetch data: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Built for Global MIT AI Hackathon, May 2-3, 2025")