import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import io
import base64
import json
import time
import sys
import os

st.set_page_config(
    page_title="SkinMeta AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

    :root {
        --cream: #FAF8F5;
        --warm-white: #FFFDF9;
        --blush: #F2E8E4;
        --sage: #C8D8C4;
        --sage-dark: #8FAE89;
        --terracotta: #C4785A;
        --deep: #2A1F1A;
        --muted: #7A6E6A;
        --card-bg: #FFFFFF;
        --border: rgba(42, 31, 26, 0.08);
        --shadow-sm: 0 2px 12px rgba(42,31,26,0.06);
        --shadow-md: 0 8px 32px rgba(42,31,26,0.1);
        --shadow-lg: 0 20px 60px rgba(42,31,26,0.15);
        --radius: 16px;
        --radius-sm: 8px;
    }

    .stApp {
        background: var(--cream);
        font-family: 'DM Sans', sans-serif;
    }

    /* Hide Streamlit default elements */
    #MainMenu, footer, header { display: none !important; }
    .stDeployButton { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }

    /* ── Typography ── */
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: clamp(2.8rem, 6vw, 5rem);
        font-weight: 600;
        color: var(--deep);
        line-height: 1.15;
        letter-spacing: -0.02em;
    }
    .hero-title span { color: var(--terracotta); font-style: italic; }

    .section-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.9rem;
        font-weight: 600;
        color: var(--deep);
        margin-bottom: 0.4rem;
    }
    .section-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: var(--muted);
        font-weight: 300;
        margin-bottom: 2rem;
        line-height: 1.6;
    }

    /* ── Navigation ── */
    .nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.2rem 2rem;
        background: rgba(250,248,245,0.95);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .nav-logo {
        font-family: 'Playfair Display', serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--deep);
    }
    .nav-logo span { color: var(--terracotta); }

    /* ── Cards ── */
    .card {
        background: var(--card-bg);
        border-radius: var(--radius);
        padding: 2rem;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border);
        transition: box-shadow 0.3s ease, transform 0.2s ease;
    }
    .card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }

    .card-sm {
        background: var(--card-bg);
        border-radius: var(--radius-sm);
        padding: 1.2rem 1.5rem;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border);
        margin-bottom: 0.8rem;
    }

    .result-card {
        background: linear-gradient(135deg, #FFFDF9 0%, #F9F5F2 100%);
        border-radius: var(--radius);
        padding: 2rem;
        border: 1px solid rgba(196, 120, 90, 0.2);
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
    }
    .result-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--terracotta), var(--sage-dark));
        border-radius: 4px 0 0 4px;
    }

    .ingredient-tag {
        display: inline-block;
        background: var(--blush);
        color: var(--terracotta);
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 0.2rem;
        border: 1px solid rgba(196,120,90,0.2);
    }

    .severity-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .severity-mild     { background: #E8F5E9; color: #2E7D32; }
    .severity-moderate { background: #FFF3E0; color: #E65100; }
    .severity-severe   { background: #FCE4EC; color: #C62828; }
    .severity-clear    { background: #E3F2FD; color: #1565C0; }

    .product-card {
        background: var(--card-bg);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border);
        transition: all 0.3s ease;
        height: 100%;
    }
    .product-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-3px);
        border-color: rgba(196,120,90,0.3);
    }
    .product-brand {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--muted);
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .product-name {
        font-family: 'Playfair Display', serif;
        font-size: 1.05rem;
        color: var(--deep);
        font-weight: 600;
        margin-bottom: 0.6rem;
        line-height: 1.3;
    }
    .product-why {
        font-size: 0.83rem;
        color: var(--muted);
        line-height: 1.5;
        font-style: italic;
    }

    .routine-step {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1.2rem;
        background: var(--card-bg);
        border-radius: var(--radius-sm);
        border: 1px solid var(--border);
        margin-bottom: 0.7rem;
        box-shadow: var(--shadow-sm);
    }
    .step-number {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--terracotta), #D4926B);
        color: white;
        font-weight: 700;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    /* ── Upload Zone ── */
    .upload-zone {
        border: 2px dashed rgba(196,120,90,0.3);
        border-radius: var(--radius);
        padding: 3rem 2rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(242,232,228,0.3), rgba(200,216,196,0.2));
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .upload-zone:hover {
        border-color: var(--terracotta);
        background: rgba(242,232,228,0.5);
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, var(--terracotta) 0%, #D4926B 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.75rem 2.5rem !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 4px 20px rgba(196,120,90,0.35) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(196,120,90,0.4) !important;
    }

    .btn-secondary > button {
        background: transparent !important;
        color: var(--terracotta) !important;
        border: 1.5px solid var(--terracotta) !important;
        box-shadow: none !important;
    }
    .btn-secondary > button:hover {
        background: var(--blush) !important;
        box-shadow: none !important;
    }

    /* ── Progress Bars ── */
    .confidence-bar {
        height: 6px;
        border-radius: 3px;
        background: var(--blush);
        overflow: hidden;
        margin: 0.4rem 0;
    }
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--terracotta), var(--sage-dark));
        border-radius: 3px;
        transition: width 0.8s ease;
    }

    /* ── Dividers ── */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        margin: 3rem 0;
    }

    /* ── Hero Section ── */
    .hero-section {
        min-height: 85vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 4rem 2rem;
        background: linear-gradient(160deg, #FAF8F5 0%, #F5EDE7 40%, #EEF3EC 100%);
        position: relative;
        overflow: hidden;
    }

    /* ── Pills ── */
    .feature-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(196,120,90,0.08);
        border: 1px solid rgba(196,120,90,0.2);
        border-radius: 50px;
        padding: 0.35rem 0.9rem;
        font-size: 0.82rem;
        color: var(--terracotta);
        font-weight: 500;
        margin: 0.2rem;
    }

    /* ── Disclaimer ── */
    .disclaimer-box {
        background: rgba(255,243,224,0.7);
        border: 1px solid rgba(230,160,0,0.3);
        border-radius: var(--radius-sm);
        padding: 1rem 1.2rem;
        font-size: 0.83rem;
        color: #7A6000;
        line-height: 1.5;
    }

    .transparency-box {
        background: rgba(200,216,196,0.2);
        border: 1px solid rgba(143,174,137,0.3);
        border-radius: var(--radius-sm);
        padding: 1rem 1.2rem;
        font-size: 0.83rem;
        color: #3A5C37;
        line-height: 1.5;
        margin: 1rem 0;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        color: var(--muted);
        padding: 0.7rem 1.4rem;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: var(--card-bg) !important;
        color: var(--terracotta) !important;
        border: 1px solid var(--border) !important;
        border-bottom: 1px solid var(--card-bg) !important;
    }

    /* ── Selectbox / Inputs ── */
    .stSelectbox > div > div {
        background: var(--card-bg);
        border-radius: var(--radius-sm);
        border: 1px solid var(--border);
        font-family: 'DM Sans', sans-serif;
    }
    .stSlider > div { padding: 0.5rem 0; }

    /* ── Metric ── */
    [data-testid="metric-container"] {
        background: var(--card-bg);
        border-radius: var(--radius-sm);
        padding: 1rem;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }

    /* ── File Uploader ── */
    [data-testid="stFileUploader"] {
        background: transparent;
    }
    [data-testid="stFileUploader"] > div {
        background: var(--card-bg);
        border: 2px dashed rgba(196,120,90,0.3);
        border-radius: var(--radius);
    }

    /* ── Success / Warning / Info boxes ── */
    .stSuccess { border-radius: var(--radius-sm); }
    .stInfo { border-radius: var(--radius-sm); }
    .stWarning { border-radius: var(--radius-sm); }

    /* ── Page padding ── */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    .content-wrapper {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)


