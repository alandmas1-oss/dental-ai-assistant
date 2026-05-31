import streamlit as st
import requests
from PIL import Image, ImageDraw
import io
from streamlit_image_comparison import image_comparison
from fpdf import FPDF
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv() # This loads the hidden keys from your .env file

API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")

# --- 1. PROFESSIONAL PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Dental AI Assistant", layout="wide", page_icon="🦷")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b111e;
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 30px 30px;
        background-position: center;
    }
    h1, h2, h3, p, label, .stMarkdown, .stSelectbox label {
        color: #ffffff !important;
    }
    .st-emotion-cache-16ids4e { 
        background-color: rgba(16, 26, 46, 0.8) !important;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .stButton>button {
        background-color: #1c83e1 !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. FUNCTION TO GENERATE PROFESSIONAL PDF ---
def create_pdf_report(patient_id, notes, caries, fillings, implants, findings_list):
    pdf = FPDF()
    pdf.add_page()
    
    # Header / Clinic Banner
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(28, 131, 225) 
    pdf.cell(0, 10, "DENTAL DIAGNOSTIC AI REPORT", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(0, 5, f"Generated on: {current_date} | System: Version 1.0", ln=True, align="C")
    pdf.ln(10)
    
    # Metadata Box (Patient Info)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f" Patient Chart Metadata", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f" Patient Identifier / ID: {patient_id}", ln=True)
    pdf.cell(0, 7, f" Primary Practitioner: Attending Licensed Clinician", ln=True)
    pdf.ln(5)
    
    # AI Summary Metrics Box (FIXED: Bullets replaced with dashes)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, " AI Clinical Aggregates Summary", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f" - Active Caries / Cavities Detected: {caries}", ln=True)
    pdf.cell(0, 7, f" - Existing Dental Fillings Located: {fillings}", ln=True)
    pdf.cell(0, 7, f" - Structural Surgical Implants: {implants}", ln=True)
    pdf.ln(5)
    
    # Granular Findings
    pdf.set_fill_color(240, 244, 248)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, " Detailed Target Findings Breakdown", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    if len(findings_list) == 0:
        pdf.cell(0, 7, "  No structural anomalies detected by neural network pipeline.", ln=True)
    else:
        for i, f in enumerate(findings_list, 1):
            pdf.cell(0, 7, f"  {i}. Structure Type: {f['class'].upper()} | System Confidence: {int(f['confidence']*100)}%", ln=True)
    pdf.ln(5)
    
    # Clinician Notes
    pdf.set_fill_color(240, 244, 248)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, " Attending Practitioner Examination Notes", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    if notes.strip():
        pdf.multi_cell(0, 7, f" {notes}")
    else:
        pdf.cell(0, 7, "  No supplemental text notes entered by the clinician.", ln=True)
    pdf.ln(15)
    
    # Compliance Footer
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    disclaimer = (
        "LEGAL COMPLIANCE DISCLAIMER: This computer-generated artifact acts as an informational clinical decision "
        "support matrix tool. It does not replace independent professional medical verification. Final treatment pathways, "
        "diagnostic safety liability, and charting compliance rest purely with the signing licensed dentist."
    )
    pdf.multi_cell(0, 4, disclaimer, align="C")
    
    return pdf.output()

# --- 3. CREDENTIALS ---
API_KEY = "DkxIEeGDLHq6iHUAaulm"
MODEL_ID = "dental-x-ray-panoramic/2?" 

# --- 4. SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.header("⚙️ Clinician Controls")
    st.write("Adjust the AI settings for this diagnostic session.")
    
    confidence_threshold = st.slider(
        label="🎯 AI Confidence Filter (%)",
        min_value=30,
        max_value=95,
        value=50,
        step=5
    )
    
    st.markdown("---")
    st.header("📝 Clinical Log")
    patient_id = st.text_input("Patient ID / Chart #", value="PT-8842")
    clinical_notes = st.text_area(
        "Doctor's Examination Notes", 
        placeholder="Type diagnosis or treatment plan here..."
    )

# --- 5. MAIN APP CONTENT ---
st.title("Professional Dental AI Assistant")
st.write(f"Active Session | Patient Chart: **{patient_id}**")
st.markdown("---")

COLOR_PALETTE = {"caries": "#FF4B4B", "implant": "#26D81F", "filling": "#1C83E1"}
DEFAULT_COLOR = "#FFEF00"      

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload Dental Radiograph...", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        st.subheader("Original Radiograph")
        st.image(uploaded_file, use_container_width=True)
        run_analysis = st.button("🔍 Run Diagnostic Scan", type="primary")

if uploaded_file is not None and run_analysis:
    with st.spinner("Executing neural network analysis..."):
        try:
            original_image_clean = Image.open(uploaded_file).convert("RGB")
            ai_painted_image = Image.open(uploaded_file).convert("RGB")
            image_bytes = uploaded_file.getvalue()
            
            clean_model_id = MODEL_ID.strip().strip("/")
            url = f"https://detect.roboflow.com/{clean_model_id}"
            params = {"api_key": API_KEY.strip(), "format": "json"}
            
            response = requests.post(url, params=params, files={"file": ("image.jpg", image_bytes, "image/jpeg")})
            
            if response.status_code == 200:
                raw_predictions = response.json().get("predictions", [])
                
                predictions = [
                    p for p in raw_predictions 
                    if int(p["confidence"] * 100) >= confidence_threshold
                ]
                
                caries_count = 0
                filling_count = 0
                implant_count = 0
                
                draw_layer = ImageDraw.Draw(ai_painted_image)
                
                for item in predictions:
                    condition_name = item["class"].lower()
                    confidence = int(item["confidence"] * 100)
                    
                    if "caries" in condition_name:
                        caries_count += 1
                    elif "filling" in condition_name:
                        filling_count += 1
                    elif "implant" in condition_name:
                        implant_count += 1
                    
                    chosen_color = DEFAULT_COLOR
                    for key in COLOR_PALETTE:
                        if key in condition_name:
                            chosen_color = COLOR_PALETTE[key]
                            break
                    
                    width = item["width"]
                    height = item["height"]
                    x_center = item["x"]
                    y_center = item["y"]
                    
                    left = x_center - (width / 2)
                    top = y_center - (height / 2)
                    right = x_center + (width / 2)
                    bottom = y_center + (height / 2)
                    
                    draw_layer.rectangle([left, top, right, bottom], outline=chosen_color, width=5)
                    draw_layer.text((left, max(0, top - 20)), f"{condition_name.upper()} ({confidence}%)", fill=chosen_color)

                # Visual Splitter Interface
                with col1:
                    st.success("Analysis complete!")
                    st.subheader("Interactive Visual Comparison")
                    
                    image_comparison(
                        img1=original_image_clean,
                        img2=ai_painted_image,
                        label1="Original X-Ray",
                        label2="AI Findings Overlays",
                        starting_position=50,
                        show_labels=True,
                        make_responsive=True
                    )
                
                with col2:
                    st.subheader("📋 Executive Clinic Summary")
                    
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        alert_text = f"{caries_count} Detected" if caries_count > 0 else "0 Found"
                        st.metric(label="🔴 Cavities", value=alert_text)
                    with metric_col2:
                        st.metric(label="🔵 Fillings", value=f"{filling_count} Present")
                    with metric_col3:
                        st.metric(label="🟢 Implants", value=f"{implant_count} Fixed")
                    
                    st.markdown("---")
                    
                    st.subheader("🔍 Granular Findings Breakdown")
                    if len(predictions) == 0:
                        st.info(f"No anomalies detected at or above {confidence_threshold}% confidence.")
                    else:
                        for index, item in enumerate(predictions, 1):
                            label = item["class"].upper()
                            conf = int(item["confidence"]*100)
                            report_color = DEFAULT_COLOR
                            for key in COLOR_PALETTE:
                                if key in label.lower():
                                    report_color = COLOR_PALETTE[key]
                                    break
                            st.markdown(f"<span style='color:{report_color}'>●</span> **Finding #{index}:** {label} ({conf}%)", unsafe_allow_html=True)
                    
                    if clinical_notes:
                        st.markdown("---")
                        st.subheader("🩺 Clinician Notes Addendum")
                        st.info(clinical_notes)
                    
                    # Generate & Download PDF Button
                    st.markdown("---")
                    st.subheader("📥 Export Clinical Records")
                    st.write("Compile this session's telemetry and doctor notes into an official PDF document:")
                    
                    pdf_bytes = create_pdf_report(
                        patient_id=patient_id,
                        notes=clinical_notes,
                        caries=caries_count,
                        fillings=filling_count,
                        implants=implant_count,
                        findings_list=predictions
                    )
                    
                    st.download_button(
                        label="📄 Download Diagnostic PDF Report",
                        data=bytes(pdf_bytes),
                        file_name=f"Dental_AI_Report_{patient_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                        
                    st.markdown("---")
                    st.caption(
                        "⚠️ **LEGAL NOTICE:** This AI system is an investigational clinical decision support tool. "
                        "Final diagnostic safety liability remains solely with the licensed practitioner."
                    )
            else:
                st.error(f"Error fetching data from AI server: {response.text}")
                
        except Exception as e:
            st.error(f"Error rendering comparison dashboard: {e}")