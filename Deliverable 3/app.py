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
        --blush: #F2E8E4;
        --sage-dark: #8FAE89;
        --terracotta: #C4785A;
        --deep: #2A1F1A;
        --muted: #7A6E6A;
        --border: rgba(42,31,26,0.08);
        --shadow-sm: 0 2px 12px rgba(42,31,26,0.06);
        --shadow-md: 0 8px 32px rgba(42,31,26,0.1);
        --shadow-lg: 0 20px 60px rgba(42,31,26,0.15);
        --radius: 16px;
        --radius-sm: 8px;
    }

    .stApp { background: var(--cream); font-family: 'DM Sans', sans-serif; }
    #MainMenu, footer, header { display: none !important; }
    .stDeployButton { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }

    /* ── Style Streamlit's native border container as a card ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid rgba(42,31,26,0.09) !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 12px rgba(42,31,26,0.06) !important;
    }

    /* ── Navigation ── */
    .nav-bar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 1.2rem 2rem;
        background: rgba(250,248,245,0.97);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
        position: sticky; top: 0; z-index: 100;
    }
    .nav-logo { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 600; color: var(--deep); }
    .nav-logo span { color: var(--terracotta); }
    .feature-pill {
        display: inline-flex; align-items: center; gap: 0.4rem;
        background: rgba(196,120,90,0.08); border: 1px solid rgba(196,120,90,0.2);
        border-radius: 50px; padding: 0.35rem 0.9rem;
        font-size: 0.82rem; color: var(--terracotta); font-weight: 500; margin: 0.2rem;
    }

    /* ── Typography ── */
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: clamp(2.8rem, 6vw, 5rem);
        font-weight: 600; color: var(--deep); line-height: 1.15; letter-spacing: -0.02em;
    }
    .hero-title span { color: var(--terracotta); font-style: italic; }
    .section-title  { font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 600; color: var(--deep); margin-bottom: 0.4rem; }
    .section-subtitle { font-size: 1rem; color: var(--muted); font-weight: 300; margin-bottom: 2rem; line-height: 1.6; }

    /* ── Card header (inside native container) ── */
    .card-header { font-size: 1rem; font-weight: 700; color: var(--deep); margin-bottom: 0.25rem; }
    .card-sub    { font-size: 0.82rem; color: var(--muted); margin-bottom: 1rem; }

    /* ── Info boxes ── */
    .transparency-box {
        background: rgba(200,216,196,0.25); border: 1px solid rgba(143,174,137,0.4);
        border-radius: var(--radius-sm); padding: 0.9rem 1.1rem;
        font-size: 0.82rem; color: #3A5C37; line-height: 1.5; margin-top: 1rem;
    }
    .disclaimer-box {
        background: rgba(255,243,224,0.8); border: 1px solid rgba(230,160,0,0.3);
        border-radius: var(--radius-sm); padding: 0.9rem 1.1rem;
        font-size: 0.83rem; color: #7A6000; line-height: 1.5;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #C4785A 0%, #D4926B 100%) !important;
        color: white !important; border: none !important; border-radius: 50px !important;
        padding: 0.75rem 2.5rem !important; font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important; font-size: 1rem !important;
        box-shadow: 0 4px 20px rgba(196,120,90,0.35) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 30px rgba(196,120,90,0.4) !important; }
    .btn-secondary .stButton > button {
        background: transparent !important; color: #C4785A !important;
        border: 1.5px solid #C4785A !important; box-shadow: none !important;
    }

    /* ── Tags / badges ── */
    .ingredient-tag {
        display: inline-block; background: var(--blush); color: var(--terracotta);
        border-radius: 20px; padding: 0.3rem 0.9rem;
        font-size: 0.82rem; font-weight: 500; margin: 0.2rem;
        border: 1px solid rgba(196,120,90,0.2);
    }
    .severity-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }
    .severity-mild     { background: #E8F5E9; color: #2E7D32; }
    .severity-moderate { background: #FFF3E0; color: #E65100; }
    .severity-severe   { background: #FCE4EC; color: #C62828; }
    .severity-clear    { background: #E3F2FD; color: #1565C0; }

    /* ── Confidence bars ── */
    .confidence-bar { height: 6px; border-radius: 3px; background: var(--blush); overflow: hidden; margin: 0.4rem 0; }
    .confidence-fill { height: 100%; background: linear-gradient(90deg, #C4785A, #8FAE89); border-radius: 3px; }

    /* ── Result card ── */
    .result-card {
        background: linear-gradient(135deg, #FFFDF9, #F9F5F2);
        border-radius: var(--radius); padding: 2rem;
        border: 1px solid rgba(196,120,90,0.2); box-shadow: var(--shadow-md);
        position: relative; overflow: hidden;
    }
    .result-card::before {
        content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
        background: linear-gradient(180deg, #C4785A, #8FAE89); border-radius: 4px 0 0 4px;
    }

    /* ── Product card ── */
    .product-card {
        background: #FFFFFF; border-radius: var(--radius); padding: 1.5rem;
        box-shadow: var(--shadow-sm); border: 1px solid var(--border); height: 100%;
    }
    .product-brand { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 600; margin-bottom: 0.3rem; }
    .product-name  { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: var(--deep); font-weight: 600; margin-bottom: 0.6rem; line-height: 1.3; }
    .product-why   { font-size: 0.83rem; color: var(--muted); line-height: 1.5; font-style: italic; }

    /* ── Routine step ── */
    .routine-step {
        display: flex; align-items: flex-start; gap: 1rem; padding: 1.2rem;
        background: #FFFFFF; border-radius: var(--radius-sm);
        border: 1px solid var(--border); margin-bottom: 0.7rem; box-shadow: var(--shadow-sm);
    }
    .step-number {
        width: 36px; height: 36px; border-radius: 50%;
        background: linear-gradient(135deg, #C4785A, #D4926B);
        color: white; font-weight: 700; font-size: 0.9rem;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }

    /* ── Misc ── */
    .card-sm { background: #FFFFFF; border-radius: var(--radius-sm); padding: 1rem 1.3rem; box-shadow: var(--shadow-sm); border: 1px solid var(--border); margin-bottom: 0.7rem; font-size: 0.88rem; color: var(--deep); }
    .section-divider { height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent); margin: 3rem 0; }
    .main .block-container { padding: 0; max-width: 100%; }
    .content-wrapper { max-width: 1200px; margin: 0 auto; padding: 2rem; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; background: transparent; border-bottom: 1px solid var(--border); }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px 8px 0 0; font-family: 'DM Sans', sans-serif; font-weight: 500; color: var(--muted); padding: 0.7rem 1.4rem; border: none; }
    .stTabs [aria-selected="true"] { background: #FFFFFF !important; color: #C4785A !important; border: 1px solid var(--border) !important; border-bottom: 1px solid #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)


def render_nav():
    st.markdown("""
    <div class="nav-bar">
        <div class="nav-logo">Skin<span>Meta</span> AI</div>
        <div style="display:flex;gap:1rem;align-items:center;">
            <span style="font-size:0.85rem;color:var(--muted);font-weight:500;">Powered by XAI</span>
            <span class="feature-pill">&#10022; Beta</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero():
    col1, col2 = st.columns([1.1, 0.9], gap="large")
    with col1:
        st.markdown("""
        <div style="padding:3rem 0 2rem 2rem;">
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1.5rem;">
                <span class="feature-pill">&#128302; CNN Detection</span>
                <span class="feature-pill">&#128161; Explainable AI</span>
                <span class="feature-pill">&#129380; Personalized</span>
            </div>
            <div class="hero-title">Your skin,<br><span>decoded</span><br>by AI.</div>
            <div style="font-size:1.1rem;color:var(--muted);font-weight:300;margin:1.5rem 0 2rem;line-height:1.7;max-width:480px;">
                Upload a photo, answer a few questions. SkinMeta AI analyzes your skin using deep
                learning and maps real skincare products to your unique needs.
            </div>
            <div style="font-size:0.82rem;color:var(--muted);">
                &#10003; Acne classification &nbsp;&middot;&nbsp;
                &#10003; Ingredient matching &nbsp;&middot;&nbsp;
                &#10003; Product filtering
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="padding:2rem;">
            <div style="background:linear-gradient(135deg,#F9F0EB,#EEF3EC);border-radius:24px;padding:2.5rem;box-shadow:var(--shadow-lg);border:1px solid var(--border);">
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


# ─────────────────────────────────────────────────────────────────────────────
def render_analysis_section():
    from utils.cnn_model import CNNModel
    from utils.recommend import RecommendationEngine
    from utils.product_bridge import ProductBridge
    from utils.filters import ProductFilter

    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1.5rem;">
        <div class="section-title">Analyze Your Skin</div>
        <div class="section-subtitle">Upload a clear, well-lit photo of your face &middot; No filters or makeup</div>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_profile = st.columns([1, 1], gap="large")

    # ── LEFT CARD ─────────────────────────────────────────────────────────────
    with col_input:
        with st.container(border=True):
            # These two markdown calls are INSIDE the bordered container
            # and render ABOVE the file uploader — exactly what you want.
            st.markdown('<p class="card-header">&#128248; Upload Skin Image</p>', unsafe_allow_html=True)
            st.markdown('<p class="card-sub">JPG, PNG or JPEG &middot; Max 10MB &middot; Clear, well-lit selfie</p>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Upload skin image",
                type=["jpg", "jpeg", "png"],
                label_visibility="collapsed",
                key="skin_image"
            )
            if uploaded_file:
                image = Image.open(uploaded_file).convert("RGB")
                st.image(image, caption="Your photo", use_container_width=True)
                st.markdown(
                    '<div class="transparency-box">&#9989; Image loaded. Ready for analysis.</div>',
                    unsafe_allow_html=True
                )

    # ── RIGHT CARD ────────────────────────────────────────────────────────────
    with col_profile:
        with st.container(border=True):
            st.markdown('<p class="card-header">&#128100; Skin Profile Questionnaire</p>', unsafe_allow_html=True)
            st.markdown('<p class="card-sub">Used for rule-based refinement only</p>', unsafe_allow_html=True)
            skin_type   = st.selectbox("Skin Type",   ["Normal","Oily","Dry","Combination","Sensitive"], key="skin_type")
            sensitivity = st.selectbox("Sensitivity Level", ["Low","Moderate","High"], key="sensitivity")
            age_group   = st.selectbox("Age Group",   ["14-18","19-24","25-34","35-44","45+"], key="age_group")
            climate     = st.selectbox("Climate",     ["Temperate","Tropical / Humid","Dry / Arid","Cold"], key="climate")
            concerns    = st.multiselect("Skin Concerns",
                ["Acne","Blackheads","Dark Spots","Oiliness","Dryness","Redness","Enlarged Pores","Uneven Texture"],
                default=["Acne"], key="concerns")
            st.markdown("""
            <div class="transparency-box">
                &#128161; <strong>Transparency Note:</strong> Ingredients are recommended via CNN
                acne-type prediction. Questionnaire answers refine results rule-based
                (e.g. sensitive skin &rarr; no harsh exfoliants).
            </div>
            """, unsafe_allow_html=True)

    # ── Centered analyze button ───────────────────────────────────────────────
    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([2, 1.5, 2])
    with btn_col:
        analyze_clicked = st.button("✨ Analyze My Skin", key="analyze_btn", use_container_width=True)

    st.markdown("""
    <div class="disclaimer-box" style="margin-top:1.2rem;">
        &#9888;&#65039; <strong>Medical Disclaimer:</strong> SkinMeta AI is an educational tool and
        does not provide medical advice. Consult a dermatologist for persistent or severe conditions.
        Results are AI predictions and may not always be accurate.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Run analysis ──────────────────────────────────────────────────────────
    if analyze_clicked:
        if not uploaded_file:
            st.error("Please upload a skin image first.")
            return

        profile = {
            "skin_type": skin_type, "sensitivity": sensitivity,
            "age_group": age_group, "climate": climate, "concerns": concerns,
        }
        try:
            with st.spinner("Analyzing your skin..."):
                time.sleep(0.8)
                cnn        = CNNModel()
                rec_engine = RecommendationEngine()
                bridge     = ProductBridge()
                pf         = ProductFilter()

                image_bytes       = uploaded_file.getvalue()
                cnn_result        = cnn.predict(image_bytes)
                rec_result        = rec_engine.recommend(
                    acne_type=cnn_result["acne_type"],
                    severity=cnn_result["severity_level"],
                    skin_profile=profile,
                )
                products          = bridge.get_products(
                    formula=rec_result["formula"],
                    acne_type=cnn_result["acne_type"],
                    top_n=9,
                )
                filtered_products = pf.filter(products, profile)

            st.session_state.update({
                "analysis_done":  True,
                "cnn_result":     cnn_result,
                "rec_result":     rec_result,
                "products":       filtered_products,
                "profile":        profile,
                "uploaded_image": image,
            })
            st.rerun()

        except ValueError as ve:
            err = str(ve)
            msg = err.replace("NOT_SKIN: ", "") if "NOT_SKIN" in err else err
            st.error(f"This doesn't look like a skin photo. {msg}")
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
def _sev_class(s):
    s = s.lower().strip()
    if s in ("severe","high"):     return "severity-severe"
    if s in ("moderate","medium"): return "severity-moderate"
    if s in ("clear","none"):      return "severity-clear"
    return "severity-mild"

def _sev_icon(s):
    s = s.lower().strip()
    if s in ("severe","high"):     return "&#128308;"
    if s in ("moderate","medium"): return "&#128993;"
    return "&#128994;"


def render_results():
    cnn_result     = st.session_state.get("cnn_result", {})
    rec_result     = st.session_state.get("rec_result", {})
    products       = st.session_state.get("products", [])
    uploaded_image = st.session_state.get("uploaded_image")

    acne_type  = cnn_result.get("acne_type", "Unknown")
    severity   = cnn_result.get("severity", "Mild")
    confidence = cnn_result.get("confidence", 0.82)
    all_probs  = cnn_result.get("probabilities", {})
    conf_pct   = int(confidence * 100)

    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;flex-wrap:wrap;">'
        f'<div class="section-title">Analysis Results</div>'
        f'<span class="severity-badge {_sev_class(severity)}">{_sev_icon(severity)} {severity}</span>'
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
        prob_rows = "".join(
            f'<div style="margin-bottom:0.5rem;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">'
            f'<span style="font-size:0.8rem;color:#2A1F1A;">{cls}</span>'
            f'<span style="font-size:0.8rem;color:#7A6E6A;">{int(prob*100)}%</span></div>'
            f'<div class="confidence-bar">'
            f'<div style="height:4px;width:{int(prob*100)}%;'
            f'background:{"#C4785A" if cls==acne_type else "#C8D8C4"};border-radius:3px;"></div>'
            f'</div></div>'
            for cls, prob in sorted(all_probs.items(), key=lambda x: -x[1])
        )
        st.markdown(
            f'<div class="result-card">'
            f'<div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:#7A6E6A;margin-bottom:0.3rem;">Detected Condition</div>'
            f'<div style="font-family:\'Playfair Display\',serif;font-size:1.8rem;color:#2A1F1A;font-weight:600;margin-bottom:1.2rem;">{acne_type}</div>'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">'
            f'<span style="font-size:0.82rem;color:#7A6E6A;">Model Confidence</span>'
            f'<span style="font-size:0.82rem;font-weight:600;color:#C4785A;">{conf_pct}%</span></div>'
            f'<div class="confidence-bar"><div class="confidence-fill" style="width:{conf_pct}%;"></div></div>'
            f'<div style="margin:1rem 0 0.6rem;font-size:0.82rem;color:#7A6E6A;font-weight:500;">All Class Probabilities</div>'
            f'{prob_rows}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### &#127807; Recommended Ingredients")
    st.markdown('<div class="transparency-box">&#129302; Ingredients recommended by <strong>CNN acne-type prediction</strong>, refined via rule-based skin profile logic.</div>', unsafe_allow_html=True)

    ingredients = rec_result.get("ingredients_by_category", {})
    adjustments = rec_result.get("adjustments", [])

    if ingredients:
        cols = st.columns(min(len(ingredients), 3))
        for i, (category, ing_list) in enumerate(ingredients.items()):
            with cols[i % len(cols)]:
                tags    = "".join(f'<span class="ingredient-tag">{ing["name"]}</span>' for ing in ing_list)
                benefit = f'<div class="product-why" style="margin-top:0.8rem;">{ing_list[0].get("benefit","")}</div>' if ing_list else ""
                st.markdown(
                    f'<div class="product-card" style="min-height:150px;">'
                    f'<div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:#7A6E6A;margin-bottom:0.7rem;">{category}</div>'
                    f'{tags}{benefit}</div>',
                    unsafe_allow_html=True
                )

    if adjustments:
        st.markdown("**Profile Adjustments Applied:**")
        for adj in adjustments:
            st.markdown(f'<div class="card-sm">&#9881; {adj}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### &#128717; Recommended Products")
    explanation = rec_result.get("explanation","")
    if explanation:
        st.markdown(f'<div class="transparency-box">&#129302; <strong>Why these products?</strong><br>{explanation}</div>', unsafe_allow_html=True)

    if not products:
        st.info("No matching products found. Try uploading a different image.")
    else:
        st.markdown(f'<div style="font-size:0.85rem;color:#7A6E6A;margin-bottom:1rem;">Showing {len(products)} products &middot; Filtered for acne-prone skin</div>', unsafe_allow_html=True)
        cat_groups: dict = {}
        for p in products:
            cat_groups.setdefault(p.get("category","Treatment"), []).append(p)

        for category, cat_products in cat_groups.items():
            st.markdown(f"**{category}**")
            pcols = st.columns(min(len(cat_products), 3))
            for j, prod in enumerate(cat_products[:3]):
                with pcols[j]:
                    score_pct = int(prod.get("match_score", 0.7) * 100)
                    ing_tags  = "".join(f'<span class="ingredient-tag">{ing}</span>' for ing in prod.get("key_ingredients",[])[:3])
                    st.markdown(
                        f'<div class="product-card">'
                        f'<div class="product-brand">{prod.get("brand","Brand")}</div>'
                        f'<div class="product-name">{prod.get("name","Product")}</div>'
                        f'<div style="margin-bottom:0.8rem;">{ing_tags}</div>'
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">'
                        f'<span style="font-size:0.75rem;color:#7A6E6A;">Match</span>'
                        f'<span style="font-size:0.75rem;font-weight:600;color:#C4785A;">{score_pct}%</span></div>'
                        f'<div class="confidence-bar"><div class="confidence-fill" style="width:{score_pct}%;"></div></div>'
                        f'<div class="product-why" style="margin-top:0.6rem;">{prod.get("why_recommended","Suitable for acne-prone skin.")}</div>'
                        f'<div style="font-size:0.75rem;color:#7A6E6A;margin-top:0.6rem;padding-top:0.6rem;border-top:1px solid rgba(42,31,26,0.08);">&#128161; {prod.get("usage","Apply as directed.")}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    st.markdown("---")
    st.markdown("### &#128197; Personalized Routine")

    routine    = rec_result.get("routine", {})
    am_routine = routine.get("am", [])
    pm_routine = routine.get("pm", [])
    notes      = routine.get("notes", [])

    def step_hint(step_name, prod_list):
        sn = step_name.lower()
        matched = [
            p for p in prod_list
            if ("cleanser"    in sn and any(x in p.get("category","").lower() for x in ["cleanser","wash"]))
            or ("toner"       in sn and any(x in p.get("category","").lower() for x in ["toner","essence"]))
            or ("treatment"   in sn and any(x in p.get("category","").lower() for x in ["serum","treatment"]))
            or ("moisturizer" in sn and any(x in p.get("category","").lower() for x in ["moisturizer","cream","lotion"]))
            or ("spf"         in sn and any(x in p.get("category","").lower() for x in ["sunscreen","spf"]))
            or ("repair"      in sn and any(x in p.get("category","").lower() for x in ["moisturizer","cream","lotion"]))
        ]
        if not matched:
            return ""
        labels = ", ".join("{} {}".format(p.get("brand",""), p.get("name","")).strip() for p in matched[:2])
        return f'<div style="font-size:0.75rem;color:#C4785A;font-weight:600;margin-top:0.4rem;">&#10024; Try: {labels}</div>'

    tab_am, tab_pm = st.tabs(["☀️ Morning (AM)", "🌙 Night (PM)"])

    with tab_am:
        if am_routine:
            for step in am_routine:
                actives = ", ".join(step.get("actives",[])[:2])
                tag     = f'<span class="ingredient-tag">{actives}</span>' if actives else ""
                hint    = step_hint(step.get("name",""), products)
                st.markdown(
                    f'<div class="routine-step">'
                    f'<div class="step-number">{step["step"]}</div>'
                    f'<div style="flex:1;">'
                    f'<div style="font-weight:600;color:#2A1F1A;margin-bottom:0.2rem;">{step["name"]}</div>'
                    f'<div style="font-size:0.82rem;color:#7A6E6A;">{step["description"]}</div>'
                    f'<div style="margin-top:0.3rem;">{tag}</div>{hint}'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Morning routine will appear after analysis.")

    with tab_pm:
        if pm_routine:
            for step in pm_routine:
                actives = ", ".join(step.get("actives",[])[:2])
                tag     = f'<span class="ingredient-tag">{actives}</span>' if actives else ""
                hint    = step_hint(step.get("name",""), products)
                st.markdown(
                    f'<div class="routine-step">'
                    f'<div class="step-number" style="background:linear-gradient(135deg,#5C5470,#352F44);">{step["step"]}</div>'
                    f'<div style="flex:1;">'
                    f'<div style="font-weight:600;color:#2A1F1A;margin-bottom:0.2rem;">{step["name"]}</div>'
                    f'<div style="font-size:0.82rem;color:#7A6E6A;">{step["description"]}</div>'
                    f'<div style="margin-top:0.3rem;">{tag}</div>{hint}'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Night routine will appear after analysis.")

    if notes:
        for note in notes:
            st.markdown(f'<div class="disclaimer-box" style="margin-top:0.8rem;">&#128161; {note}</div>', unsafe_allow_html=True)

    st.markdown("---")
    col_reset, _ = st.columns([1, 3])
    with col_reset:
        st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
        if st.button("↺ New Analysis", key="reset_btn"):
            for k in ["analysis_done","cnn_result","rec_result","products","profile","uploaded_image"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <div style="background:#2A1F1A;color:rgba(255,255,255,0.6);padding:3rem 2rem;margin-top:4rem;">
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

    if not st.session_state.get("analysis_done", False):
        render_hero()
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        render_analysis_section()
    else:
        render_results()

    render_footer()


if __name__ == "__main__":
    main()