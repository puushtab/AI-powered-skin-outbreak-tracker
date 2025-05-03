import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import base64  # Needed for decoding heatmap
import mimetypes # Needed for guessing file Content-Type
import json

# --- Configuration ---
# Streamlit page configuration
st.set_page_config(page_title="AI-Psowered Skin Outbreak Tracker", layout="wide")

# Backend API URL - Update this to match your backend URL
API_URL = "http://localhost:8000"  # Base URL only

# Mock user ID (replace with actual authentication in a real application)
USER_ID = "test_user_1"

# --- Helper Function for Image Analysis and Display ---

def process_image_and_display_results(image_bytes, filename, api_url=API_URL):
    """
    Sends image bytes to the backend detection API, processes the response,
    and displays the results (score, metrics, heatmap, detections) in Streamlit.
    """
    st.info("⏳ Processing image... Please wait.")
    try:
        # --- Determine Content-Type ---
        content_type, _ = mimetypes.guess_type(filename)
        # Fallback logic if guess fails
        if content_type is None:
            ext = filename.split('.')[-1].lower()
            if ext in ["jpg", "jpeg"]: content_type = "image/jpeg"
            elif ext == "png": content_type = "image/png"
            elif ext == "bmp": content_type = "image/bmp"
            else: content_type = "application/octet-stream"
            print(f"Warning: Could not guess content type for '{filename}', using '{content_type}'.")

        # Check if the determined content type is allowed by the backend
        allowed_types = ["image/jpeg", "image/png", "image/bmp"]
        if content_type not in allowed_types:
            st.error(f"Unsupported file type '{content_type}' derived from '{filename}'. Please upload JPG, PNG, or BMP.")
            return

        # --- Send Request with Explicit Content-Type ---
        files = {"file": (filename, image_bytes, content_type)}
        detect_endpoint = f"{api_url}/detect"
        print(f"Sending request to {detect_endpoint} with Content-Type: {content_type}")

        response = requests.post(detect_endpoint, files=files, timeout=120)
        response.raise_for_status()
        result = response.json()

        # --- Display Results ---
        if result.get("success"):
            st.success("✅ Analysis Complete!")

            # Extract results safely using .get()
            score = result.get("severity_score")
            perc_area = result.get("percentage_area")
            avg_intensity = result.get("average_intensity")
            lesion_count = result.get("lesion_count")
            heatmap_b64 = result.get("heatmap_image_base64")
            detections = result.get("detections", [])

            # Display Score and Metrics in columns
            col_score, col_metrics = st.columns(2)
            with col_score:
                if score is not None:
                    st.metric(label="Facial Severity Score", value=f"{score:.1f} / 100")
                else:
                    st.write("**Severity Score:** N/A")

            with col_metrics:
                st.write(f"**Affected Area:** {perc_area:.2f}%" if isinstance(perc_area, (int, float)) else "N/A")
                st.write(f"**Avg Intensity:** {avg_intensity:.2f}" if isinstance(avg_intensity, (int, float)) else "N/A")
                st.write(f"**Lesion Count:** {lesion_count}" if isinstance(lesion_count, int) else "N/A")
                st.markdown("---")

            # Display Original Image and Heatmap side-by-side
            st.subheader("Visual Analysis")
            col1, col2 = st.columns(2)
            with col1:
                try:
                    original_image = Image.open(io.BytesIO(image_bytes))
                    st.image(original_image, caption="Original Photo", use_column_width=True)
                except Exception as e:
                    st.error(f"Could not display original image: {e}")

            with col2:
                if heatmap_b64:
                    try:
                        heatmap_bytes = base64.b64decode(heatmap_b64)
                        heatmap_image = Image.open(io.BytesIO(heatmap_bytes))
                        st.image(heatmap_image, caption="Severity Heatmap", use_column_width=True)
                    except Exception as e:
                        st.error(f"Could not decode or display heatmap: {e}")
                        print(f"Base64 decode error details: {e}")
                else:
                    st.info("Heatmap was not generated or provided by the backend.")

            # Display Detections Table
            st.subheader("Detected Conditions")
            if detections:
                detection_data = [(det.get('class_name', 'Unknown'), f"{det.get('confidence', 0)*100:.1f}%") for det in detections]
                df_detections = pd.DataFrame(detection_data, columns=["Condition", "Confidence"])
                st.dataframe(df_detections, use_container_width=True, hide_index=True)
            else:
                st.write("No specific conditions detected above the threshold.")

        else:
            st.error(f"❗️ Analysis failed: {result.get('message', 'Unknown error from backend')}")

    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to the backend API at {api_url}. Please ensure the backend server is running.")
    except requests.exceptions.Timeout:
        st.error("Request Timeout: The analysis took too long to respond. Please try again.")
    except requests.exceptions.RequestException as e:
        st.error(f"API Request Failed: {e}")
        try:
            st.error(f"Response status: {e.response.status_code}")
            st.error(f"Response text: {e.response.text}")
        except AttributeError:
            pass
    except Exception as e:
        st.error(f"An unexpected error occurred in Streamlit: {e}")
        traceback.print_exc()

