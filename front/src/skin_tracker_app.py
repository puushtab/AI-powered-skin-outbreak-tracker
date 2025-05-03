import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import base64  # Needed for decoding heatmap
import mimetypes # Needed for guessing file Content-Type

# --- Configuration ---
# Streamlit page configuration
st.set_page_config(page_title="AI-Powered Skin Outbreak Tracker", layout="wide")

# Backend API URL - IMPORTANT: Ensure this points to your running FastAPI backend
API_URL = "http://127.0.0.1:8000" # Default for local run, change if needed

# Mock user ID (replace with actual authentication in a real application)
USER_ID = "user_1"

# --- Helper Function for Image Analysis and Display ---

def process_image_and_display_results(image_bytes, filename, api_url=API_URL):
    """
    Sends image bytes to the backend detection API, processes the response,
    and displays the results (score, metrics, heatmap, detections) in Streamlit.

    Args:
        image_bytes (bytes): The image content as bytes.
        filename (str): The original filename of the image (used for type guessing).
        api_url (str): The base URL of the backend API.
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
            else: content_type = "application/octet-stream" # Default fallback
            print(f"Warning: Could not guess content type for '{filename}', using '{content_type}'.") # Log fallback

        # Check if the determined content type is allowed by the backend
        allowed_types = ["image/jpeg", "image/png", "image/bmp"]
        if content_type not in allowed_types:
            st.error(f"Unsupported file type '{content_type}' derived from '{filename}'. Please upload JPG, PNG, or BMP.")
            return # Stop processing

        # --- Send Request with Explicit Content-Type ---
        files = {"file": (filename, image_bytes, content_type)} # Tuple: (filename, file_bytes, content_type)
        detect_endpoint = f"{api_url}/detect/"
        print(f"Sending request to {detect_endpoint} with Content-Type: {content_type}") # Debugging info

        response = requests.post(detect_endpoint, files=files, timeout=120) # Added timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        result = response.json() # Parse JSON response

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
                 st.markdown("---") # Separator

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
                        # Decode Base64 string to bytes
                        heatmap_bytes = base64.b64decode(heatmap_b64)
                        # Open bytes as image
                        heatmap_image = Image.open(io.BytesIO(heatmap_bytes))
                        st.image(heatmap_image, caption="Severity Heatmap", use_column_width=True)
                    except Exception as e:
                        st.error(f"Could not decode or display heatmap: {e}")
                        print(f"Base64 decode error details: {e}") # Log detailed error
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
        try: # Attempt to show more detailed error from response
             st.error(f"Response status: {e.response.status_code}")
             st.error(f"Response text: {e.response.text}")
        except AttributeError:
            pass # No response object available
    except Exception as e:
        st.error(f"An unexpected error occurred in Streamlit: {e}")
        traceback.print_exc() # Print stack trace to Streamlit console for debugging


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
            # Placeholder for lifestyle saving
            st.success("Lifestyle data submitted (Backend endpoint needed for saving).")
            lifestyle_data = {
                "user_id": USER_ID,
                "date": date.isoformat(),
                "sugar": diet_sugar,
                "dairy": diet_dairy,
                "sleep": sleep_hours,
                "stress": stress_level,
                "product": product_used,
                "sunlight": sunlight_hours,
                "menstrual": menstrual_cycle,
                "travel": travel_location,
                "notes": notes
            }
            print("Lifestyle Data to Send:", lifestyle_data) # For debugging
            # try:
            #     response = requests.post(f"{API_URL}/lifestyle/", json=lifestyle_data)
            #     response.raise_for_status()
            #     st.success("Lifestyle data successfully logged!")
            # except requests.RequestException as e:
            #     st.error(f"Failed to log data: {e}")

# Dashboard Page
elif page == "Dashboard":
    st.header("📊 Dashboard")
    st.warning("Dashboard functionality requires backend implementation to fetch and correlate lifestyle data with analysis results.")
    st.markdown("This page will display charts showing trends and potential correlations between lifestyle factors and skin severity scores over time.")

    # --- Placeholder for future dashboard ---
    st.subheader("Severity Trend (Placeholder)")
    # Example data structure you might fetch from backend
    example_data = {
        'date': pd.to_datetime(['2024-05-01', '2024-05-02', '2024-05-03', '2024-05-04']),
        'severity': [35.2, 40.1, 38.5, 45.8],
        'dairy': [2, 5, 3, 6],
        'sleep': [7.5, 6.0, 8.0, 5.5]
    }
    df_placeholder = pd.DataFrame(example_data)
    fig_trend = px.line(df_placeholder, x="date", y="severity", title="Skin Severity Over Time (Example)")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("Correlations (Placeholder)")
    col_d, col_s = st.columns(2)
    with col_d:
        fig_dairy = px.scatter(df_placeholder, x="dairy", y="severity", title="Dairy Intake vs. Severity (Example)", trendline="ols")
        st.plotly_chart(fig_dairy, use_container_width=True)
    with col_s:
        fig_sleep = px.scatter(df_placeholder, x="sleep", y="severity", title="Sleep Hours vs. Severity (Example)", trendline="ols")
        st.plotly_chart(fig_sleep, use_container_width=True)
    # --- End Placeholder ---

    # Add more complex correlation logic and insights once backend provides data

# User Profile Page
elif page == "User Profile":
    st.header("👤 User Profile")
    st.warning("User profile saving and loading requires backend implementation.")
    with st.form("profile_form"):
        st.text_input("Full Name", placeholder="Jane Doe")
        st.date_input("Date of Birth", min_value=datetime(1920, 1, 1), value=datetime(2000,1,1))
        c1, c2 = st.columns(2)
        with c1:
             st.number_input("Height (cm)", min_value=100, max_value=250, value=165)
        with c2:
             st.number_input("Weight (kg)", min_value=30, max_value=200, value=60)
        st.selectbox("Gender (Optional)", ["Prefer not to say", "Female", "Male", "Other"])
        st.text_area("Known Allergies or Skin Sensitivities")
        submit = st.form_submit_button("Save Profile")
        if submit:
            st.success("Profile submitted (Backend endpoint needed for saving).")
            # profile_data = { ... }
            # try: requests.post(...) ...


# Footer in Sidebar
st.sidebar.markdown("---")
st.sidebar.info("v0.2 - Skin Analysis App")