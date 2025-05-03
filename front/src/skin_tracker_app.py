import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import base64
import mimetypes
import json
import time

# --- Configuration ---
st.set_page_config(page_title="AI-Powered Skin Outbreak Tracker", layout="wide")

API_URL = "http://localhost:8000/api/v1"
USER_ID = "test_user_1"

if 'pending_lifestyle_data' not in st.session_state:
    st.session_state.pending_lifestyle_data = None

# --- Mascot image paths ---
mascot_images = {
    "photo_upload": "media/1-Photoroom.png",        # Mascot 1 (applying cream)
    "lifestyle_tracking": "media/2-Photoroom.png",  # Mascot 2 (smiling with cup)
    "dashboard": "media/3-Photoroom.png",           # Mascot 3 (holding bottle)
    "user_profile": "media/4-Photoroom.png",        # Mascot 4 (checklist -> "Profile Details")
    "encouragement": "media/5-Photoroom.png",       # Mascot 5 (Safocare® -> "Take Care!")
    "success": "media/6-Photoroom.png"              # Mascot 6 (checklist -> "Well Done!")
}

# --- Helper Functions ---

def process_image_and_display_results(image_bytes, filename, api_url=API_URL):
    st.info("⏳ Processing image... Please wait.")
    try:
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            ext = filename.split('.')[-1].lower()
            if ext in ["jpg", "jpeg"]: content_type = "image/jpeg"
            elif ext == "png": content_type = "image/png"
            elif ext == "bmp": content_type = "image/bmp"
            else: content_type = "application/octet-stream"
        allowed_types = ["image/jpeg", "image/png", "image/bmp"]
        if content_type not in allowed_types:
            st.error(f"Unsupported file type '{content_type}'. Please upload JPG, PNG, or BMP.")
            return
        files = {"file": (filename, image_bytes, content_type)}
        detect_endpoint = f"{api_url}/detect/"
        response = requests.post(detect_endpoint, files=files, timeout=120)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            col_success, col_img = st.columns([5, 1])
            with col_success:
                st.success("✅ Great job! Your skin analysis is complete!")
            with col_img:
                st.image(mascot_images["success"], width=50)
            score = result.get("severity_score")
            perc_area = result.get("percentage_area")
            avg_intensity = result.get("average_intensity")
            lesion_count = result.get("lesion_count")
            heatmap_b64 = result.get("heatmap_image_base64")
            detections = result.get("detections", [])
            if st.session_state.pending_lifestyle_data is not None:
                pending_data = st.session_state.pending_lifestyle_data
                pending_data["acne_severity_score"] = score
                if save_lifestyle_data(pending_data):
                    col_success, col_img = st.columns([5, 1])
                    with col_success:
                        st.success("✅ Lifestyle data saved with severity score!")
                    with col_img:
                        st.image(mascot_images["success"], width=50)
                    st.session_state.pending_lifestyle_data = None
                else:
                    st.error("Failed to save lifestyle data with severity score.")
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
            st.subheader("Visual Analysis")
            col1, col2 = st.columns(2)
            with col1:
                original_image = Image.open(io.BytesIO(image_bytes))
                st.image(original_image, caption="Original Photo", use_container_width=True)
            with col2:
                if heatmap_b64:
                    heatmap_bytes = base64.b64decode(heatmap_b64)
                    heatmap_image = Image.open(io.BytesIO(heatmap_bytes))
                    st.image(heatmap_image, caption="Severity Heatmap", use_container_width=True)
                else:
                    st.info("Heatmap not generated.")
            st.subheader("Detected Conditions")
            if detections:
                detection_data = [(det.get('class_name', 'Unknown'), f"{det.get('confidence', 0)*100:.1f}%") for det in detections]
                df_detections = pd.DataFrame(detection_data, columns=["Condition", "Confidence"])
                st.dataframe(df_detections, use_container_width=True, hide_index=True)
            else:
                st.write("No specific conditions detected.")
        else:
            st.error(f"❗️ Analysis failed: {result.get('message', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        st.error(f"API Request Failed: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

def get_user_profile(user_id: str) -> dict:
    try:
        response = requests.get(f"{API_URL}/profile/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch user profile: {e}")
        response = requests.post(f"{API_URL}/lifestyle", json=lifestyle_data)

def save_user_profile(profile_data: dict) -> bool:
    try:
        response = requests.post(f"{API_URL}/profile", json=profile_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to save user profile: {e}")
        return False

def save_lifestyle_data(lifestyle_data: dict) -> bool:
    try:
        response = requests.post(f"{API_URL}/timeseries", json=lifestyle_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to save lifestyle data: {e}")
        return False

def get_skin_plan(user_id: str, model_name: str = "medllama2") -> dict:
    try:
        response = requests.post(f"{API_URL}/skin-plan/generate", params={"user_id": user_id, "model_name": model_name})
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
        data = response.json()
        if data and data.get("success"):
            return data
        return {"success": False, "data": []}
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch timeseries data: {e}")
        return {"success": False, "data": []}

def get_summary(user_id: str) -> dict:
    try:
        response = requests.get(f"{API_URL}/timeseries/summary/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch summary: {e}")
        return None

def get_color_for_correlation(correlation: float) -> str:
    if correlation > 0:
        intensity = min(255, int(255 * correlation))
        return f"rgb(255, {255 - intensity}, {255 - intensity})"
    elif correlation < 0:
        intensity = min(255, int(255 * abs(correlation)))
        return f"rgb({255 - intensity}, 255, {255 - intensity})"
    else:
        return "rgb(255, 255, 0)"

# --- Streamlit App Layout ---

st.sidebar.image("https://dytvr9ot2sszz.cloudfront.net/wp-content/uploads/2021/01/face-recognition-logo.png", width=100)
st.sidebar.title("Skin Outbreak Tracker")
page = st.sidebar.radio("Navigation", ["Photo Upload", "Lifestyle Tracking", "Dashboard", "User Profile"])

# --- Page Implementations ---

if page == "Photo Upload":
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(mascot_images["photo_upload"], width=100)
    with col2:
        st.header("📸 Photo Analysis")
        st.markdown("Let's check how your skin is doing today!")
    st.markdown("Upload a photo of your face or use your webcam to get a skin condition analysis and severity score.")
    upload_method = st.radio("Choose upload method:", ["⬆️ File Upload", "📷 Webcam Capture"], horizontal=True)
    image_bytes = None
    filename = "image.jpg"
    if upload_method == "⬆️ File Upload":
        uploaded_file = st.file_uploader("Select a face photo (PNG/JPG/JPEG/BMP)", type=["png", "jpg", "jpeg", "bmp"], label_visibility="collapsed")
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            st.image(image_bytes, caption="Uploaded Photo Preview", width=300)
    elif upload_method == "📷 Webcam Capture":
        photo_buffer = st.camera_input("Center your face and take a photo")
        if photo_buffer is not None:
            image_bytes = photo_buffer.getvalue()
            filename = "webcam_capture.png"
            st.image(image_bytes, caption="Captured Photo Preview", width=300)
    if image_bytes is not None:
        st.markdown("---")
        if st.button("✨ Analyze Photo", type="primary"):
            process_image_and_display_results(image_bytes, filename, api_url=API_URL)
    else:
        col_info, col_img = st.columns([5, 1])
        with col_info:
            st.info("Please upload a file or capture a photo to enable analysis.")
        with col_img:
            st.image(mascot_images["encouragement"], width=50)

elif page == "Lifestyle Tracking":
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(mascot_images["lifestyle_tracking"], width=100)
    with col2:
        st.header("📝 Lifestyle Log")
        st.markdown("Tell me about your day! Your habits can affect your skin.")
    if st.session_state.pending_lifestyle_data is not None:
        st.warning("⚠️ You have unsaved lifestyle data. Please analyze a photo to save it with a severity score.")
    with st.form("lifestyle_form"):
        c1, c2 = st.columns(2)
        with c1:
            date = st.date_input("Date", value=datetime.now().date())
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
                "menstrual_cycle_day": 0,
                "latitude": 0.0,
                "longitude": 0.0,
                "humidity": 0.0,
                "pollution": 0.0
            }
            st.session_state.pending_lifestyle_data = lifestyle_data
            col_success, col_img = st.columns([5, 1])
            with col_success:
                st.success("Thanks for logging your day! This helps us understand your skin better.")
            with col_img:
                st.image(mascot_images["success"], width=50)

elif page == "Dashboard":
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(mascot_images["dashboard"], width=100)
    with col2:
        st.header("📊 Dashboard")
        st.markdown("Here's what we've learned about your skin!")
    
    # Fetch timeseries data
    timeseries_data = get_timeseries_data(USER_ID)
    if timeseries_data and timeseries_data.get("success"):
        data = timeseries_data.get("data", [])
        if data:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Convert timestamp to datetime, handling ISO format
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
            except ValueError:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
                except ValueError:
                    st.error("Error parsing timestamps. Please check the data format.")
                    st.stop()
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Create and display the trend graph
            st.subheader("Severity Trend")
            fig_trend = px.line(df, x="timestamp", y="acne_severity_score", 
                              title="Skin Severity Over Time",
                              labels={"acne_severity_score": "Severity Score", "timestamp": "Date"})
            fig_trend.update_layout(
                yaxis_range=[0, 100],  # Set y-axis range from 0 to 100
                yaxis_title="Severity Score (0-100)",
                xaxis_title="Date"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            col_warning, col_img = st.columns([5, 1])
            with col_warning:
                st.warning("No data available yet. Start by uploading a photo and logging your lifestyle!")
            with col_img:
                st.image(mascot_images["encouragement"], width=50)
    else:
        st.error("Failed to fetch timeseries data. Please try again later.")

    st.subheader("📈 Weekly Analysis")
    summary_data = get_summary(USER_ID)
    if summary_data and summary_data.get("success"):
        st.markdown(f"**{summary_data.get('summary', 'No summary available')}**")
        correlations = summary_data.get('correlations', {})
        if correlations:
            st.markdown("**Correlation Scores:**")
            for factor, score in correlations.items():
                if not pd.isna(score):
                    factor_name = factor.replace('_', ' ').title()
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.write(factor_name)
                    with col2:
                        normalized_score = (score + 1) / 2
                        color = get_color_for_correlation(score)
                        st.markdown(f"""
                            <style>
                                div[data-testid="stProgress"] > div > div > div {{
                                    background-color: {color};
                                    border-radius: 10px;
                                }}
                                div[data-testid="stProgress"] > div > div {{
                                    background-color: #f0f0f0;
                                    border-radius: 10px;
                                }}
                            </style>
                            """, unsafe_allow_html=True)
                        st.progress(normalized_score)
                        # Fixed correlation interpretation: positive = regression, negative = progression
                        direction = "↑ Regression" if score > 0 else "↓ Progression" if score < 0 else "→ Neutral"
                        direction_color = "#e74c3c" if score > 0 else "#2ecc71" if score < 0 else "#f1c40f"
                        st.markdown(f'<div style="text-align: center; color: {direction_color}; font-weight: bold;">{direction}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div style="text-align: center;">{score:.2f}</div>', unsafe_allow_html=True)
                    with col3:
                        st.write("")
    else:
        col_warning, col_img = st.columns([5, 1])
        with col_warning:
            st.warning("No summary available. Please log more data to generate insights.")
        with col_img:
            st.image(mascot_images["encouragement"], width=50)
    st.subheader("Generate Skin Plan")
    model_name = st.selectbox("Select Model", ["medllama2:7b-q3_K_M", "llama2"])
    if st.button("Generate Plan"):
        plan = get_skin_plan(USER_ID, model_name)
        if plan and plan.get("success"):
            plan_data = plan.get("data", {})
            st.subheader("Treatment Plan")
            for treatment in plan_data.get("treatment_plan", []):
                st.write(f"**{treatment['date']}**: {treatment['treatment']}")
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
            
            # Display Recommended Products
            st.subheader("Recommended Products for your profile")
            recommended_products = plan_data.get("recommended_products", [])
            if recommended_products:
                # Create 4 columns for the products
                cols = st.columns(4)
                for idx, product in enumerate(recommended_products):
                    with cols[idx % 4]:
                        # Create a container for each product
                        with st.container():
                            # Display product thumbnail
                            if product.get("thumbnail"):
                                st.image(product["thumbnail"], width=150)
                            else:
                                st.image("https://via.placeholder.com/150?text=No+Image", width=150)
                            
                            # Display product name
                            st.markdown(f"**{product['title']}**")
                            
                            # Display price
                            st.write(f"**Price:** {product['price']}")
                            
                            # Display source
                            st.write(f"*{product['source']}*")
                            
                            # Add clickable button for the product link
                            if product.get("link"):
                                st.markdown(
                                    f'<a href="{product["link"]}" target="_blank" style="text-decoration: none;">'
                                    f'<button style="background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">'
                                    f'View Product</button></a>',
                                    unsafe_allow_html=True
                                )
            else:
                st.info("No product recommendations available at this time.")
        else:
            st.error("Failed to generate skin plan. Please try again.")

elif page == "User Profile":
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(mascot_images["user_profile"], width=100)
    with col2:
        st.header("👤 User Profile")
        st.markdown("Let's make sure your profile is up to date!")
    profile = get_user_profile(USER_ID)
    if profile and profile.get("success"):
        profile_data = profile.get("data", {})
    else:
        profile_data = {}
    with st.form("profile_form"):
        name = st.text_input("Full Name", value=profile_data.get("name", ""))
        dob = st.date_input("Date of Birth", value=datetime.strptime(profile_data.get("dob", "2000-01-01"), "%Y-%m-%d").date())
        c1, c2 = st.columns(2)
        with c1:
            height = st.number_input("Height (cm)", min_value=100, max_value=250, value=profile_data.get("height", 165))
        with c2:
            weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=profile_data.get("weight", 60))
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
                col_success, col_img = st.columns([5, 1])
                with col_success:
                    st.success("You're all set! Your profile is up to date!")
                with col_img:
                    st.image(mascot_images["success"], width=50)
            else:
                st.error("Failed to save profile. Please try again.")

st.sidebar.markdown("---")
st.sidebar.info("v0.2 - Skin Analysis App")