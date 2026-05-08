import streamlit as st
import os
import tempfile
from PIL import Image, ImageDraw
from ImageQuality import app, InspectorState
import base64

# Page Configuration
st.set_page_config(
    page_title="Forensic Evidence Mapper",
    page_icon="📍",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

def draw_boxes(image, detections):
    """Draws bounding boxes on the image based on normalized coordinates."""
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    for det in detections:
        # box_2d is [ymin, xmin, ymax, xmax] in normalized (0-1000)
        ymin, xmin, ymax, xmax = det['box_2d']
        
        # Scale to pixel values
        left = xmin * width / 1000
        top = ymin * height / 1000
        right = xmax * width / 1000
        bottom = ymax * height / 1000
        
        # Draw the rectangle
        draw.rectangle([left, top, right, bottom], outline="red", width=5)
        draw.text((left, top - 20), det['label'], fill="red")
    
    return image

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/marker.png", width=80)
    st.title("Forensic Settings")
    max_iters = st.slider("Max Iterations", 1, 5, 3)
    st.info("Using Gemini 2.5 Flash for Spatial Forensic Mapping.")

# Header
st.title("📍 Forensic Evidence Mapping System")
st.subheader("Spatial Detection & Quality Validation")

# Layout Columns
col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown("### 📤 Upload Evidence")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image", use_container_width=True)
        
        # Save to temp file for the backend
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            image.convert("RGB").save(tmp_file.name)
            temp_path = tmp_file.name

with col2:
    st.markdown("### ⚡ Analysis Dashboard")
    
    if uploaded_file is not None:
        if st.button("🚀 Run Spatial Analysis", type="primary", use_container_width=True):
            
            # Reset history and state
            state = {
                "image_path": temp_path,
                "iterations": 0,
                "decision": "",
                "analysis": "",
                "quality_score": 0,
                "detections": [],
                "history": []
            }
            
            status_container = st.status("Performing Spatial Mapping...", expanded=True)
            
            with status_container:
                st.write("🏃 Identifying forensic marks...")
                final_result = app.invoke(state)
                st.write("✅ Analysis complete.")
                status_container.update(label="Analysis Finished!", state="complete", expanded=False)
            
            # --- Results Display ---
            st.divider()
            
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                st.metric("Final Quality", f"{final_result['quality_score']}/10")
            
            with res_col2:
                color = "green" if final_result['decision'] == "Approve" else "red"
                st.markdown(f"**Decision:** <span style='color:{color}; font-size: 24px; font-weight: bold;'>{final_result['decision']}</span>", unsafe_allow_html=True)
            
            with res_col3:
                st.metric("Evidence Points", len(final_result.get('detections', [])))
            
            # --- Spatial Visualization ---
            if final_result.get('detections'):
                st.markdown("### 📍 Forensic Evidence Map")
                # Reload image to draw on it
                img_to_draw = Image.open(uploaded_file).convert("RGB")
                marked_image = draw_boxes(img_to_draw, final_result['detections'])
                st.image(marked_image, caption="AI-Generated Evidence Map", use_container_width=True)
                
                # Detections Table
                st.markdown("#### Detected Elements")
                st.table(final_result['detections'])

            st.markdown("#### 📝 Full AI Analysis")
            st.info(final_result['analysis'])
            
            # --- Iteration History ---
            st.markdown("### 📜 Iteration History")
            for record in final_result.get("history", []):
                with st.expander(f"Attempt {record['iteration']} - Score: {record['score']}/10 ({record['decision']})"):
                    st.write(f"**Reasoning:** {record['reasoning']}")
                    if record.get('detections'):
                         st.write(f"**Detections:** {len(record['detections'])}")
                    st.text_area("Analysis Details", record['analysis'], height=150, key=f"hist_{record['iteration']}")
                    
    else:
        st.info("Please upload an image to begin.")

# Footer
st.divider()
st.caption("Powered by LangGraph & Gemini Spatial Prompting")