def render_nav():
    st.markdown("""
    <div class="nav-bar">
        <div class="nav-logo">Skin<span>Meta</span> AI</div>
        <div style="display:flex;gap:1rem;align-items:center">
            <span style="font-size:0.85rem;color:var(--muted);font-weight:500">Powered by XAI</span>
            <span class="feature-pill">&#10022; Beta</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero():
    col1, col2 = st.columns([1.1, 0.9], gap="large")
    with col1:
        st.markdown("""
        <div style="padding: 3rem 0 2rem 2rem;">
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1.5rem;">
                <span class="feature-pill">&#128302; CNN Detection</span>
                <span class="feature-pill">&#128161; Explainable AI</span>
                <span class="feature-pill">&#129380; Personalized</span>
            </div>
            <div class="hero-title">Your skin,<br><span>decoded</span><br>by AI.</div>
            <div style="font-size:1.1rem;color:var(--muted);font-weight:300;margin:1.5rem 0 2rem;line-height:1.7;max-width:480px;">
                Upload a photo, answer a few questions. SkinMeta AI analyzes your skin using deep learning and maps real skincare products to your unique needs.
            </div>
            <div style="display:flex;gap:0.5rem;align-items:center;font-size:0.82rem;color:var(--muted);">
                <span>&#10003; Acne classification</span>
                <span style="margin:0 0.5rem">&#183;</span>
                <span>&#10003; Ingredient matching</span>
                <span style="margin:0 0.5rem">&#183;</span>
                <span>&#10003; Product filtering</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="padding:2rem;display:flex;flex-direction:column;align-items:center;gap:1rem;">
            <div style="background:linear-gradient(135deg,#F9F0EB,#EEF3EC);border-radius:24px;padding:2.5rem;width:100%;box-shadow:var(--shadow-lg);border:1px solid var(--border);">
                <div style="text-align:center;margin-bottom:1.5rem;">
                    <div style="font-size:3.5rem;margin-bottom:0.5rem;">&#10024;</div>
                    <div style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--deep);font-weight:600;">Skin Analysis Ready</div>
                    <div style="font-size:0.85rem;color:var(--muted);">Upload your image below to begin</div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;">
                    <div style="background:white;border-radius:12px;padding:1rem;text-align:center;box-shadow:var(--shadow-sm);">
                        <div style="font-size:1.4rem;margin-bottom:0.3rem;">&#127919;</div>
                        <div style="font-size:0.75rem;font-weight:600;color:var(--deep);">4 Acne Types</div>
                        <div style="font-size:0.7rem;color:var(--muted);">Detected</div>
                    </div>
                    <div style="background:white;border-radius:12px;padding:1rem;text-align:center;box-shadow:var(--shadow-sm);">
                        <div style="font-size:1.4rem;margin-bottom:0.3rem;">&#127807;</div>
                        <div style="font-size:0.75rem;font-weight:600;color:var(--deep);">20+ Ingredients</div>
                        <div style="font-size:0.7rem;color:var(--muted);">Analyzed</div>
                    </div>
                    <div style="background:white;border-radius:12px;padding:1rem;text-align:center;box-shadow:var(--shadow-sm);">
                        <div style="font-size:1.4rem;margin-bottom:0.3rem;">&#128737;</div>
                        <div style="font-size:0.75rem;font-weight:600;color:var(--deep);">Smart Filter</div>
                        <div style="font-size:0.7rem;color:var(--muted);">Products only</div>
                    </div>
                    <div style="background:white;border-radius:12px;padding:1rem;text-align:center;box-shadow:var(--shadow-sm);">
                        <div style="font-size:1.4rem;margin-bottom:0.3rem;">&#128172;</div>
                        <div style="font-size:0.75rem;font-weight:600;color:var(--deep);">Explained AI</div>
                        <div style="font-size:0.7rem;color:var(--muted);">Why it works</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Analysis Section ───────────────────────────────────────────────────────────
