import base64
import difflib
import hashlib
import html
import io
import json
import math
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
from pypdf import PdfReader
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

import i18n
import theme

try:
    from supabase import create_client
except Exception:
    create_client = None
try:
    import extra_streamlit_components as stx
except Exception:
    stx = None

APP_NAME = "AI Quiz Arena"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Client-side persistence for localStorage
LOCALSTORAGE_JS = """
<script>
(function() {
    const savedLang = localStorage.getItem('app_ui_lang');
    if (savedLang) {
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.has('lang')) {
            // Synchronize session state via query parameter if missing
        }
    }
})();
function saveLanguage(lang) {
    localStorage.setItem('app_ui_lang', lang);
}
</script>
"""
st.markdown(LOCALSTORAGE_JS, unsafe_allow_html=True)

LIGHT = bool(st.session_state.get("light", False))
st.markdown(theme.PREMIUM_CSS, unsafe_allow_html=True)
if LIGHT:
    st.markdown(theme.PREMIUM_LIGHT_CSS, unsafe_allow_html=True)

# ── API KEY ──
try:
    api_key = st.secrets.get("GROQ_API_KEY")
except Exception:
    api_key = None
api_key = api_key or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key not found. Please add `GROQ_API_KEY` to Secrets.")
    st.stop()

@st.cache_resource
def get_client(key: str):
    return Groq(api_key=key)

client = get_client(api_key)

MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_CHARS = 24000
MAX_IMG_BYTES = 3 * 1024 * 1024
MAX_RAW_IMG_BYTES = 15 * 1024 * 1024
MAX_TOTAL_Q = 200

TYPE_MAP = {
    "Multiple Choice": "mcq",
    "True / False": "tf",
    "Multi-select": "multi",
    "Fill in the blank": "blank",
    "Short answer (AI check)": "short",
    "Numerical value": "num",
}

# ── SIDEBAR LANGUAGE SWITCHER ──
i18n.init_ui_lang()

with st.sidebar:
    st.markdown("### 🌐 Language / भाषा")
    selected_lang_str = st.selectbox(
        "Select Application Language",
        options=i18n.LANG_ORDER,
        index=0 if i18n.cur() == "en" else 1,
        key="lang_switcher_select",
        label_visibility="collapsed"
    )
    
    target_code = i18n.LANGS[selected_lang_str]
    if target_code != i18n.cur():
        i18n.set_ui_lang(target_code)
        components.html(f"<script>saveLanguage('{target_code}');</script>", height=0)
        st.rerun()

    st.markdown("### ⚙️ Quiz Settings")
    num_questions = st.slider("Questions", 3, 50, 5)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    adaptive = st.toggle("🎚️ Adaptive difficulty", value=False)
    type_sel = st.multiselect("Question types", list(TYPE_MAP.keys()), default=["Multiple Choice", "True / False"])
    type_keys = [TYPE_MAP[x] for x in type_sel] or ["mcq"]
    mode = st.radio("Mode", ["Practice", "Exam", "Survival"])

    with st.expander("🔊 Sound & Look"):
        sound_on = st.toggle("Sound effects", value=True)
        auto_read = st.toggle("Read questions aloud automatically", value=False)
        tts_rate = st.slider("Speaking speed", 0.6, 1.4, 1.0, 0.1)
        st.toggle("☀️ Light mode", value=False, key="light")

    with st.expander("Advanced"):
        model = st.selectbox("AI model", MODELS)

# ── HERO SECTION ──
cur_lang = i18n.cur()
sub_text = "Provide a topic, PDF or notes photo — AI generates quizzes instantly." if cur_lang == "en" else "टॉपिक, PDF या नोट्स की फ़ोटो दो — AI तुरंत क्विज़ बनाता है।"

st.markdown(
    theme.hero_html(APP_NAME, sub_text, show_chips=True),
    unsafe_allow_html=True
)

# ── TAB NAVIGATION ──
tab_quiz, tab_pyq, tab_doubt = st.tabs(["🧠 Quiz Arena", "🏛️ Govt Exam PYQs", "🔍 Doubt Solver"])

with tab_quiz:
    st.markdown("### " + i18n.tr("🧠 Quiz Arena"))
    topic = st.text_input("Which topic do you want a quiz on?", placeholder="e.g. Machine Learning basics, Indian Constitution, Python lists…")
    if st.button("✨ Make quiz", type="primary", use_container_width=True):
        if not topic:
            st.warning("First write a topic, upload/click a photo or paste notes.")
        else:
            st.info(f"Generating quiz for: {topic}")

with tab_pyq:
    st.markdown("### " + i18n.tr("🏛️ Govt & Entrance Exam Practice"))
    st.caption("Practice real exam PYQs with official marking schemes.")

with tab_doubt:
    st.markdown("### " + i18n.tr("🔍 AI Doubt Solver"))
    st.text_area("Write your doubt here", placeholder="Ask any question...")
    if st.button("💡 Explain", type="primary"):
        st.success("Analyzing your doubt...")
