import streamlit as st
import base64
from pathlib import Path

LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"


def get_logo_base64() -> str:
    if LOGO_PATH.exists():
        return base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return ""


def inject_glassmorphism():
    logo_b64 = get_logo_base64()

    st.markdown(f"""
    <style>
    /* ===== GLASSMORPHISM THEME — WP Brand Colors ===== */
    /* Palette: Coral #E84D3D | Red #D94452 | Magenta #8B2F8F | Deep Purple #3A1857 */

    /* --- Animated gradient background --- */
    .stApp {{
        background: linear-gradient(135deg, #0F0A1A 0%, #1A1228 30%, #2A1540 60%, #1A1228 100%) !important;
        background-attachment: fixed !important;
    }}

    /* Subtle animated gradient orbs behind content */
    .stApp::before {{
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background:
            radial-gradient(circle at 20% 30%, rgba(232, 77, 61, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(139, 47, 143, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(217, 68, 82, 0.05) 0%, transparent 60%);
        animation: orbFloat 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }}

    @keyframes orbFloat {{
        0%, 100% {{ transform: translate(0, 0) rotate(0deg); }}
        33% {{ transform: translate(30px, -30px) rotate(120deg); }}
        66% {{ transform: translate(-20px, 20px) rotate(240deg); }}
    }}

    /* --- Glass card for main content blocks --- */
    .stMainBlockContainer > div > div > div > div {{
        position: relative;
        z-index: 1;
    }}

    /* Main block container */
    [data-testid="stMainBlockContainer"] {{
        position: relative;
        z-index: 1;
    }}

    /* --- Sidebar glass --- */
    [data-testid="stSidebar"] {{
        background: rgba(26, 18, 40, 0.7) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(217, 68, 82, 0.15) !important;
    }}

    [data-testid="stSidebar"] > div {{
        background: transparent !important;
    }}

    /* --- Metrics glass cards --- */
    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(217, 68, 82, 0.2) !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        transition: all 0.3s ease !important;
    }}

    [data-testid="stMetric"]:hover {{
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(232, 77, 61, 0.4) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(217, 68, 82, 0.15) !important;
    }}

    [data-testid="stMetricValue"] {{
        color: #E84D3D !important;
        font-weight: 700 !important;
    }}

    [data-testid="stMetricLabel"] {{
        color: rgba(240, 230, 246, 0.7) !important;
    }}

    /* --- Tabs glass styling --- */
    .stTabs [data-baseweb="tab-list"] {{
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        border: 1px solid rgba(139, 47, 143, 0.2) !important;
        gap: 4px !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: rgba(240, 230, 246, 0.6) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(217, 68, 82, 0.1) !important;
        color: #F0E6F6 !important;
    }}

    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, rgba(232, 77, 61, 0.2), rgba(139, 47, 143, 0.2)) !important;
        color: #F0E6F6 !important;
        border: 1px solid rgba(217, 68, 82, 0.3) !important;
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        display: none !important;
    }}

    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}

    /* --- File uploader glass --- */
    [data-testid="stFileUploader"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 2px dashed rgba(217, 68, 82, 0.3) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        transition: all 0.3s ease !important;
    }}

    [data-testid="stFileUploader"]:hover {{
        border-color: rgba(232, 77, 61, 0.5) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 0 30px rgba(217, 68, 82, 0.1) !important;
    }}

    [data-testid="stFileUploader"] section {{
        background: transparent !important;
        padding: 0 !important;
    }}

    [data-testid="stFileUploader"] section > button {{
        background: linear-gradient(135deg, #E84D3D, #8B2F8F) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
        transition: all 0.3s ease !important;
    }}

    [data-testid="stFileUploader"] section > button:hover {{
        box-shadow: 0 4px 20px rgba(232, 77, 61, 0.4) !important;
        transform: translateY(-1px);
    }}

    /* --- Primary button gradient --- */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, #E84D3D, #D94452, #8B2F8F) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(217, 68, 82, 0.3) !important;
    }}

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {{
        box-shadow: 0 6px 25px rgba(232, 77, 61, 0.5) !important;
        transform: translateY(-2px) !important;
    }}

    /* --- Secondary / download buttons --- */
    .stDownloadButton > button {{
        background: rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(217, 68, 82, 0.3) !important;
        border-radius: 10px !important;
        color: #F0E6F6 !important;
        transition: all 0.3s ease !important;
    }}

    .stDownloadButton > button:hover {{
        background: rgba(217, 68, 82, 0.15) !important;
        border-color: rgba(232, 77, 61, 0.5) !important;
    }}

    /* --- Expanders glass --- */
    [data-testid="stExpander"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(139, 47, 143, 0.15) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }}

    [data-testid="stExpander"]:hover {{
        border-color: rgba(217, 68, 82, 0.3) !important;
    }}

    [data-testid="stExpander"] details {{
        background: transparent !important;
        border: none !important;
    }}

    [data-testid="stExpander"] summary {{
        color: #F0E6F6 !important;
    }}

    /* --- Status container glass --- */
    [data-testid="stStatusWidget"],
    .stStatus {{
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(139, 47, 143, 0.2) !important;
        border-radius: 12px !important;
    }}

    /* --- Text input / select glass --- */
    .stTextInput > div > div,
    .stSelectbox > div > div,
    .stNumberInput > div > div {{
        background: rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(139, 47, 143, 0.2) !important;
        border-radius: 10px !important;
        color: #F0E6F6 !important;
    }}

    .stTextInput > div > div:focus-within,
    .stSelectbox > div > div:focus-within {{
        border-color: rgba(217, 68, 82, 0.5) !important;
        box-shadow: 0 0 15px rgba(217, 68, 82, 0.15) !important;
    }}

    /* --- Text area glass --- */
    .stTextArea textarea {{
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(139, 47, 143, 0.15) !important;
        border-radius: 10px !important;
        color: #F0E6F6 !important;
    }}

    /* --- Alerts glass --- */
    [data-testid="stAlert"] {{
        backdrop-filter: blur(8px) !important;
        border-radius: 12px !important;
    }}

    .stAlert div[data-testid="stNotification"][data-type="error"] {{
        background: rgba(232, 77, 61, 0.12) !important;
        border: 1px solid rgba(232, 77, 61, 0.3) !important;
        border-radius: 12px !important;
    }}

    .stAlert div[data-testid="stNotification"][data-type="success"] {{
        background: rgba(46, 204, 113, 0.1) !important;
        border: 1px solid rgba(46, 204, 113, 0.3) !important;
        border-radius: 12px !important;
    }}

    .stAlert div[data-testid="stNotification"][data-type="info"] {{
        background: rgba(139, 47, 143, 0.12) !important;
        border: 1px solid rgba(139, 47, 143, 0.3) !important;
        border-radius: 12px !important;
    }}

    .stAlert div[data-testid="stNotification"][data-type="warning"] {{
        background: rgba(232, 77, 61, 0.08) !important;
        border: 1px solid rgba(232, 77, 61, 0.2) !important;
        border-radius: 12px !important;
    }}

    /* --- Dividers --- */
    [data-testid="stHorizontalRule"],
    hr {{
        border-color: rgba(139, 47, 143, 0.2) !important;
    }}

    /* --- Checkbox styling --- */
    .stCheckbox label span[data-testid="stCheckbox"] {{
        color: #F0E6F6 !important;
    }}

    [data-testid="stCheckbox"] input:checked + div {{
        background-color: #D94452 !important;
        border-color: #D94452 !important;
    }}

    /* --- Headings glow --- */
    h1 {{
        background: linear-gradient(135deg, #E84D3D, #D94452, #8B2F8F) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 800 !important;
    }}

    h2, h3 {{
        color: rgba(240, 230, 246, 0.95) !important;
    }}

    /* --- Scrollbar --- */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: rgba(15, 10, 26, 0.5);
    }}

    ::-webkit-scrollbar-thumb {{
        background: rgba(217, 68, 82, 0.3);
        border-radius: 3px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(217, 68, 82, 0.5);
    }}

    /* --- Code blocks --- */
    code, .stCode {{
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(139, 47, 143, 0.15) !important;
        border-radius: 8px !important;
    }}

    /* --- Form submit button --- */
    [data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(135deg, #E84D3D, #8B2F8F) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}

    /* --- Sidebar specific overrides --- */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        background: none !important;
        -webkit-text-fill-color: #F0E6F6 !important;
    }}

    /* --- Caption / small text --- */
    .stCaption, [data-testid="stCaption"] {{
        color: rgba(240, 230, 246, 0.5) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Inject logo in sidebar
    if logo_b64:
        st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <img src="data:image/png;base64,{logo_b64}" width="120"
                 style="filter: drop-shadow(0 4px 15px rgba(217, 68, 82, 0.3));">
        </div>
        """, unsafe_allow_html=True)