def render_analysis_section():
    from utils.cnn_model import CNNModel
    from utils.recommend import RecommendationEngine
    from utils.product_bridge import ProductBridge
    from utils.filters import ProductFilter

    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;">
        <div class="section-title">Analyze Your Skin</div>
        <div class="section-subtitle">Upload a clear, well-lit photo of your face &middot; No filters or makeup</div>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_profile = st.columns([1, 1], gap="large")

    with col_input:
        # FIX: card open/close must both be in same render call — use st.container
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**&#128248; Upload Skin Image**")
            st.markdown(
                '<div style="font-size:0.82rem;color:var(--muted);margin-bottom:1rem;">'
                'JPG, PNG or JPEG &middot; Max 10MB &middot; Clear, well-lit selfie</div>',
                unsafe_allow_html=True
            )
            uploaded_file = st.file_uploader(
                "Upload skin image",
                type=["jpg", "jpeg", "png"],
                label_visibility="collapsed",
                key="skin_image"
            )
            if uploaded_file:
                image = Image.open(uploaded_file).convert("RGB")
                st.image(image, caption="Uploaded Image", use_container_width=True)
                st.markdown(
                    '<div class="transparency-box">&#9989; Image loaded successfully. Ready for analysis.</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

    with col_profile:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**&#128100; Skin Profile Questionnaire**")
            st.markdown(
                '<div style="font-size:0.82rem;color:var(--muted);margin-bottom:1rem;">'
                'Used for rule-based refinement only</div>',
                unsafe_allow_html=True
            )
            skin_type = st.selectbox(
                "Skin Type",
                ["Normal", "Oily", "Dry", "Combination", "Sensitive"],
                key="skin_type"
            )
            sensitivity = st.selectbox(
                "Sensitivity Level",
                ["Low", "Moderate", "High"],
                key="sensitivity"
            )
            age_group = st.selectbox(
                "Age Group",
                ["14-18", "19-24", "25-34", "35-44", "45+"],
                key="age_group"
            )
            climate = st.selectbox(
                "Climate",
                ["Temperate", "Tropical / Humid", "Dry / Arid", "Cold"],
                key="climate"
            )
            concerns = st.multiselect(
                "Skin Concerns",
                ["Acne", "Blackheads", "Dark Spots", "Oiliness", "Dryness",
                 "Redness", "Enlarged Pores", "Uneven Texture"],
                default=["Acne"],
                key="concerns"
            )
            st.markdown("""
            <div class="transparency-box">
                &#128161; <strong>Transparency Note:</strong> Ingredient recommendations are primarily generated
                using CNN acne-type prediction. Questionnaire answers apply rule-based refinement
                (e.g. sensitive skin &rarr; no harsh exfoliants). The ML model does not directly learn
                from climate or age group inputs.
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Analyze button
    st.markdown('<div style="text-align:center;margin:2rem 0;">', unsafe_allow_html=True)
    analyze_clicked = st.button("&#10024; Analyze My Skin", key="analyze_btn", use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        &#9888;&#65039; <strong>Medical Disclaimer:</strong> SkinMeta AI is an educational tool and does not
        provide medical advice. Consult a dermatologist for persistent or severe skin conditions.
        Results are based on AI predictions and may not always be accurate.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if analyze_clicked:
        if not uploaded_file:
            st.error("Please upload a skin image first.")
            return

        profile = {
            "skin_type": skin_type,
            "sensitivity": sensitivity,
            "age_group": age_group,
            "climate": climate,
            "concerns": concerns
        }

        try:
            with st.spinner("Analyzing your skin..."):
                time.sleep(0.8)
                cnn = CNNModel()
                rec_engine = RecommendationEngine()
                bridge = ProductBridge()
                pf = ProductFilter()

                image_bytes = uploaded_file.getvalue()
                cnn_result = cnn.predict(image_bytes)

                rec_result = rec_engine.recommend(
                    acne_type=cnn_result["acne_type"],
                    severity=cnn_result["severity_level"],
                    skin_profile=profile
                )

                products = bridge.get_products(
                    formula=rec_result["formula"],
                    acne_type=cnn_result["acne_type"],
                    top_n=9
                )

                filtered_products = pf.filter(products, profile)

            st.session_state["analysis_done"] = True
            st.session_state["cnn_result"] = cnn_result
            st.session_state["rec_result"] = rec_result
            st.session_state["products"] = filtered_products
            st.session_state["profile"] = profile
            st.session_state["uploaded_image"] = image

            st.rerun()

        except ValueError as ve:
            err_msg = str(ve)
            if "NOT_SKIN" in err_msg:
                friendly = err_msg.replace("NOT_SKIN: ", "")
                st.error(
                    "This doesn't look like a skin photo.\n\n"
                    + friendly
                    + "\n\nPlease upload a clear, well-lit photo of your face or affected skin area."
                )
            else:
                st.error(f"Validation failed: {err_msg}")
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")


def _get_severity_class(severity: str) -> str:
    """Return CSS class for severity badge. Handles any casing."""
    s = severity.lower().strip()
    if s in ("mild", "low"):
        return "severity-mild"
    if s in ("moderate", "medium"):
        return "severity-moderate"
    if s in ("severe", "high"):
        return "severity-severe"
    if s in ("clear", "none"):
        return "severity-clear"
    return "severity-mild"


def _severity_icon(severity: str) -> str:
    s = severity.lower().strip()
    if s in ("severe", "high"):
        return "&#128308;"   # red circle
    if s in ("moderate", "medium"):
        return "&#128993;"   # yellow circle
    if s in ("clear", "none"):
        return "&#128994;"   # green circle
    return "&#128994;"       # default green (mild)


def render_results():
    cnn_result      = st.session_state.get("cnn_result", {})
    rec_result      = st.session_state.get("rec_result", {})
    products        = st.session_state.get("products", [])
    profile         = st.session_state.get("profile", {})
    uploaded_image  = st.session_state.get("uploaded_image")

    acne_type     = cnn_result.get("acne_type", "Unknown")
    severity      = cnn_result.get("severity", "Mild")
    confidence    = cnn_result.get("confidence", 0.82)
    all_probs     = cnn_result.get("probabilities", {})

    sev_class = _get_severity_class(severity)
    sev_icon  = _severity_icon(severity)

    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;flex-wrap:wrap;">'
        f'<div class="section-title">Analysis Results</div>'
        f'<span class="severity-badge {sev_class}">{sev_icon} {severity}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("### &#128302; Skin Analysis")

    col_img, col_cnn = st.columns([0.45, 0.55], gap="large")

    with col_img:
        if uploaded_image:
            st.image(uploaded_image, caption="Your Image", use_container_width=True)

    with col_cnn:
        conf_pct = int(confidence * 100)

        # Build probability rows as a single string to avoid repeated markdown calls
        prob_rows_html = ""
        for cls, prob in sorted(all_probs.items(), key=lambda x: -x[1]):
            prob_pct = int(prob * 100)
            bar_color = "#C4785A" if cls == acne_type else "#C8D8C4"
            prob_rows_html += (
                f'<div style="margin-bottom:0.5rem;">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">'
                f'<span style="font-size:0.8rem;color:var(--deep);">{cls}</span>'
                f'<span style="font-size:0.8rem;color:var(--muted);">{prob_pct}%</span>'
                f'</div>'
                f'<div class="confidence-bar">'
                f'<div style="height:4px;width:{prob_pct}%;background:{bar_color};border-radius:3px;"></div>'
                f'</div>'
                f'</div>'
            )

        st.markdown(
            f'<div class="result-card">'
            f'<div style="margin-bottom:1.2rem;">'
            f'<div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--muted);margin-bottom:0.3rem;">Detected Condition</div>'
            f'<div style="font-family:\'Playfair Display\',serif;font-size:1.8rem;color:var(--deep);font-weight:600;">{acne_type}</div>'
            f'</div>'
            f'<div style="margin-bottom:1.2rem;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">'
            f'<span style="font-size:0.82rem;color:var(--muted);">Model Confidence</span>'
            f'<span style="font-size:0.82rem;font-weight:600;color:var(--terracotta);">{conf_pct}%</span>'
            f'</div>'
            f'<div class="confidence-bar"><div class="confidence-fill" style="width:{conf_pct}%;"></div></div>'
            f'</div>'
            f'<div style="margin-bottom:0.8rem;font-size:0.82rem;color:var(--muted);font-weight:500;">All Class Probabilities</div>'
            f'{prob_rows_html}'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Ingredients ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### &#127807; Recommended Ingredients")
    st.markdown("""
    <div class="transparency-box">
        &#129302; Ingredients are recommended based on <strong>CNN acne-type prediction</strong>
        and refined using rule-based skin profile logic.
        Questionnaire answers adjust concentration and exclude conflicting actives.
    </div>
    """, unsafe_allow_html=True)

    ingredients  = rec_result.get("ingredients_by_category", {})
    adjustments  = rec_result.get("adjustments", [])

    if ingredients:
        ing_cols = st.columns(min(len(ingredients), 3))
        for i, (category, ing_list) in enumerate(ingredients.items()):
            with ing_cols[i % len(ing_cols)]:
                tags_html = "".join(
                    [f'<span class="ingredient-tag">{ing["name"]}</span>' for ing in ing_list]
                )
                benefit_html = (
                    f'<div class="product-why" style="margin-top:0.8rem;">{ing_list[0].get("benefit","")}</div>'
                    if ing_list else ""
                )
                st.markdown(
                    f'<div class="card" style="min-height:160px;">'
                    f'<div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--muted);margin-bottom:0.7rem;">{category}</div>'
                    f'{tags_html}'
                    f'{benefit_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )

    if adjustments:
        st.markdown("**Profile Adjustments Applied:**")
        for adj in adjustments:
            st.markdown(f'<div class="card-sm">&#9881;&#65039; {adj}</div>', unsafe_allow_html=True)

    # ── Products ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### &#128717;&#65039; Recommended Products")

    explanation = rec_result.get("explanation", "")
    if explanation:
        st.markdown(
            f'<div class="transparency-box">&#129302; <strong>Why these products?</strong><br/>{explanation}</div>',
            unsafe_allow_html=True
        )

    if not products:
        st.info("No matching facial skincare products found. Try a different skin type or upload another image.")
    else:
        st.markdown(
            f'<div style="font-size:0.85rem;color:var(--muted);margin-bottom:1rem;">'
            f'Showing {len(products)} facial skincare products &middot; Filtered for acne-prone skin</div>',
            unsafe_allow_html=True
        )

        cat_groups: dict = {}
        for p in products:
            cat = p.get("category", "Treatment")
            cat_groups.setdefault(cat, []).append(p)

        for category, cat_products in cat_groups.items():
            st.markdown(f"**{category}**")
            prod_cols = st.columns(min(len(cat_products), 3))
            for j, prod in enumerate(cat_products[:3]):
                with prod_cols[j]:
                    score_pct = int(prod.get("match_score", 0.7) * 100)
                    key_ings  = prod.get("key_ingredients", [])[:3]
                    ing_tags  = "".join(
                        [f'<span class="ingredient-tag">{ing}</span>' for ing in key_ings]
                    )
                    why   = prod.get("why_recommended", "Suitable for acne-prone skin.")
                    usage = prod.get("usage", "Apply as directed.")

                    st.markdown(
                        f'<div class="product-card">'
                        f'<div class="product-brand">{prod.get("brand", "Brand")}</div>'
                        f'<div class="product-name">{prod.get("name", "Product Name")}</div>'
                        f'<div style="margin-bottom:0.8rem;">{ing_tags}</div>'
                        f'<div style="margin-bottom:0.5rem;">'
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">'
                        f'<span style="font-size:0.75rem;color:var(--muted);">Match</span>'
                        f'<span style="font-size:0.75rem;font-weight:600;color:var(--terracotta);">{score_pct}%</span>'
                        f'</div>'
                        f'<div class="confidence-bar"><div class="confidence-fill" style="width:{score_pct}%;"></div></div>'
                        f'</div>'
                        f'<div class="product-why">{why}</div>'
                        f'<div style="font-size:0.75rem;color:var(--muted);margin-top:0.6rem;padding-top:0.6rem;border-top:1px solid var(--border);">&#128161; {usage}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    # ── Routine ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### &#128197; Personalized Routine")

    routine    = rec_result.get("routine", {})
    am_routine = routine.get("am", [])
    pm_routine = routine.get("pm", [])
    notes      = routine.get("notes", [])

    tab_am, tab_pm = st.tabs(["&#9728;&#65039; Morning (AM)", "&#127769; Night (PM)"])

    def _step_products_hint(step_name: str, products_list: list) -> str:
        """Return a formatted hint string of matching products for a routine step."""
        sn = step_name.lower()
        matched = []
        for prod in products_list:
            cat = prod.get("category", "").lower()
            if (
                ("cleanser" in sn and any(x in cat for x in ["cleanser", "wash"])) or
                ("toner"    in sn and any(x in cat for x in ["toner", "essence"])) or
                ("treatment" in sn and any(x in cat for x in ["serum", "treatment"])) or
                ("moisturizer" in sn and any(x in cat for x in ["moisturizer", "cream", "lotion"])) or
                ("spf"     in sn and any(x in cat for x in ["sunscreen", "spf"])) or
                ("repair"  in sn and any(x in cat for x in ["moisturizer", "cream", "lotion"]))
            ):
                matched.append(prod)
        if not matched:
            return ""
        # FIX: build product label outside f-string to avoid nested quote issues
        labels = ", ".join(
            ["{} {}".format(p.get("brand", ""), p.get("name", "")).strip() for p in matched[:2]]
        )
        return (
            '<div style="font-size:0.75rem;color:var(--terracotta);font-weight:600;margin-top:0.5rem;">'
            '&#10024; Try: {}</div>'.format(labels)
        )

    with tab_am:
        if am_routine:
            for step in am_routine:
                actives     = ", ".join(step.get("actives", [])[:2]) or "&#8212;"
                tag_html    = f'<span class="ingredient-tag">{actives}</span>' if actives != "&#8212;" else ""
                hint_html   = _step_products_hint(step.get("name", ""), products)
                st.markdown(
                    f'<div class="routine-step">'
                    f'<div class="step-number">{step["step"]}</div>'
                    f'<div style="flex:1;">'
                    f'<div style="font-weight:600;color:var(--deep);margin-bottom:0.2rem;">{step["name"]}</div>'
                    f'<div style="font-size:0.82rem;color:var(--muted);">{step["description"]}</div>'
                    f'<div style="margin-top:0.4rem;">{tag_html}</div>'
                    f'{hint_html}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Morning routine will appear after analysis.")

    with tab_pm:
        if pm_routine:
            for step in pm_routine:
                actives   = ", ".join(step.get("actives", [])[:2]) or "&#8212;"
                tag_html  = f'<span class="ingredient-tag">{actives}</span>' if actives != "&#8212;" else ""
                hint_html = _step_products_hint(step.get("name", ""), products)
                st.markdown(
                    f'<div class="routine-step">'
                    f'<div class="step-number" style="background:linear-gradient(135deg,#5C5470,#352F44);">{step["step"]}</div>'
                    f'<div style="flex:1;">'
                    f'<div style="font-weight:600;color:var(--deep);margin-bottom:0.2rem;">{step["name"]}</div>'
                    f'<div style="font-size:0.82rem;color:var(--muted);">{step["description"]}</div>'
                    f'<div style="margin-top:0.4rem;">{tag_html}</div>'
                    f'{hint_html}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Night routine will appear after analysis.")

    if notes:
        for note in notes:
            st.markdown(
                f'<div class="disclaimer-box" style="margin-top:0.8rem;">&#128161; {note}</div>',
                unsafe_allow_html=True
            )

    # ── Reset ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    col_reset, _ = st.columns([1, 3])
    with col_reset:
        st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
        if st.button("&#8635; New Analysis", key="reset_btn"):
            for key in ["analysis_done", "cnn_result", "rec_result", "products", "profile", "uploaded_image"]:
                st.session_state.pop(key, None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <div style="background:var(--deep);color:rgba(255,255,255,0.6);padding:3rem 2rem;margin-top:4rem;">
        <div style="max-width:1200px;margin:0 auto;display:grid;grid-template-columns:repeat(3,1fr);gap:2rem;">
            <div>
                <div style="font-family:'Playfair Display',serif;font-size:1.3rem;color:white;margin-bottom:0.8rem;">SkinMeta AI</div>
                <div style="font-size:0.82rem;line-height:1.6;">AI-powered acne analysis and personalized skincare recommendations using explainable machine learning.</div>
            </div>
            <div>
                <div style="font-weight:600;color:white;margin-bottom:0.8rem;font-size:0.9rem;">Technology</div>
                <div style="font-size:0.82rem;line-height:1.8;">CNN Image Classification<br>Rule-Based Refinement<br>TF-IDF Product Bridge<br>SHAP Explainability</div>
            </div>
            <div>
                <div style="font-weight:600;color:white;margin-bottom:0.8rem;font-size:0.9rem;">Disclaimer</div>
                <div style="font-size:0.82rem;line-height:1.6;">This tool is for educational purposes only. Always consult a qualified dermatologist for medical advice.</div>
            </div>
        </div>
        <div style="max-width:1200px;margin:2rem auto 0;padding-top:1.5rem;border-top:1px solid rgba(255,255,255,0.1);font-size:0.78rem;text-align:center;">
            &copy; 2025 SkinMeta AI &middot; Built with Streamlit &amp; TensorFlow &middot; Educational Use Only
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    inject_css()
    render_nav()

    analysis_done = st.session_state.get("analysis_done", False)

    if not analysis_done:
        render_hero()
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        render_analysis_section()
    else:
        render_results()

    render_footer()


if __name__ == "__main__":
    main()