# --- Helper Functions for API Calls ---

def get_user_profile(user_id: str) -> dict:
    """Fetch user profile from the backend"""
    try:
        response = requests.get(f"{API_URL}/profile/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch user profile: {e}")
        return None

def save_user_profile(profile_data: dict) -> bool:
    """Save user profile to the backend"""
    try:
        response = requests.post(f"{API_URL}/profile", json=profile_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to save user profile: {e}")
        return False

def save_lifestyle_data(lifestyle_data: dict) -> bool:
    """Save lifestyle data to the backend"""
    try:
        response = requests.post(f"{API_URL}/timeseries", json=lifestyle_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to save lifestyle data: {e}")
        return False

def get_skin_plan(user_id: str, model_name: str = "medllama2") -> dict:
    """Get skin plan from the backend"""
    try:
        response = requests.post(
            f"{API_URL}/skin-plan/generate",
            params={"user_id": user_id, "model_name": model_name}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to generate skin plan: {e}")
        return None

def get_timeseries_data(user_id: str) -> dict:
    """Get timeseries data from the backend"""
    try:
        response = requests.get(f"{API_URL}/timeseries/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch timeseries data: {e}")
        return None

# --- Streamlit App Layout ---

# Sidebar for navigation
st.sidebar.image("https://dytvr9ot2sszz.cloudfront.net/wp-content/uploads/2021/01/face-recognition-logo.png", width=100) # Placeholder logo
st.sidebar.title("Skin Outbreak Tracker")
page = st.sidebar.radio("Navigation", ["Photo Upload", "Lifestyle Tracking", "Dashboard", "User Profile"])

# --- Page Implementations ---

# Photo Upload Page (Default Page)
if page == "Photo Upload":
    st.header("📸 Photo Analysis")
    st.markdown("Upload a photo of your face or use your webcam to get a skin condition analysis and severity score.")

    upload_method = st.radio("Choose upload method:", ["⬆️ File Upload", "📷 Webcam Capture"], horizontal=True)

    image_bytes = None
    filename = "image.jpg" # Default filename

    if upload_method == "⬆️ File Upload":
        uploaded_file = st.file_uploader("Select a face photo (PNG/JPG/JPEG/BMP)", type=["png", "jpg", "jpeg", "bmp"], label_visibility="collapsed")
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            # Show preview immediately
            st.image(image_bytes, caption="Uploaded Photo Preview", width=300)


    elif upload_method == "📷 Webcam Capture":
        photo_buffer = st.camera_input("Center your face and take a photo")
        if photo_buffer is not None:
            image_bytes = photo_buffer.getvalue()
            filename = "webcam_capture.png" # Webcam typically saves as png or jpg
            # Show preview immediately
            st.image(image_bytes, caption="Captured Photo Preview", width=300)

    # Analyze button appears only when an image is ready
    if image_bytes is not None:
        st.markdown("---")
        if st.button("✨ Analyze Photo", type="primary"):
            process_image_and_display_results(image_bytes, filename, api_url=API_URL)
    else:
        st.info("Please upload a file or capture a photo to enable analysis.")

# Lifestyle Tracking Page
elif page == "Lifestyle Tracking":
    st.header("📝 Lifestyle Log")
    st.markdown("Track daily factors that might influence your skin health.")
    with st.form("lifestyle_form"):
        c1, c2 = st.columns(2)
        with c1:
            date = st.date_input("Date", value=datetime.now().date()) # Use .date()
        with c2:
             sleep_hours = st.number_input("😴 Sleep Hours", min_value=0.0, max_value=24.0, step=0.5, value=7.5)

        st.markdown("**Diet**")
        c3, c4 = st.columns(2)
        with c3:
             diet_sugar = st.slider("🍬 Sugar Intake (1=Low, 10=High)", 1, 10, 3)
        with c4:
            diet_dairy = st.slider("🥛 Dairy Intake (1=Low, 10=High)", 1, 10, 2)

        st.markdown("**Other Factors**")
        c5, c6 = st.columns(2)
        with c5:
             stress_level = st.slider("🧘 Stress Level (1=Low, 10=High)", 1, 10, 4)
        with c6:
            sunlight_hours = st.number_input("☀️ Sunlight Exposure (hours)", min_value=0.0, max_value=16.0, step=0.5, value=0.5)

        product_used = st.text_area("🧴 Skincare Products Used (comma-separated)", placeholder="e.g., CeraVe Cleanser, SPF 50 Sunscreen")
        menstrual_cycle = st.checkbox("🩸 Menstrual Cycle Active (if applicable)")
        travel_location = st.text_input("✈️ Travel Location (City, optional)")
        notes = st.text_area("📝 Additional Notes (optional)")

        submit = st.form_submit_button("Log Today's Data")
        if submit:
            lifestyle_data = {
                "user_id": USER_ID,
                "timestamp": date.isoformat(),
                "sleep_hours": sleep_hours,
                "diet_sugar": diet_sugar,
                "diet_dairy": diet_dairy,
                "stress": stress_level,
                "products_used": product_used,
                "sunlight_exposure": sunlight_hours,
                "menstrual_cycle_active": menstrual_cycle,
                "menstrual_cycle_day": 0,  # This should be calculated based on user input
                "latitude": 0.0,  # These should be fetched from location
                "longitude": 0.0,
                "humidity": 0.0,  # These should be fetched from weather API
                "pollution": 0.0
            }
            
            if save_lifestyle_data(lifestyle_data):
                st.success("Lifestyle data successfully logged!")
            else:
                st.error("Failed to log lifestyle data. Please try again.")

# Dashboard Page
elif page == "Dashboard":
    st.header("📊 Dashboard")
    
    # Fetch timeseries data
    timeseries_data = get_timeseries_data(USER_ID)
    if timeseries_data and timeseries_data.get("success"):
        data = timeseries_data.get("data", [])
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Severity Trend
            st.subheader("Severity Trend")
            fig_trend = px.line(df, x="timestamp", y="acne_severity_score", title="Skin Severity Over Time")
            st.plotly_chart(fig_trend, use_container_width=True)

            # Correlations
            st.subheader("Correlations")
            col_d, col_s = st.columns(2)
            with col_d:
                fig_dairy = px.scatter(df, x="diet_dairy", y="acne_severity_score", 
                                     title="Dairy Intake vs. Severity", trendline="ols")
                st.plotly_chart(fig_dairy, use_container_width=True)
            with col_s:
                fig_sleep = px.scatter(df, x="sleep_hours", y="acne_severity_score", 
                                     title="Sleep Hours vs. Severity", trendline="ols")
                st.plotly_chart(fig_sleep, use_container_width=True)
        else:
            st.warning("No data available for visualization.")
    else:
        st.error("Failed to fetch timeseries data. Please try again later.")

    # Generate Skin Plan
    st.subheader("Generate Skin Plan")
    model_name = st.selectbox("Select Model", ["medllama2", "llama2"])
    if st.button("Generate Plan"):
        plan = get_skin_plan(USER_ID, model_name)
        if plan and plan.get("success"):
            plan_data = plan.get("data", {})
            
            # Display Treatment Plan
            st.subheader("Treatment Plan")
            for treatment in plan_data.get("treatment_plan", []):
                st.write(f"**{treatment['date']}**: {treatment['treatment']}")
            
            # Display Recommendations
            st.subheader("Recommendations")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Lifestyle Advice**")
                for advice in plan_data.get("lifestyle_advice", []):
                    st.write(f"- {advice}")
                
                st.write("**Diet Recommendations**")
                for rec in plan_data.get("diet_recommendations", []):
                    st.write(f"- {rec}")
            
            with col2:
                st.write("**Sleep Recommendations**")
                for rec in plan_data.get("sleep_recommendations", []):
                    st.write(f"- {rec}")
                
                st.write("**Environmental Factors**")
                for factor in plan_data.get("environmental_factors", []):
                    st.write(f"- {factor}")
        else:
            st.error("Failed to generate skin plan. Please try again.")

# User Profile Page
elif page == "User Profile":
    st.header("👤 User Profile")
    
    # Fetch existing profile
    profile = get_user_profile(USER_ID)
    if profile and profile.get("success"):
        profile_data = profile.get("data", {})
    else:
        profile_data = {}
    
    with st.form("profile_form"):
        name = st.text_input("Full Name", value=profile_data.get("name", ""))
        dob = st.date_input("Date of Birth", 
                          value=datetime.strptime(profile_data.get("dob", "2000-01-01"), "%Y-%m-%d").date())
        c1, c2 = st.columns(2)
        with c1:
             height = st.number_input("Height (cm)", min_value=100, max_value=250, 
                                    value=profile_data.get("height", 165))
        with c2:
             weight = st.number_input("Weight (kg)", min_value=30, max_value=200, 
                                    value=profile_data.get("weight", 60))
        gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], 
                            index=["Male", "Female", "Other", "Prefer not to say"].index(profile_data.get("gender", "Prefer not to say")))
        
        submit = st.form_submit_button("Save Profile")
        if submit:
            profile_data = {
                "user_id": USER_ID,
                "name": name,
                "dob": dob.isoformat(),
                "height": height,
                "weight": weight,
                "gender": gender
            }
            
            if save_user_profile(profile_data):
                st.success("Profile saved successfully!")
            else:
                st.error("Failed to save profile. Please try again.")


# Footer in Sidebar
st.sidebar.markdown("---")
st.sidebar.info("v0.2 - Skin Analysis App")