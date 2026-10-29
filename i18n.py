import io
import os
import hashlib
import re
import json
import math
import time
import base64
import random
import difflib
import html
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from groq import Groq

try:  # login + database (optional: without it the app runs in guest mode)
    from supabase import create_client
except Exception:
    create_client = None

try:  # keeps the user logged in after a page refresh
    import extra_streamlit_components as stx
except Exception:
    stx = None

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
APP_NAME = "AI Quiz Arena"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

LIGHT = bool(st.session_state.get("light", False))

# ─────────────────────────────────────────────────────────────
# MULTI-LANGUAGE TRANSLATION DICTIONARY
# ─────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "English": {
        "hero_sub": "Provide a Topic, PDF, or photo of notes — AI generates quizzes instantly. Learn with Audio, Timer, Lives, XP, and Badges.",
        "step_1": "1 · Choose Content",
        "step_2": "2 · Play Quiz",
        "step_3": "3 · View Result",
        "tab_quiz": "🧠 Quiz Arena",
        "tab_pyq": "🏛️ Govt Exam PYQs",
        "tab_doubt": "🔍 Doubt Solver",
        "app_lang": "🌐 App Language",
        "src_prompt": "Where should the content come from?",
        "topic_input": "Which topic do you want a quiz on?",
        "topic_placeholder": "e.g. Machine Learning basics, Indian Constitution, Python lists…",
        "quick_picks": "Quick Picks",
        "generate_btn": "✨ Generate Quiz",
        "start_pyq_btn": "🚀 Start Exam Practice",
        "back_btn": "⬅️ Back",
        "next_btn": "Next ➡️",
        "finish_btn": "Finish 🏁",
        "check_btn": "Check answer",
        "skip_btn": "Skip ⏭️",
        "hint_btn": "💡 Hint (-5 XP)",
        "save_btn": "🔖 Save",
        "saved_btn": "📌 Saved",
        "listen_btn": "🔊 Listen",
        "new_quiz": "🔁 New Quiz",
        "retry_wrong": "🎯 Retry Wrong Only",
        "restart_quiz": "🔄 Restart Same Quiz",
        "fresh_q": "🆕 Fresh Questions",
        "flashcards_btn": "📇 Flashcards",
        "level": "Level",
        "total_xp": "Total XP",
        "quizzes_played": "Quizzes Played",
        "best_score": "Best Score",
        "settings": "⚙️ Quiz Settings",
        "questions_count": "Questions",
        "difficulty": "Difficulty",
        "adaptive": "🎚️ Adaptive Difficulty",
        "q_types": "Question Types",
        "mode": "Mode",
        "timer": "⏱️ Timer Type",
        "marking": "🎯 Marking",
        "saved_questions": "🔖 Saved Questions",
        "my_history": "🏆 My History",
        "account": "👤 Account",
        "logout": "🚪 Logout",
        "backup": "💾 Progress Backup",
    },
    "Hinglish": {
        "hero_sub": "Topic, PDF ya notes ki photo do — AI turant quiz banata hai. Awaaz, timer, lives, XP aur badges ke saath seekho.",
        "step_1": "1 · Content chuno",
        "step_2": "2 · Quiz khelo",
        "step_3": "3 · Result dekho",
        "tab_quiz": "🧠 Quiz Arena",
        "tab_pyq": "🏛️ Govt Exam PYQs",
        "tab_doubt": "🔍 Doubt Solver",
        "app_lang": "🌐 App Language",
        "src_prompt": "Content kahan se aayega?",
        "topic_input": "Kis topic par quiz chahiye?",
        "topic_placeholder": "e.g. Machine Learning basics, Indian Constitution, Python lists…",
        "quick_picks": "Quick Picks",
        "generate_btn": "✨ Quiz banao",
        "start_pyq_btn": "🚀 Practice shuru karo",
        "back_btn": "⬅️ Back",
        "next_btn": "Next ➡️",
        "finish_btn": "Finish 🏁",
        "check_btn": "Check answer",
        "skip_btn": "Skip ⏭️",
        "hint_btn": "💡 Hint (-5 XP)",
        "save_btn": "🔖 Save",
        "saved_btn": "📌 Saved",
        "listen_btn": "🔊 Sunao",
        "new_quiz": "🔁 Naya Quiz",
        "retry_wrong": "🎯 Sirf galat dobara",
        "restart_quiz": "🔄 Wahi quiz phir se",
        "fresh_q": "🆕 Naye sawal",
        "flashcards_btn": "📇 Flashcards",
        "level": "Level",
        "total_xp": "Total XP",
        "quizzes_played": "Quizzes Khele",
        "best_score": "Best Score",
        "settings": "⚙️ Quiz Settings",
        "questions_count": "Sawal",
        "difficulty": "Difficulty",
        "adaptive": "🎚️ Adaptive Difficulty",
        "q_types": "Question Types",
        "mode": "Mode",
        "timer": "⏱️ Timer Type",
        "marking": "🎯 Marking",
        "saved_questions": "🔖 Saved Questions",
        "my_history": "🏆 Meri History",
        "account": "👤 Account",
        "logout": "🚪 Logout",
        "backup": "💾 Progress Backup",
    },
    "Hindi": {
        "hero_sub": "विषय, पीडीएफ या नोट्स की फोटो दें — एआई तुरंत क्विज़ बनाता है। आवाज, टाइमर, लाइव्स, एक्सपी और बैज के साथ सीखें।",
        "step_1": "1 · सामग्री चुनें",
        "step_2": "2 · क्विज़ खेलें",
        "step_3": "3 · परिणाम देखें",
        "tab_quiz": "🧠 क्विज़ अरीना",
        "tab_pyq": "🏛️ सरकारी परीक्षा PYQ",
        "tab_doubt": "🔍 डाउट सॉल्वर",
        "app_lang": "🌐 ऐप की भाषा",
        "src_prompt": "सामग्री कहां से आएगी?",
        "topic_input": "किस विषय पर क्विज़ चाहिए?",
        "topic_placeholder": "जैसे: मशीन लर्निंग, भारतीय संविधान, पाइथन लिस्ट…",
        "quick_picks": "त्वरित चयन",
        "generate_btn": "✨ क्विज़ बनाएं",
        "start_pyq_btn": "🚀 अभ्यास शुरू करें",
        "back_btn": "⬅️ पीछे",
        "next_btn": "आगे ➡️",
        "finish_btn": "समाप्त 🏁",
        "check_btn": "उत्तर जांचें",
        "skip_btn": "छोड़ें ⏭️",
        "hint_btn": "💡 संकेत (-5 XP)",
        "save_btn": "🔖 सहेजें",
        "saved_btn": "📌 सहेजा गया",
        "listen_btn": "🔊 सुनें",
        "new_quiz": "🔁 नया क्विज़",
        "retry_wrong": "🎯 केवल गलत पुनः प्रयास करें",
        "restart_quiz": "🔄 वही क्विज़ पुनः चालू करें",
        "fresh_q": "🆕 नए प्रश्न",
        "flashcards_btn": "📇 फ्लैशकार्ड्स",
        "level": "स्तर",
        "total_xp": "कुल XP",
        "quizzes_played": "खेले गए क्विज़",
        "best_score": "सर्वश्रेष्ठ स्कोर",
        "settings": "⚙️ क्विज़ सेटिंग्स",
        "questions_count": "प्रश्न संख्या",
        "difficulty": "कठिनाई",
        "adaptive": "🎚️ अनुकूलन योग्य कठिनाई",
        "q_types": "प्रश्न के प्रकार",
        "mode": "मोड",
        "timer": "⏱️ टाइमर प्रकार",
        "marking": "🎯 अंकन योजना",
        "saved_questions": "🔖 सहेजे गए प्रश्न",
        "my_history": "🏆 मेरा इतिहास",
        "account": "👤 खाता",
        "logout": "🚪 लॉगआउट",
        "backup": "💾 प्रगति बैकअप",
    },
}


def t(key: str) -> str:
    """Translation helper for global UI language."""
    lang = st.session_state.get("app_lang", "Hinglish")
    return TRANSLATIONS.get(lang, TRANSLATIONS["Hinglish"]).get(key, key)


# ─────────────────────────────────────────────────────────────
# STYLING — Modern Futuristic Glow Interface
# ─────────────────────────────────────────────────────────────
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root{
  --bg:#070A14; --panel:rgba(255,255,255,.04); --panel-2:rgba(255,255,255,.07);
  --line:rgba(255,255,255,.12); --txt:#E2E8F0; --mute:#94A3B8;
  --violet:#8B5CF6; --cyan:#06B6D4; --amber:#F59E0B; --good:#10B981; --bad:#EF4444;
}
html, body, [class*="css"]{ font-family:'Plus Jakarta Sans',sans-serif; color:var(--txt); }
h1,h2,h3,.qf-display{ font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.02em; }

#MainMenu, footer{ visibility:hidden; height:0; }
header[data-testid="stHeader"]{ background:transparent !important; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarExpandButton"]{
  display:block !important; position:fixed !important; top:12px !important; left:12px !important; z-index:999999 !important;
  background-color:#0F172A !important; border-radius:10px !important; border:1px solid var(--line) !important;
  box-shadow:0 4px 20px rgba(0,0,0,.6) !important;
}

.stApp{
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(139,92,246,.22), transparent 60%),
    radial-gradient(900px 500px at 90% 10%, rgba(6,182,212,.18), transparent 55%),
    var(--bg);
}
.block-container{ padding-top:1.4rem; max-width:880px; }
section[data-testid="stSidebar"]{ background:#0B0F19; border-right:1px solid var(--line); }

/* Futuristic Glass Hero Box */
.qf-hero{
  position:relative; overflow:hidden; border-radius:24px; padding:36px 32px 26px; margin-bottom:20px;
  border:1px solid var(--line); backdrop-filter:blur(12px);
  background:
    linear-gradient(rgba(255,255,255,.02) 1px, transparent 1px) 0 0/24px 24px,
    linear-gradient(90deg, rgba(255,255,255,.02) 1px, transparent 1px) 0 0/24px 24px,
    linear-gradient(135deg, rgba(139,92,246,.3), rgba(6,182,212,.15) 70%, rgba(7,10,20,.6));
  box-shadow: 0 12px 32px rgba(0,0,0,0.4);
}
.qf-hero:after{
  content:""; position:absolute; width:300px; height:300px; right:-80px; top:-100px; border-radius:50%;
  background:radial-gradient(circle, rgba(245,158,11,.25), transparent 65%); filter:blur(10px);
}
.qf-title{
  font-size:3.2rem; font-weight:700; line-height:1.05; margin:0; position:relative; z-index:1;
  background:linear-gradient(90deg,#FFFFFF 10%,#DDD6FE 45%,#38BDF8 90%); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent;
}
.qf-sub{ margin-top:12px; color:#CBD5E1; font-size:1.05rem; max-width:580px; position:relative; z-index:1; line-height:1.5; }
.qf-steps{ display:flex; gap:10px; margin-top:22px; position:relative; z-index:1; flex-wrap:wrap; }
.qf-step{ padding:6px 16px; border-radius:99px; font-size:.82rem; font-weight:600; color:#94A3B8; border:1px solid rgba(255,255,255,.15); background:rgba(0,0,0,.3); }
.qf-step.on{ color:#070A14; background:var(--amber); border-color:var(--amber); font-weight:700; }
.qf-step.done{ color:var(--good); border-color:rgba(16,185,129,.4); }

/* Glass Panels & Option Cards */
.st-key-panel, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-panel_login, .st-key-optbox, .st-key-morebox{
  background:var(--panel); border:1px solid var(--line); border-radius:20px; padding:22px; backdrop-filter:blur(8px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}
.st-key-optbox{ padding:16px 18px; counter-reset:opt; }

.st-key-srcpick div[role="radiogroup"]{ gap:10px; flex-wrap:wrap; }
.st-key-srcpick label[data-baseweb="radio"]{ background:var(--panel); border:1px solid var(--line); border-radius:99px; padding:8px 18px; margin:0; transition:all 0.2s; }
.st-key-srcpick label[data-baseweb="radio"]:has(input:checked){ background:rgba(139,92,246,.3); border-color:var(--violet); }
.st-key-srcpick label[data-baseweb="radio"] > div:first-of-type{ display:none; }

.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]{
  display:flex; align-items:center; gap:12px;
  background:var(--panel-2); border:1.5px solid var(--line); border-radius:14px; padding:12px 16px; margin:0 0 12px; width:100%;
  transition:all .15s ease;
}
.st-key-optbox label[data-baseweb="radio"]::before, .st-key-optbox label[data-baseweb="checkbox"]::before{
  counter-increment:opt; content:counter(opt); flex:0 0 auto; width:30px; height:30px; border-radius:10px;
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:.88rem;
  background:rgba(139,92,246,.25); color:var(--txt); border:1px solid var(--line);
}
.st-key-optbox label[data-baseweb="radio"] > div:first-of-type{ display:none; }
.st-key-optbox label[data-baseweb="radio"]:hover, .st-key-optbox label[data-baseweb="checkbox"]:hover{ border-color:var(--cyan); transform:translateX(3px); }
.st-key-optbox label:has(input:checked){ border-color:var(--violet); background:rgba(139,92,246,.25); }
.st-key-optbox label:has(input:checked)::before{ background:var(--violet); color:#fff; border-color:var(--violet); }

/* Question Card */
.qf-qcard{
  position:relative; background:linear-gradient(160deg, rgba(139,92,246,.2), rgba(255,255,255,.03));
  border:1px solid var(--line); border-radius:22px; padding:26px 28px; margin:14px 0;
}
.qf-qcard:before{ content:""; position:absolute; left:0; top:22px; bottom:22px; width:5px; border-radius:0 6px 6px 0; background:var(--amber); }
.qf-qnum{ font-size:.85rem; font-weight:700; color:var(--amber); margin-bottom:8px; }
.qf-qtext{ font-family:'Space Grotesk',sans-serif; font-size:1.45rem; font-weight:500; line-height:1.4; }
.qf-tags{ float:right; display:flex; gap:6px; }
.qf-tag{ font-size:.76rem; padding:4px 12px; border-radius:99px; border:1px solid var(--line); color:var(--mute); }
.qf-tag.lv{ border-color:var(--cyan); color:var(--cyan); }

/* Stats Tiles */
.qf-tiles{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:16px 0 12px; }
.qf-tile{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:16px 12px; text-align:center; }
.qf-tile .v{ font-family:'Space Grotesk',sans-serif; font-size:1.6rem; font-weight:700; }
.qf-tile .l{ font-size:.78rem; color:var(--mute); margin-top:2px; }

/* Buttons & Inputs */
.stButton>button, .stDownloadButton>button{
  border-radius:14px; font-weight:700; padding:.65rem 1.2rem; border:1px solid var(--line);
  background:var(--panel-2); color:var(--txt); transition:all .15s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover{ transform:translateY(-2px); border-color:var(--cyan); }
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,var(--violet),#3B82F6 55%,var(--cyan)); border:0; color:#fff;
  box-shadow:0 8px 24px rgba(139,92,246,.4);
}
</style>
"""

LIGHT_CSS = """
<style>
:root{
  --bg:#F8FAFC; --panel:rgba(255,255,255,.85); --panel-2:#FFFFFF;
  --line:rgba(148,163,184,.3); --txt:#0F172A; --mute:#64748B;
}
.stApp{
  background:
    radial-gradient(1000px 500px at 10% -10%, rgba(139,92,246,.12), transparent 60%),
    radial-gradient(800px 420px at 90% 10%, rgba(6,182,212,.1), transparent 55%),
    #F8FAFC !important;
}
section[data-testid="stSidebar"]{ background:#FFFFFF !important; }
.qf-hero{ background:linear-gradient(135deg,#4C1D95,#6D28D9 55%,#0284C7) !important; }
.qf-hero .qf-sub{ color:#F1F5F9 !important; }
.qf-qcard{ background:linear-gradient(160deg, rgba(139,92,246,.1), rgba(255,255,255,.95)); }
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)
if LIGHT:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# API KEY / CLIENT
# ─────────────────────────────────────────────────────────────
try:
    api_key = st.secrets.get("GROQ_API_KEY")
except Exception:
    api_key = None
api_key = api_key or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key nahi mili. Streamlit Cloud ke **Secrets** me `GROQ_API_KEY` add karein.")
    st.stop()


@st.cache_resource
def get_client(key: str):
    return Groq(api_key=key)


client = get_client(api_key)


def _secret(name):
    try:
        v = st.secrets.get(name)
    except Exception:
        v = None
    return v or os.getenv(name)


SB_URL, SB_KEY = _secret("SUPABASE_URL"), _secret("SUPABASE_ANON_KEY")
AUTH_CONFIGURED = bool(SB_URL and SB_KEY)
AUTH_ENABLED = AUTH_CONFIGURED and create_client is not None

MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_CHARS = 24000
MAX_IMG_BYTES = 3 * 1024 * 1024
MAX_RAW_IMG_BYTES = 15 * 1024 * 1024
MAX_TOTAL_Q = 200
XP_BASE = {1: 10, 2: 15, 3: 20}
LEVEL_NAME = {1: "Easy", 2: "Medium", 3: "Hard"}
DIFF_LEVEL = {"Easy": 1, "Medium": 2, "Hard": 3}
LIVES = 3

TYPE_MAP = {
    "Multiple Choice": "mcq",
    "True / False": "tf",
    "Multi-select": "multi",
    "Fill in the blank": "blank",
    "Short answer (AI check)": "short",
    "Numerical value": "num",
}
TYPE_ALIASES = {
    "mcq": "mcq", "multiple choice": "mcq", "multiple_choice": "mcq",
    "tf": "tf", "true/false": "tf", "true_false": "tf", "true / false": "tf", "truefalse": "tf",
    "multi": "multi", "multi-select": "multi", "multiselect": "multi", "multi_select": "multi",
    "blank": "blank", "fill": "blank", "fill in the blank": "blank", "fill_in_the_blank": "blank",
    "short": "short", "short answer": "short", "short_answer": "short",
    "num": "num", "numerical": "num", "numeric": "num", "numerical value": "num", "integer": "num", "nvq": "num",
}
TYPE_SPECS = {
    "mcq": '{"type":"mcq","question":"...","options":["A","B","C","D"],"answer":"<exact text of the correct option>"}',
    "tf": '{"type":"tf","question":"<a statement>","options":["True","False"],"answer":"True"}',
    "multi": '{"type":"multi","question":"... (select all that apply)","options":["..","..","..","..",".."],"answers":["<exact option>","<exact option>"]}',
    "blank": '{"type":"blank","question":"A sentence with ____ in place of the missing word","answer":"missing word or phrase","accept":["acceptable alternative"]}',
    "short": '{"type":"short","question":"open question answerable in 1-3 sentences","answer":"model answer in 1-2 sentences"}',
    "num": '{"type":"num","question":"a problem whose final answer is a single number","answer":"<number only, no units>"}',
}

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
def fresh_run_state():
    return {
        "quiz": [], "idx": 0, "answers": {}, "locked": {}, "hints_used": {}, "times": {}, "timed_out": {},
        "grades": {}, "cur_level": 2, "quiz_time_up": False, "elapsed_before": 0.0, "result": None, "study_plan": "", "celebrated": False,
        "start_time": None, "end_time": None,
    }


GLOBAL_DEFAULTS = {
    "stage": "setup", "app_lang": "Hinglish", "quiz_id": 0, "history": [], "meta": {}, "total_xp": 0, "bookmarks": {}, "deep": {},
    "flash_cards": [], "flash_i": 0, "flash_show": False, "flash_return": "setup",
    "q_key": None, "q_start": time.time(), "_picked": "",
    "pyq_uploaded": [], "doubt_thread": [], "doubt_pending": False, "doubt_opts": {},
    "user": None, "sb": None, "tokens": {}, "is_admin": False, "seen_local": {}, "bank_cache": {}, "otp": {},
}
for _k, _v in {**GLOBAL_DEFAULTS, **fresh_run_state()}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────────────────────
def esc(s) -> str:
    return html.escape(str(s))


def fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60}m {seconds % 60:02d}s"


def level_of(xp):
    return xp // 100 + 1


def friendly_error(e: Exception) -> str:
    msg = str(e)
    low = msg.lower()
    if ("rate" in low and "limit" in low) or "429" in low:
        return "Groq ki rate limit lag gayi. 20-30 second ruk kar dobara try karo, ya chhota model chuno."
    if "api key" in low or "401" in low or "invalid_api_key" in low:
        return "API key galat lag rahi hai. Secrets me `GROQ_API_KEY` check karo."
    if "model" in low and ("not found" in low or "decommissioned" in low or "does not exist" in low):
        return "Ye model abhi available nahi hai. Sidebar → Advanced me doosra model chuno."
    return f"Error: {msg}"


def llm(messages, model, json_mode=False, temperature=0.6):
    kwargs = dict(model=model, messages=messages, temperature=temperature)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if model.startswith("openai/gpt-oss"):
        kwargs["extra_body"] = {"reasoning_effort": "low"}
    r = client.chat.completions.create(**kwargs)
    return r.choices[0].message.content or ""


def llm_stream(messages, model, temperature=0.5):
    kwargs = dict(model=model, messages=messages, temperature=temperature, stream=True)
    if model.startswith("openai/gpt-oss"):
        kwargs["extra_body"] = {"reasoning_effort": "low"}
    for chunk in client.chat.completions.create(**kwargs):
        try:
            piece = chunk.choices[0].delta.content
        except Exception:
            piece = None
        if piece:
            yield piece


def clean_json(raw: str):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    if isinstance(data, dict):
        if isinstance(data.get("questions"), list):
            return data["questions"]
        for v in data.values():
            if isinstance(v, list):
                return v
    return data


# ─────────────────────────────────────────────────────────────
# QUESTION MODEL: validation, answers, scoring
# ─────────────────────────────────────────────────────────────
def to_number(s):
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("−", "-")
    pat = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
    m = re.fullmatch(pat, t) or re.search(pat, t)
    try:
        return float(m.group()) if m else None
    except Exception:
        return None


def fmt_num(v):
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.6g}"


def prepare_image(data, mime="image/jpeg", max_side=1600):
    try:
        from PIL import Image, ImageOps

        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return data, mime


def norm_text(s) -> str:
    s = re.sub(r"[^\w\s]", "", str(s).casefold())
    return " ".join(s.split())


def blank_match(answer, q) -> bool:
    na = norm_text(answer)
    if not na:
        return False
    for cand in [q.get("answer", "")] + list(q.get("accept", [])):
        nc = norm_text(cand)
        if nc and (na == nc or difflib.SequenceMatcher(None, na, nc).ratio() >= 0.86):
            return True
    return False


def resolve_option(val, options):
    val = str(val).strip()
    if val in options:
        return val
    letters = "ABCDEFGH"
    if len(val) == 1 and val.upper() in letters[: len(options)]:
        return options[letters.index(val.upper())]
    m = [o for o in options if o.lower() == val.lower()]
    return m[0] if m else None


def validate_and_shuffle(items, default_level=2, adaptive=False):
    good = []
    if not isinstance(items, list):
        return good
    for q in items:
        try:
            if not isinstance(q, dict):
                continue
            t = TYPE_ALIASES.get(str(q.get("type", "mcq")).lower().strip(), "mcq")
            question = str(q["question"]).strip()
            if not question:
                continue
            item = {
                "type": t,
                "question": question,
                "options": [],
                "answer": "",
                "answers": [],
                "accept": [],
                "explanation": str(q.get("explanation", "")).strip() or "Explanation available nahi hai.",
                "hint": str(q.get("hint", "")).strip(),
                "topic": (str(q.get("topic", "General")).strip()[:30] or "General"),
                "level": default_level,
            }
            if adaptive:
                try:
                    item["level"] = min(3, max(1, int(q.get("level", 2))))
                except Exception:
                    item["level"] = 2

            if t in ("mcq", "tf", "multi"):
                options = [str(o).strip() for o in q["options"]]
                if len(options) < 2:
                    continue
                if t == "multi":
                    raw = q.get("answers") or ([q["answer"]] if "answer" in q else [])
                    if isinstance(raw, str):
                        raw = [raw]
                    ans = [resolve_option(a, options) for a in raw]
                    ans = [a for a in dict.fromkeys(ans) if a]
                    if not ans:
                        continue
                    if len(ans) == 1:
                        t, item["type"], item["answer"] = "mcq", "mcq", ans[0]
                    else:
                        item["answers"] = ans
                else:
                    a = resolve_option(q["answer"], options)
                    if a is None:
                        continue
                    item["answer"] = a
                    if {o.lower() for o in options} == {"true", "false"}:
                        t, item["type"] = "tf", "tf"
                if t != "tf":
                    random.shuffle(options)
                item["options"] = options
            elif t == "num":
                val = to_number(q.get("answer"))
                if val is None:
                    continue
                item["answer"] = fmt_num(val)
                try:
                    tol = float(q.get("tolerance", 0) or 0)
                except Exception:
                    tol = 0.0
                item["tol"] = tol if tol > 0 else (0.0 if abs(val - round(val)) < 1e-9 else 0.011)
            elif t == "blank":
                ans = str(q["answer"]).strip()
                if not ans or "__" not in question:
                    continue
                accept = q.get("accept") or []
                if isinstance(accept, str):
                    accept = [accept]
                item["answer"] = ans
                item["accept"] = [str(a).strip() for a in accept if str(a).strip()]
            else:  # short
                ans = str(q["answer"]).strip()
                if not ans:
                    continue
                item["answer"] = ans
            good.append(item)
        except Exception:
            continue
    return good


def is_skipped(i) -> bool:
    return st.session_state.answers.get(i) in (None, "", [])


def is_correct(i) -> bool:
    ss = st.session_state
    q, a = ss.quiz[i], ss.answers.get(i)
    if a in (None, "", []):
        return False
    t = q["type"]
    if t in ("mcq", "tf"):
        return a == q["answer"]
    if t == "multi":
        return set(a) == set(q["answers"])
    if t == "num":
        ua, ca = to_number(a), to_number(q["answer"])
        return ua is not None and ca is not None and abs(ua - ca) <= q.get("tol", 0.0) + 1e-9
    if t == "blank":
        return blank_match(a, q)
    return ss.grades.get(i, {}).get("score", 0) >= 0.6


def correct_text(q) -> str:
    return " · ".join(q["answers"]) if q["type"] == "multi" else q["answer"]


def user_text(i) -> str:
    a = st.session_state.answers.get(i)
    if a in (None, "", []):
        return "—"
    return " | ".join(a) if isinstance(a, list) else str(a)


def norm_answer(a):
    if isinstance(a, str):
        a = a.strip()
    return None if a in (None, "", []) else a


def has_answer(a) -> bool:
    return norm_answer(a) is not None


def reshuffle(q):
    q = dict(q)
    if q["type"] in ("mcq", "multi"):
        opts = list(q["options"])
        random.shuffle(opts)
        q["options"] = opts
    return q


def speech_text(q) -> str:
    t = q["question"].replace("____", "blank").replace("___", "blank")
    if q["type"] in ("mcq", "multi"):
        t += ". " + " ".join(f"Option {n + 1}. {o}." for n, o in enumerate(q["options"]))
    elif q["type"] == "tf":
        t += ". True ya False?"
    return t


# ─────────────────────────────────────────────────────────────
# AI GENERATION
# ─────────────────────────────────────────────────────────────
def generate_quiz(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, exam=None):
    type_keys = [t for t in type_keys if t in TYPE_SPECS] or ["mcq"]
    shapes = "\n".join(f"- {t}: {TYPE_SPECS[t]}" for t in type_keys)
    level_rule = (
        '- Give each question a numeric "level": 1 (easy), 2 (medium) or 3 (hard), roughly a third each.'
        if adaptive
        else f'- Every question has "level": {DIFF_LEVEL[diff]}. Overall difficulty: {diff}.'
    )
    avoid_rule = ""
    if avoid:
        avoid_rule = "- Do NOT repeat or rephrase these earlier questions:\n  " + "\n  ".join(f"* {a}" for a in avoid[-40:])
    exam_rule = (
        f"- Write in the style, difficulty and syllabus of {exam} previous-year papers. "
        "Do NOT claim any question is from a real past paper and do NOT invent exam years."
        if exam
        else ""
    )
    content_block = (
        "Use the attached image as the content. Read it carefully, including handwriting if present."
        if media
        else f'Content:\n"""\n{text[:MAX_CHARS]}\n"""'
    )

    prompt = f"""You are an expert teacher and quiz designer.
Create exactly {num_q} quiz questions from the content below.

Allowed question types and their JSON shapes (spread the questions roughly evenly across them):
{shapes}

Every question object must ALSO contain: "explanation", "hint", "topic".

Rules:
{level_rule}
- Write questions, options, hints and explanations in: {lang}.
- Exactly one correct option for mcq/tf; multi needs 2-3 correct options out of 5.
- Distractors must be plausible. Avoid "All of the above".
- Cover different parts of the content; no duplicate questions.
- "hint": a short nudge WITHOUT revealing the answer.
- "explanation": 1-2 short sentences why the answer is correct.
- "topic": a 1-3 word sub-topic label.
{avoid_rule}
{exam_rule}
- Prefer fresh sub-topics and angles every time (variation seed {random.randint(1000, 9999)}).

Return ONLY a JSON object: {{"questions": [ ...question objects... ]}}

{content_block}
"""
    system = {"role": "system", "content": "You are a JSON generator. Respond only with valid JSON."}
    if media:
        b64 = base64.b64encode(media["bytes"]).decode()
        user = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{media['mime']};base64,{b64}"}},
            ],
        }
        model = VISION_MODEL
    else:
        user = {"role": "user", "content": prompt}

    last_err = None
    for attempt in range(2):
        try:
            raw = llm([system, user], model, json_mode=True, temperature=0.6 + 0.2 * attempt)
            quiz = validate_and_shuffle(clean_json(raw), DIFF_LEVEL[diff], adaptive)
            if quiz:
                return quiz
        except json.JSONDecodeError as e:
            last_err = e
    if last_err:
        raise last_err
    return []


def generate_quiz_batched(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, progress=None, exam=None):
    quiz = []
    avoid_list = list(avoid or [])
    seen_h = {qhash(a) for a in avoid_list}
    seen_n = [norm_text(a) for a in avoid_list]
    attempts, max_attempts = 0, num_q // 5 + 5
    while len(quiz) < num_q and attempts < max_attempts:
        attempts += 1
        n = min(10, num_q - len(quiz))
        try:
            batch = generate_quiz(text, n, diff, type_keys, lang, model, media=media, avoid=avoid_list, adaptive=adaptive, exam=exam)
        except Exception:
            if quiz:
                break
            raise
        for b in batch:
            if not is_duplicate(b["question"], seen_h, seen_n):
                seen_h.add(qhash(b["question"]))
                seen_n.append(norm_text(b["question"]))
                quiz.append(b)
        avoid_list += [b["question"] for b in batch]
        if progress:
            progress(min(len(quiz) / num_q, 1.0), f"{min(len(quiz), num_q)} / {num_q} questions generated…")
    return quiz[:num_q]


def generate_with_progress(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, exam=None):
    bar = st.progress(0.0, text="Generating questions…")

    def cb(frac, msg):
        bar.progress(min(max(frac, 0.0), 1.0), text=msg)

    try:
        return generate_quiz_batched(text, num_q, diff, type_keys, lang, model, media, avoid, adaptive, progress=cb, exam=exam)
    finally:
        bar.empty()


def grade_short(i):
    ss = st.session_state
    if i in ss.grades:
        return ss.grades[i]
    q, a = ss.quiz[i], (ss.answers.get(i) or "")
    if not str(a).strip():
        g = {"score": 0.0, "feedback": "Koi answer nahi likha."}
    else:
        prompt = f"""Grade a student's short answer. Language for feedback: {ss.meta.get('language', 'English')}.
Question: {q['question']}
Model answer: {q['answer']}
Student answer: {a}

Be fair: accept correct ideas worded differently. Return ONLY JSON:
{{"score": <number 0 to 1>, "feedback": "<one or two sentences: what was good, what was missing>"}}"""
        try:
            raw = llm([{"role": "user", "content": prompt}], ss.meta.get("model", MODELS[0]), json_mode=True, temperature=0.2)
            d = json.loads(raw)
            g = {"score": min(1.0, max(0.0, float(d.get("score", 0)))), "feedback": str(d.get("feedback", "")).strip()}
        except Exception:
            g = {"score": 0.0, "feedback": "AI grading nahi ho paya — sahi answer se khud compare karo."}
    ss.grades[i] = g
    return g


def explain_more(q, user_ans, lang, model):
    key = q["question"]
    if key in st.session_state.deep:
        return st.session_state.deep[key]
    prompt = f"""Explain this quiz question in more depth for a student. Language: {lang}.
Question: {q['question']}
Options: {q['options'] or 'n/a'}
Correct answer: {correct_text(q)}
Student's answer: {user_ans or 'skipped'}
Give: (1) why the correct answer is right, (2) why the student's choice (if wrong) is tempting but wrong,
(3) one simple real-life example or memory trick. Under 150 words, short bullet points."""
    text = llm([{"role": "user", "content": prompt}], model)
    st.session_state.deep[key] = text
    return text


def make_study_plan(wrong_qs, lang, model):
    items = "\n".join(f"- [{q['topic']}] {q['question']} (correct: {correct_text(q)})" for q in wrong_qs)
    prompt = f"""A student got these quiz questions wrong or skipped them. Language: {lang}.
{items}

Write a compact revision plan in markdown:
1. **Weak areas** - 2-4 bullets naming concepts to revise.
2. **Quick notes** - key facts to remember, short bullets.
3. **Next steps** - 3 concrete practice tips.
Under 220 words."""
    return llm([{"role": "user", "content": prompt}], model)


# ─────────────────────────────────────────────────────────────
# DATABASE AND STORAGE HELPERS
# ─────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def qhash(text) -> str:
    return hashlib.sha1(norm_text(text).encode("utf-8")).hexdigest()[:16]


def topic_key_for(kind, label) -> str:
    return f"{kind}::{norm_text(label)[:80]}"


def is_duplicate(question, seen_hashes, seen_norms):
    if qhash(question) in seen_hashes:
        return True
    n = norm_text(question)
    return any(difflib.SequenceMatcher(None, n, x).ratio() >= 0.88 for x in seen_norms[-120:])


def db_on() -> bool:
    ss = st.session_state
    return bool(AUTH_ENABLED and ss.get("user") and ss.get("sb"))


def db_uid():
    return st.session_state["user"]["id"]


def db_try(fn, default=None):
    try:
        return fn()
    except Exception as e:
        st.session_state["_db_err"] = str(e)[:200]
        return default


def fetch_all(make_query, page=1000, cap=20000):
    rows = []
    for start in range(0, cap, page):
        data = make_query().range(start, start + page - 1).execute().data or []
        rows += data
        if len(data) < page:
            break
    return rows


def _local_time(iso):
    try:
        from zoneinfo import ZoneInfo
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d %b, %H:%M")
    except Exception:
        return str(iso)[:16].replace("T", " ")


def db_load_user_data():
    ss = st.session_state
    sb, uid = ss["sb"], db_uid()
    prof = db_try(lambda: sb.table("profiles").select("xp").eq("user_id", uid).execute().data, [])
    if prof:
        ss.total_xp = int(prof[0].get("xp") or 0)
    else:
        ss.total_xp = 0
        db_try(lambda: sb.table("profiles").upsert({"user_id": uid, "xp": 0}).execute())
    rows = db_try(lambda: sb.table("quiz_history").select("*").eq("user_id", uid).order("created_at", desc=True).limit(200).execute().data, []) or []
    hist = []
    for r in reversed(rows):
        try:
            hist.append(
                {
                    "id": r["id"], "time": _local_time(r.get("created_at", "")), "topic": r.get("topic") or "Quiz",
                    "difficulty": r.get("difficulty") or "-", "score": int(r.get("score") or 0), "total": max(1, int(r.get("total") or 1)),
                    "marks": float(r.get("marks") or 0), "max": float(r.get("max_marks") or 0),
                    "acc": int(r.get("accuracy") or 0), "pct": int(r.get("pct") or 0),
                }
            )
        except Exception:
            continue
    ss.history = hist
    bms = db_try(lambda: sb.table("bookmarks").select("data").eq("user_id", uid).execute().data, []) or []
    ss.bookmarks = {b["data"]["question"]: b["data"] for b in bms if isinstance(b.get("data"), dict) and b["data"].get("question")}
    ss.is_admin = bool(db_try(lambda: sb.table("admins").select("user_id").eq("user_id", uid).execute().data, []))


def db_save_result(entry):
    if not db_on():
        return None
    ss, uid = st.session_state, db_uid()
    row = {
        "user_id": uid, "topic": entry["topic"], "difficulty": entry["difficulty"], "score": entry["score"], "total": entry["total"],
        "marks": entry["marks"], "max_marks": entry["max"], "accuracy": entry["acc"], "pct": entry["pct"],
    }
    res = db_try(lambda: ss["sb"].table("quiz_history").insert(row).execute().data)
    db_try(lambda: ss["sb"].table("profiles").upsert({"user_id": uid, "xp": ss.total_xp, "updated_at": datetime.now(timezone.utc).isoformat()}).execute())
    return res[0]["id"] if res else None


def db_undo_result(hist_id):
    if not db_on():
        return
    ss, uid = st.session_state, db_uid()
    if hist_id:
        db_try(lambda: ss["sb"].table("quiz_history").delete().eq("id", hist_id).eq("user_id", uid).execute())
    db_try(lambda: ss["sb"].table("profiles").upsert({"user_id": uid, "xp": ss.total_xp, "updated_at": datetime.now(timezone.utc).isoformat()}).execute())


def db_clear_history():
    if db_on():
        ss, uid = st.session_state, db_uid()
        db_try(lambda: ss["sb"].table("quiz_history").delete().eq("user_id", uid).execute())


def db_sync_bookmark(q, added):
    if not db_on():
        return
    ss, uid = st.session_state, db_uid()
    h = qhash(q["question"])
    if added:
        db_try(lambda: ss["sb"].table("bookmarks").upsert({"user_id": uid, "qhash": h, "data": q}, on_conflict="user_id,qhash").execute())
    else:
        db_try(lambda: ss["sb"].table("bookmarks").delete().eq("user_id", uid).eq("qhash", h).execute())


def get_seen_questions(tkey, limit=80):
    ss = st.session_state
    if not tkey:
        return []
    if db_on():
        uid = db_uid()
        rows = db_try(
            lambda: ss["sb"].table("seen_questions").select("question").eq("user_id", uid).eq("topic_key", tkey)
            .order("created_at", desc=True).limit(limit).execute().data, [],
        ) or []
        return [r["question"] for r in rows if r.get("question")]
    return list(reversed(ss.seen_local.get(tkey, [])))[:limit]


def get_seen_hashes(tkey):
    ss = st.session_state
    if not tkey:
        return set()
    if db_on():
        uid = db_uid()
        rows = db_try(lambda: fetch_all(lambda: ss["sb"].table("seen_questions").select("qhash").eq("user_id", uid).eq("topic_key", tkey)), []) or []
        return {r["qhash"] for r in rows}
    return {qhash(x) for x in ss.seen_local.get(tkey, [])}


def mark_seen(tkey, quiz):
    ss = st.session_state
    if not tkey or not quiz:
        return
    items = {qhash(q["question"]): q["question"] for q in quiz}
    if db_on():
        uid = db_uid()
        rows = [{"user_id": uid, "topic_key": tkey, "qhash": h, "question": t[:400]} for h, t in items.items()]
        db_try(lambda: ss["sb"].table("seen_questions").upsert(rows, on_conflict="user_id,topic_key,qhash", ignore_duplicates=True).execute())
    else:
        lst = ss.seen_local.setdefault(tkey, [])
        have = {qhash(x) for x in lst}
        lst += [t for h, t in items.items() if h not in have]
        del lst[:-500]


def reset_seen(tkey):
    ss = st.session_state
    if db_on():
        uid = db_uid()
        db_try(lambda: ss["sb"].table("seen_questions").delete().eq("user_id", uid).eq("topic_key", tkey).execute())
    else:
        ss.seen_local.pop(tkey, None)


def bank_hash(x):
    return qhash(f"{x['exam']}|{x['question']}")


def db_load_bank(exam):
    ss = st.session_state
    if not db_on():
        return []
    cached = ss.bank_cache.get(exam)
    if cached and time.time() - cached[0] < 600:
        return cached[1]
    rows = db_try(lambda: fetch_all(lambda: ss["sb"].table("pyq_bank").select("*").eq("exam", exam)), []) or []
    items = normalize_pyq(
        [
            {
                "exam": r.get("exam"), "subject": r.get("subject") or "General", "year": r.get("year") or "", "type": r.get("qtype") or "mcq",
                "question": r.get("question"), "options": r.get("options") or [], "answer": r.get("answer"),
                "explanation": r.get("explanation") or "", "tolerance": r.get("tolerance") or 0,
            }
            for r in rows
        ]
    )
    ss.bank_cache[exam] = (time.time(), items)
    return items


def db_save_bank(items):
    ss = st.session_state
    rows = [
        {
            "qhash": bank_hash(x), "exam": x["exam"], "subject": x["subject"], "year": x["year"], "qtype": x.get("type", "mcq"),
            "question": x["question"], "options": x.get("options") or [], "answer": x["answer"],
            "explanation": x.get("explanation") or "", "tolerance": x.get("tol") or 0,
        }
        for x in items
    ]
    for i in range(0, len(rows), 500):
        ss["sb"].table("pyq_bank").upsert(rows[i : i + 500], on_conflict="qhash", ignore_duplicates=True).execute()
    ss.bank_cache = {}
    return len(rows)


def normalize_phone(s):
    d = re.sub(r"[^\d+]", "", s or "")
    if d.startswith("+"):
        digits = d[1:]
        return "+" + digits if digits.isdigit() and 10 <= len(digits) <= 15 else None
    d = d.lstrip("0")
    if d.startswith("91") and len(d) == 12:
        return "+" + d
    if len(d) == 10 and d.isdigit():
        return "+91" + d
    return None


def mask_ident(ident):
    if "@" in ident:
        name, dom = ident.split("@", 1)
        return name[:1] + "***@" + dom
    return ident[:3] + "*" * max(len(ident) - 7, 2) + ident[-4:]


def auth_friendly(e, channel, verifying=False):
    msg = str(e)
    low = msg.lower()
    if channel == "phone" and any(k in low for k in ("provider", "sms", "twilio", "unsupported phone")):
        return "Phone OTP ke liye Supabase me SMS provider setup hona chahiye. Email se login karein."
    if any(k in low for k in ("rate limit", "too many", "after", "seconds")) and not verifying:
        return "Bahut jaldi OTP maanga. Thodi der baad try karein."
    if verifying and any(k in low for k in ("expired", "invalid", "token", "otp")):
        return "OTP galat hai ya expire ho gaya hai."
    return f"Error: {msg}"


def sb_client():
    ss = st.session_state
    if ss.get("sb") is None:
        ss["sb"] = create_client(SB_URL, SB_KEY)
    return ss["sb"]


def otp_send(channel, ident):
    payload = {"email": ident} if channel == "email" else {"phone": ident}
    payload["options"] = {"should_create_user": True}
    sb_client().auth.sign_in_with_otp(payload)


def otp_verify(channel, ident, code):
    sb = sb_client()
    last = None
    for kind in (("email", "signup", "magiclink") if channel == "email" else ("sms",)):
        try:
            payload = {"token": code, "type": kind, ("email" if channel == "email" else "phone"): ident}
            res = sb.auth.verify_otp(payload)
            if res and res.session and res.user:
                return res
        except Exception as e:
            last = e
    raise last or ValueError("OTP galat hai.")


def remember_login(cm, refresh_token):
    if cm is None or not refresh_token:
        return
    try:
        cm.set("qa_rt", refresh_token, expires_at=datetime.now() + timedelta(days=30), key=f"set_rt_{int(time.time() * 1000)}")
    except Exception:
        pass


def complete_login(session, user, cm):
    ss = st.session_state
    ss["user"] = {"id": str(user.id), "email": getattr(user, "email", "") or "", "phone": getattr(user, "phone", "") or ""}
    ss["tokens"] = {"refresh": session.refresh_token, "access": session.access_token, "exp": float(session.expires_at or (time.time() + 3000))}
    try:
        ss["sb"].postgrest.auth(session.access_token)
    except Exception:
        pass
    ss["_just_logged_out"] = False
    remember_login(cm, session.refresh_token)
    db_load_user_data()


def do_logout(cm=None, rerun=True):
    ss = st.session_state
    try:
        ss["sb"].auth.sign_out({"scope": "local"})
    except Exception:
        pass
    if cm is not None:
        try:
            cm.delete("qa_rt", key=f"del_rt_{int(time.time() * 1000)}")
            time.sleep(0.6)
        except Exception:
            pass
    ss.clear()
    ss["_just_logged_out"] = True
    if rerun:
        st.rerun()


def ensure_fresh_token(cm):
    ss = st.session_state
    tk = ss.get("tokens") or {}
    if time.time() < tk.get("exp", 0) - 90:
        return
    try:
        res = ss["sb"].auth.refresh_session(tk["refresh"])
        sess = res.session
        ss["tokens"] = {"refresh": sess.refresh_token, "access": sess.access_token, "exp": float(sess.expires_at or (time.time() + 3000))}
        try:
            ss["sb"].postgrest.auth(sess.access_token)
        except Exception:
            pass
        remember_login(cm, sess.refresh_token)
    except Exception:
        do_logout(cm, rerun=False)


def try_cookie_login(cm):
    ss = st.session_state
    if cm is None or ss.get("_just_logged_out") or ss.get("_cookie_tried"):
        return
    rt = cm.get("qa_rt")
    if not rt:
        return
    ss["_cookie_tried"] = True
    try:
        res = sb_client().auth.refresh_session(rt)
        complete_login(res.session, res.user, cm)
    except Exception:
        try:
            cm.delete("qa_rt", key="del_bad_rt")
        except Exception:
            pass


def render_login(cm):
    ss = st.session_state
    st.markdown(
        f"""<div class="qf-hero"><div class="qf-title qf-display">{APP_NAME}</div>
<div class="qf-sub">Login karo — tumhari history, XP aur saved sawal hamesha safe rahenge.</div></div>""",
        unsafe_allow_html=True,
    )
    otp = ss.get("otp") or {}
    with st.container(key="panel_login"):
        if not otp:
            ch = st.radio("Login Method", ["📧 Email", "📱 Mobile"], horizontal=True, key="login_ch")
            is_email = ch.startswith("📧")
            raw = st.text_input("Email / Mobile", key="login_id_input", placeholder="you@example.com" if is_email else "9876543210")
            if st.button("📨 Send OTP", type="primary", use_container_width=True, key="otp_send_btn"):
                ident = (raw or "").strip().lower() if is_email else normalize_phone(raw)
                if (is_email and not EMAIL_RE.match(ident or "")) or (not is_email and not ident):
                    st.error("Valid Details enter karein.")
                else:
                    channel = "email" if is_email else "phone"
                    with st.spinner("OTP bhej rahe hain..."):
                        try:
                            otp_send(channel, ident)
                            ss["otp"] = {"channel": channel, "ident": ident, "sent": time.time()}
                            st.rerun()
                        except Exception as e:
                            st.error(auth_friendly(e, channel))
            return False

        st.success(f"OTP Sent to: **{mask_ident(otp['ident'])}**")
        code = st.text_input("Enter OTP", max_chars=10, key="otp_code")
        c1, c2 = st.columns(2)
        if c1.button("✅ Verify", type="primary", use_container_width=True, key="otp_verify_btn"):
            token = re.sub(r"\s", "", code or "")
            if token:
                with st.spinner("Verifying..."):
                    try:
                        res = otp_verify(otp["channel"], otp["ident"], token)
                        complete_login(res.session, res.user, cm)
                        ss["otp"] = {}
                        return True
                    except Exception as e:
                        st.error(auth_friendly(e, otp["channel"], verifying=True))
        if c2.button("← Change", key="otp_back"):
            ss["otp"] = {}
            st.rerun()
    return False


def ensure_auth():
    ss = st.session_state
    if not AUTH_CONFIGURED:
        return None
    if create_client is None:
        st.error("Supabase module missing.")
        st.stop()
    cm = None
    if stx is not None:
        try:
            cm = stx.CookieManager(key="qa_cm")
        except Exception:
            cm = None
    if ss.get("user"):
        ensure_fresh_token(cm)
        if ss.get("user"):
            return cm
    try_cookie_login(cm)
    if ss.get("user"):
        return cm
    box = st.empty()
    with box.container():
        logged_in = render_login(cm)
    if not logged_in:
        st.stop()
    box.empty()
    return cm


# ─────────────────────────────────────────────────────────────
# QUIZ FLOW HELPERS
# ─────────────────────────────────────────────────────────────
def start_quiz(quiz, meta):
    st.session_state.update(fresh_run_state())
    st.session_state.update(
        quiz=quiz, quiz_id=st.session_state.quiz_id + 1, start_time=time.time(), stage="quiz", meta=meta, q_key=None
    )
    mark_seen(meta.get("tkey"), quiz)


def record_time(i):
    if i not in st.session_state.times:
        st.session_state.times[i] = time.time() - st.session_state.q_start


def queue_sound(name):
    st.session_state["sound"] = name


def lives_left():
    ss = st.session_state
    lost = sum(1 for j in ss.locked if not is_correct(j))
    return max(LIVES - lost, 0)


def advance(i):
    ss = st.session_state
    q = ss.quiz[i]
    if ss.meta.get("adaptive"):
        if q["type"] != "short" or i in ss.grades:
            if is_correct(i):
                ss.cur_level = min(3, ss.cur_level + 1)
            elif not is_skipped(i):
                ss.cur_level = max(1, ss.cur_level - 1)
        rest = list(range(i + 1, len(ss.quiz)))
        if rest:
            best = min(rest, key=lambda j: (abs(ss.quiz[j]["level"] - ss.cur_level), random.random()))
            ss.quiz[i + 1], ss.quiz[best] = ss.quiz[best], ss.quiz[i + 1]
    ss.idx += 1


def fmt_marks(x):
    return f"{round(float(x), 2):g}"


def question_marks(i):
    ss = st.session_state
    q = ss.quiz[i]
    m = ss.meta.get("marks", 1.0)
    pen = 0.0 if q["type"] in ss.meta.get("no_neg_types", []) else m * ss.meta.get("neg", 0.0)
    if is_skipped(i):
        return 0.0
    if q["type"] == "short":
        return round(m * ss.grades.get(i, {}).get("score", 0.0), 2)
    return m if is_correct(i) else (-pen if pen else 0.0)


def compute_badges(pct, best_streak, avg_time, hints, diff, survival_win, n_types, perfect):
    badges = []
    if perfect:
        badges.append("💎 Perfect Score")
    if best_streak >= 5:
        badges.append("🔥 Streak Master")
    if avg_time and avg_time < 8 and pct >= 70:
        badges.append("⚡ Speedster")
    if hints == 0 and pct >= 80:
        badges.append("🧘 No Hints Needed")
    if diff == "Hard" and pct >= 80:
        badges.append("🦾 Hard Mode Hero")
    if survival_win:
        badges.append("🛡️ Survivor")
    if n_types >= 3 and pct >= 70:
        badges.append("🧩 All-rounder")
    if len(st.session_state.history) >= 3:
        badges.append("📚 Regular Learner")
    return badges


def finish_quiz():
    ss = st.session_state
    ss.end_time = time.time()
    quiz = ss.quiz
    diff = ss.meta.get("difficulty", "Medium")

    pending = [i for i, q in enumerate(quiz) if q["type"] == "short" and not is_skipped(i) and i not in ss.grades]
    if pending:
        with st.spinner("Short answers check ho rahe hain…"):
            for i in pending:
                grade_short(i)

    xp = streak = best = correct = 0
    for i, q in enumerate(quiz):
        if is_correct(i):
            correct += 1
            streak += 1
            best = max(best, streak)
            pts = XP_BASE.get(q.get("level", 2), 15)
            if ss.hints_used.get(i):
                pts = max(pts - 5, 5)
            if streak >= 3:
                pts += min(streak - 2, 5) * 2
            xp += pts
        else:
            streak = 0

    total = len(quiz)
    per_q = [question_marks(i) for i in range(total)]
    marks = round(sum(per_q), 2)
    max_marks = round(total * ss.meta.get("marks", 1.0), 2)
    neg_lost = round(-sum(x for x in per_q if x < 0), 2)
    attempted = sum(1 for i in range(total) if not is_skipped(i))
    accuracy = round(correct / attempted * 100) if attempted else 0
    pct = max(0, round(marks / max_marks * 100)) if max_marks else 0
    avg_time = sum(ss.times.values()) / len(ss.times) if ss.times else 0
    hints = sum(1 for v in ss.hints_used.values() if v)
    survival_win = ss.meta.get("mode") == "Survival" and len(ss.locked) == total and lives_left() > 0
    n_types = len({q["type"] for q in quiz})

    old_level = level_of(ss.total_xp)
    ss.total_xp += xp
    entry = {
        "time": datetime.now().strftime("%d %b, %H:%M"), "topic": ss.meta.get("label", "Quiz"), "difficulty": diff,
        "score": correct, "total": total, "marks": marks, "max": max_marks, "acc": accuracy, "pct": pct,
    }
    entry["id"] = db_save_result(entry)
    ss.history.append(entry)
    ss.result = {
        "score": correct, "total": total, "pct": pct, "xp": xp, "best_streak": best, "avg_time": avg_time, "hints": hints,
        "marks": marks, "max_marks": max_marks, "neg_lost": neg_lost, "attempted": attempted, "accuracy": accuracy,
        "time_up": ss.quiz_time_up,
        "leveled_up": level_of(ss.total_xp) > old_level,
        "badges": compute_badges(pct, best, avg_time, hints, diff, survival_win, n_types, correct == total),
    }
    queue_sound("win" if pct >= 50 else "lose")
    ss.stage = "result"


# ─────────────────────────────────────────────────────────────
# EXAM CONFIGS & UTILS
# ─────────────────────────────────────────────────────────────
PYQ_FILE = "pyq_data.json"
EXAM_CONFIG = {
    "SSC CGL": {
        "marks": 2.0, "neg": 0.25, "minutes": 60,
        "sections": [("Reasoning", {"mcq": 25}), ("General Awareness", {"mcq": 25}), ("Quantitative Aptitude", {"mcq": 25}), ("English Comprehension", {"mcq": 25})],
        "note": "Tier-I: 100 sawal, 60 min, +2 / −0.5.",
    },
    "RRB NTPC": {
        "marks": 1.0, "neg": 1 / 3, "minutes": 90,
        "sections": [("Mathematics", {"mcq": 30}), ("Reasoning", {"mcq": 30}), ("General Awareness", {"mcq": 40})],
        "note": "CBT-1: 100 sawal, 90 min, +1 / −⅓.",
    },
    "Banking (IBPS/SBI)": {
        "marks": 1.0, "neg": 0.25, "minutes": 60,
        "sections": [("English", {"mcq": 30}), ("Quantitative Aptitude", {"mcq": 35}), ("Reasoning", {"mcq": 35})],
        "note": "Prelims: 100 sawal, 60 min, +1 / −¼.",
    },
    "UP Police Constable": {
        "marks": 2.0, "neg": 0.25, "minutes": 120,
        "sections": [("General Knowledge", {"mcq": 38}), ("General Hindi", {"mcq": 37}), ("Numerical Ability", {"mcq": 38}), ("Reasoning", {"mcq": 37})],
        "note": "150 sawal, 120 min, +2 / −0.5.",
    },
    "UPSC / State PCS": {
        "marks": 2.0, "neg": 1 / 3, "minutes": 120,
        "sections": [("History", {"mcq": 17}), ("Polity", {"mcq": 16}), ("Economy", {"mcq": 16}), ("Geography", {"mcq": 15}), ("Environment", {"mcq": 14}), ("Science & Tech", {"mcq": 11}), ("Current Affairs", {"mcq": 11})],
        "note": "GS Paper-I: 100 sawal, 120 min, +2 / −⅓.",
    },
    "UP CNET (Nursing)": {
        "marks": 1.0, "neg": 0.0, "minutes": 140,
        "sections": [("Physics", {"mcq": 24}), ("Chemistry", {"mcq": 24}), ("Biology", {"mcq": 24}), ("English", {"mcq": 24}), ("Nursing Aptitude", {"mcq": 24})],
        "note": "120 sawal, 140 min, no negative marking.",
    },
    "NEET UG": {
        "marks": 4.0, "neg": 0.25, "minutes": 180,
        "sections": [("Physics", {"mcq": 45}), ("Chemistry", {"mcq": 45}), ("Botany", {"mcq": 45}), ("Zoology", {"mcq": 45})],
        "note": "180 sawal, 180 min, +4 / −1.",
    },
    "JEE Main": {
        "marks": 4.0, "neg": 0.25, "minutes": 180,
        "sections": [("Physics", {"mcq": 20, "num": 5}), ("Chemistry", {"mcq": 20, "num": 5}), ("Mathematics", {"mcq": 20, "num": 5})],
        "note": "Paper-1: 75 sawal, 180 min, +4 / −1.",
    },
}
EXAM_LIST = list(EXAM_CONFIG) + ["General All Exams"]
EXAM_SUBJECTS = {k: [name for name, _ in v["sections"]] for k, v in EXAM_CONFIG.items()}
EXAM_SUBJECTS["General All Exams"] = ["Mixed"]
NEG_CHOICES = {"Official": None, "Koi negative nahi": 0.0, "¼": 0.25, "⅓": 1 / 3, "½": 0.5, "Full (−1x)": 1.0}


def normalize_pyq(items):
    out = []
    if not isinstance(items, list):
        return out
    for it in items:
        try:
            question = str(it["question"]).strip()
            if not question:
                continue
            base = {
                "exam": str(it.get("exam", "General All Exams")).strip() or "General All Exams",
                "subject": str(it.get("subject", "General")).strip() or "General",
                "year": str(it.get("year", "")).strip(),
                "question": question,
                "explanation": str(it.get("explanation", "")).strip(),
            }
            if str(it.get("type", "mcq")).lower().strip() in ("num", "numerical", "nvq", "integer"):
                val = to_number(it.get("answer", it.get("correct", "")))
                if val is None:
                    continue
                try:
                    tol = float(it.get("tolerance", 0) or 0)
                except Exception:
                    tol = 0.0
                out.append({**base, "type": "num", "options": [], "answer": fmt_num(val), "tol": tol if tol > 0 else (0.0 if abs(val - round(val)) < 1e-9 else 0.011)})
            else:
                opts = [str(o).strip() for o in it["options"] if str(o).strip()]
                ans = resolve_option(it.get("answer", it.get("correct", "")), opts)
                if len(opts) < 2 or ans is None:
                    continue
                out.append({**base, "type": "mcq", "options": opts, "answer": ans})
        except Exception:
            continue
    return out


@st.cache_data(show_spinner=False)
def _load_pyq_file(path, mtime):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return normalize_pyq(json.load(f))
    except Exception:
        return []


def load_pyq_dataset(exam=None):
    base = _load_pyq_file(PYQ_FILE, os.path.getmtime(PYQ_FILE)) if os.path.exists(PYQ_FILE) else []
    bank = db_load_bank(exam) if exam else []
    out, seen = [], set()
    for x in list(base) + list(bank) + list(st.session_state.get("pyq_uploaded", [])):
        if exam and x["exam"] != exam:
            continue
        h = bank_hash(x)
        if h not in seen:
            seen.add(h)
            out.append(x)
    return out


def parse_pyq_upload(f):
    raw = f.getvalue()
    if f.name.lower().endswith(".json"):
        data = json.loads(raw.decode("utf-8-sig"))
        if isinstance(data, dict):
            data = data.get("questions") or next((v for v in data.values() if isinstance(v, list)), [])
        return normalize_pyq(data)
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [str(c).strip().lower() for c in df.columns]

    def cell(r, k, d=""):
        v = r.get(k, d)
        return d if pd.isna(v) else str(v).strip()

    items = []
    for _, r in df.iterrows():
        opts = [cell(r, c) for c in ("option_a", "option_b", "option_c", "option_d", "option_e") if cell(r, c)]
        if not opts and cell(r, "options"):
            opts = [o.strip() for o in cell(r, "options").split("|")]
        items.append(
            {
                "exam": cell(r, "exam", "General All Exams"), "subject": cell(r, "subject", "General"), "year": cell(r, "year"),
                "type": cell(r, "type", "mcq"), "question": cell(r, "question"), "options": opts, "answer": cell(r, "answer"),
                "tolerance": cell(r, "tolerance", "0"), "explanation": cell(r, "explanation"),
            }
        )
    return normalize_pyq(items)


def pyq_to_item(x):
    kind = x.get("type", "mcq")
    opts = list(x["options"])
    if kind == "mcq":
        random.shuffle(opts)
    return {
        "type": kind, "question": x["question"], "options": opts, "answer": x["answer"], "answers": [], "accept": [],
        "tol": x.get("tol", 0.0),
        "explanation": x.get("explanation") or "Is sawal ka explanation dataset me nahi hai.",
        "hint": "", "topic": (x.get("subject") or "General")[:30],
        "level": 2, "src": f"{x['exam']} {x['year']}".strip(),
    }


def pick_from_pool(pool, n, exclude):
    fresh = [x for x in pool if qhash(x["question"]) not in exclude]
    return [pyq_to_item(x) for x in random.sample(fresh, min(n, len(fresh)))]


def more_questions(n, avoid_texts):
    m = st.session_state.meta
    tkey = m.get("tkey")
    seen_h = set(get_seen_hashes(tkey)) | {qhash(t) for t in avoid_texts}
    pool = m.get("pyq_pool") or []
    got = pick_from_pool(pool, n, seen_h) if pool else []
    need = n - len(got)
    if need > 0 and (not pool or m.get("pyq_fill_ai", False)):
        past = list(avoid_texts) + get_seen_questions(tkey)
        got += generate_with_progress(
            m.get("source", ""), need, m.get("difficulty", "Medium"), m.get("types", ["mcq"]),
            m.get("language", "English"), m.get("model", MODELS[0]), media=m.get("media"),
            avoid=past + [g["question"] for g in got], adaptive=m.get("adaptive", False), exam=m.get("exam"),
        )
    return got


def reset_all():
    st.session_state.update(fresh_run_state())
    st.session_state.stage = "setup"


def read_pdf(file, start_page, end_page):
    reader = PdfReader(file)
    text = ""
    for p in reader.pages[start_page - 1 : end_page]:
        t_p = p.extract_text()
        if t_p:
            text += t_p + "\n"
    return text, len(reader.pages)


def toggle_bookmark(q):
    bm = st.session_state.bookmarks
    if q["question"] in bm:
        bm.pop(q["question"], None)
        db_sync_bookmark(q, False)
    else:
        bm[q["question"]] = q
        db_sync_bookmark(q, True)


def current_choice(q, qid, i):
    s, t_q = st.session_state, q["type"]
    if t_q in ("mcq", "tf"):
        return s.get(f"radio_{qid}_{i}")
    if t_q == "multi":
        return [o for n, o in enumerate(q["options"]) if s.get(f"cb_{qid}_{i}_{n}")]
    if t_q in ("blank", "num"):
        return s.get(f"txt_{qid}_{i}")
    return s.get(f"ta_{qid}_{i}")


def answer_widget(q, qid, i, locked, prev):
    t_q = q["type"]
    if t_q in ("mcq", "tf"):
        idx = q["options"].index(prev) if prev in q["options"] else None
        return st.radio("Apna answer chuno", q["options"], index=idx, key=f"radio_{qid}_{i}", disabled=locked, label_visibility="collapsed")
    if t_q == "multi":
        st.caption("Ek se zyada sahi options chuno")
        chosen = set(prev or [])
        sel = []
        for n, o in enumerate(q["options"]):
            if st.checkbox(o, value=(o in chosen), key=f"cb_{qid}_{i}_{n}", disabled=locked):
                sel.append(o)
        return sel
    if t_q == "num":
        return st.text_input("Numerical answer", value=prev or "", key=f"txt_{qid}_{i}", disabled=locked, placeholder="Sirf number likho, jaise 12.5")
    if t_q == "blank":
        return st.text_input("Khali jagah bharo", value=prev or "", key=f"txt_{qid}_{i}", disabled=locked, placeholder="Apna answer type karo…")
    return st.text_area("Apna answer likho (1-3 line)", value=prev or "", key=f"ta_{qid}_{i}", height=120, disabled=locked)


def feedback_html(i, q, timed_out):
    ss = st.session_state
    prev = ss.answers.get(i)
    ok = is_correct(i)
    if q["type"] == "short":
        g = ss.grades.get(i, {"score": 0, "feedback": ""})
        cls = "ok" if ok else ("mid" if g["score"] >= 0.3 else "no")
        head = "✅ <b>Badhiya!</b>" if ok else "🟡 <b>Adhura / galat.</b>"
        return (
            f"<div class='qf-fb {cls}'>{head} AI score: <b>{g['score']:.1f} / 1</b><br>{esc(g['feedback'])}"
            f"<br><br><b>Model answer:</b> {esc(q['answer'])}<br>{esc(q['explanation'])}</div>"
        )
    if ok:
        return f"<div class='qf-fb ok'>✅ <b>Sahi jawab!</b><br>{esc(q['explanation'])}</div>"
    why = "⏰ <b>Time khatam.</b> " if timed_out else ("⏭️ <b>Skip.</b> " if prev is None else "❌ <b>Galat.</b> ")
    return f"<div class='qf-fb no'>{why}Sahi answer: <b>{esc(correct_text(q))}</b><br>{esc(q['explanation'])}</div>"


def build_report_html():
    ss = st.session_state
    r = ss.result
    rows = ""
    for i, q in enumerate(ss.quiz):
        ok = is_correct(i)
        rows += (
            f"<tr><td>{i + 1}</td><td>{esc(q['question'])}</td><td>{esc(user_text(i))}</td>"
            f"<td>{esc(correct_text(q))}</td><td style='color:{'#1FA67A' if ok else '#E5484D'}'>{'✔' if ok else 'x'}</td>"
            f"<td>{esc(q['explanation'])}</td></tr>"
        )
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{APP_NAME} Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 16px;color:#222}}
h1{{color:#4B3FD1}} table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:8px;font-size:14px;vertical-align:top}}
th{{background:#4B3FD1;color:#fff}}</style></head><body>
<h1>{APP_NAME} · Result Report</h1>
<p>{esc(ss.meta.get('label', 'Quiz'))} · {esc(ss.meta.get('difficulty', ''))} · {datetime.now().strftime('%d %b %Y, %H:%M')}</p>
<table><tr><th>#</th><th>Question</th><th>Your answer</th><th>Correct</th><th></th><th>Explanation</th></tr>{rows}</table>
</body></html>"""


# ─────────────────────────────────────────────────────────────
# BROWSER JS / AUDIO LAYER
# ─────────────────────────────────────────────────────────────
QF_VERSION = 4
QF_JS = r"""
(function(){
  var old = window.qf; if (old && old.off) { try { old.off(); } catch(e) {} }
  var qf = {v:__V__, muted:false, lang:'en-IN', rate:1, cur:null, ac:null, lastAuto:null};
  qf.ctx = function(){
    var C = window.AudioContext || window.webkitAudioContext; if(!C) return null;
    if(!qf.ac) qf.ac = new C(); if(qf.ac.state === 'suspended') qf.ac.resume(); return qf.ac;
  };
  qf.tone = function(f, t0, d, type, vol){
    var c = qf.ctx(); if(!c) return;
    var o = c.createOscillator(), g = c.createGain(), t = c.currentTime + t0;
    o.type = type || 'sine'; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol || 0.16, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + d);
    o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + d + 0.05);
  };
  qf.play = function(name){
    if(qf.muted) return;
    try {
      if(name === 'correct'){ qf.tone(659,0,.14); qf.tone(880,.11,.22); }
      else if(name === 'wrong'){ qf.tone(196,0,.22,'sawtooth',.10); qf.tone(147,.14,.32,'sawtooth',.10); }
      else if(name === 'win'){ [523,659,784,1047].forEach(function(f,i){ qf.tone(f,i*.12,i===3?.5:.18,'triangle',.18); }); }
      else if(name === 'lose'){ [392,330,262].forEach(function(f,i){ qf.tone(f,i*.16,.3,'triangle',.14); }); }
    } catch(e) {}
  };
  qf.speak = function(text){
    var s = window.speechSynthesis; if(!s || !text) return;
    s.cancel();
    var u = new SpeechSynthesisUtterance(text); u.lang = qf.lang; u.rate = qf.rate;
    var vs = s.getVoices() || [], pre = qf.lang.slice(0,2);
    var v = vs.find(function(x){ return x.lang === qf.lang; }) || vs.find(function(x){ return x.lang.indexOf(pre) === 0; });
    if(v) u.voice = v; s.speak(u);
  };
  qf.speakCur = function(){ if(qf.cur) qf.speak(qf.cur.text); };
  var onKey = function(e){
    var t = e.target, tag = ((t && t.tagName) || '').toLowerCase();
    if(tag === 'input' || tag === 'textarea' || tag === 'select' || (t && t.isContentEditable)) return;
    if(e.ctrlKey || e.metaKey || e.altKey) return;
    var clickBtn = function(re){
      var b = Array.prototype.slice.call(document.querySelectorAll('button')).find(function(x){
        return re.test(x.innerText) && !x.disabled && x.offsetParent !== null; });
      if(b){ b.click(); return true; } return false;
    };
    if(/^[1-9]$/.test(e.key)){
      var labels = document.querySelectorAll('.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]');
      var n = parseInt(e.key, 10) - 1;
      if(labels[n]){ labels[n].click(); e.preventDefault(); }
    } else if(e.key === 'Enter'){
      if(tag === 'button') return;
      if(clickBtn(/Check answer|Next|Finish|Result dekho/)) e.preventDefault();
    } else if(e.key === 'h' || e.key === 'H'){ clickBtn(/Hint/); }
    else if(e.key === 's' || e.key === 'S'){ clickBtn(/Skip/); }
    else if(e.key === 'r' || e.key === 'R'){ qf.speakCur(); }
  };
  document.addEventListener('keydown', onKey, true);
  qf.off = function(){ document.removeEventListener('keydown', onKey, true); };
  window.qf = qf;
})();
""".replace("__V__", str(QF_VERSION))

BOOT_TEMPLATE = """<script>(function(){var P=window.parent;try{
if(!P.qf||P.qf.v!==__V__){var s=P.document.createElement('script');s.textContent=__CODE__;P.document.head.appendChild(s);}
var qf=P.qf;Object.assign(qf,__CFG__);qf.cur=__CUR__;
__SOUND__
__AUTO__
}catch(e){console.warn('qf',e);}})();</script><!--__NONCE__-->"""


def render_browser_layer(sound_on, tts_lang, tts_rate, auto_read):
    ss = st.session_state
    sound = ss.pop("sound", None)
    cur, auto_key = "null", None
    if ss.stage == "quiz" and ss.quiz and ss.idx < len(ss.quiz):
        q = ss.quiz[ss.idx]
        cur = json.dumps({"text": speech_text(q)})
        if auto_read and not ss.locked.get(ss.idx):
            auto_key = f"{ss.quiz_id}-{ss.idx}"
    js = (
        BOOT_TEMPLATE.replace("__V__", str(QF_VERSION))
        .replace("__CODE__", json.dumps(QF_JS))
        .replace("__CFG__", json.dumps({"muted": not sound_on, "lang": tts_lang, "rate": tts_rate}))
        .replace("__CUR__", cur)
        .replace("__SOUND__", f"qf.play({json.dumps(sound)});" if sound else "")
        .replace(
            "__AUTO__",
            f"if(qf.lastAuto!=={json.dumps(auto_key)}){{qf.lastAuto={json.dumps(auto_key)};setTimeout(function(){{qf.speakCur();}},250);}}"
            if auto_key
            else "",
        )
        .replace("__NONCE__", str(time.time()))
    )
    components.html(js, height=0)


def speak_button(text):
    colors = (
        {"__LINE__": "rgba(30,35,80,.2)", "__BG__": "#ffffff", "__FG__": "#1B1F3B"}
        if LIGHT
        else {"__LINE__": "rgba(255,255,255,.14)", "__BG__": "rgba(255,255,255,.07)", "__FG__": "#E8EAF6"}
    )
    code = f"""<button style="width:100%;height:40px;border-radius:12px;border:1px solid {colors['__LINE__']};background:{colors['__BG__']};color:{colors['__FG__']};font-weight:700;cursor:pointer" onclick="window.parent.qf.speak({json.dumps(text)})">🔊 {t('listen_btn')}</button>"""
    components.html(code, height=42)


# ─────────────────────────────────────────────────────────────
# COUNTDOWN FRAGMENTS
# ─────────────────────────────────────────────────────────────
def _countdown(limit, qid, i, total, instant):
    ss = st.session_state
    left = limit - (time.time() - ss.q_start)
    if left > 0:
        st.progress(max(left / limit, 0.0), text=f"⏱️ {math.ceil(left)} sec bache hain")
        return
    q = ss.quiz[i]
    ss.answers[i] = norm_answer(current_choice(q, qid, i))
    record_time(i)
    if instant:
        if q["type"] == "short" and ss.answers[i]:
            grade_short(i)
        ss.locked[i] = True
        ss.timed_out[i] = True
        queue_sound("wrong")
    elif i == total - 1:
        finish_quiz()
    else:
        advance(i)
    st.rerun()


def _quiz_countdown(total_secs, qid, i):
    ss = st.session_state
    left = total_secs - (time.time() - ss.start_time)
    if left > 0:
        m, sec = divmod(math.ceil(left), 60)
        st.progress(max(left / total_secs, 0.0), text=f"⏳ Time: {m:02d}:{sec:02d}")
        return
    q = ss.quiz[i]
    if not ss.locked.get(i):
        ss.answers[i] = norm_answer(current_choice(q, qid, i))
        record_time(i)
    ss.quiz_time_up = True
    finish_quiz()
    st.rerun()


_fragment = getattr(st, "fragment", None)
countdown = _fragment(run_every=1)(_countdown) if _fragment else None
quiz_countdown = _fragment(run_every=1)(_quiz_countdown) if _fragment else None

# ─────────────────────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────────────────────
CM = ensure_auth()

# ─────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION & GLOBAL SETTINGS
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    # GLOBAL APP LANGUAGE TOGGLE
    st.markdown("### 🌐 Global Interface")
    app_lang = st.selectbox(
        t("app_lang"),
        ["Hinglish", "English", "Hindi"],
        index=["Hinglish", "English", "Hindi"].index(st.session_state.get("app_lang", "Hinglish")),
        key="app_lang_select",
    )
    st.session_state["app_lang"] = app_lang

    st.divider()

    lvl = level_of(st.session_state.total_xp)
    st.markdown(f"### 🎖️ {t('level')} {lvl}")
    st.progress((st.session_state.total_xp % 100) / 100, text=f"{st.session_state.total_xp} XP · Next Level {100 - st.session_state.total_xp % 100}")

    st.markdown(f"### {t('settings')}")
    num_questions = st.slider(t("questions_count"), 3, 50, 5)
    difficulty = st.select_slider(t("difficulty"), ["Easy", "Medium", "Hard"], value="Medium")
    adaptive = st.toggle(t("adaptive"), value=False)
    type_sel = st.multiselect(t("q_types"), list(TYPE_MAP.keys()), default=["Multiple Choice", "True / False"])
    type_keys = [TYPE_MAP[x] for x in type_sel] or ["mcq"]
    language = st.selectbox("AI Content Language", ["English", "Hinglish", "Hindi"])
    mode = st.radio(t("mode"), ["Practice", "Exam", "Survival"])

    st.markdown(f"**{t('timer')}**")
    timer_mode = st.selectbox("Timer", ["Off", "Har sawal par", "Poore quiz ka"], label_visibility="collapsed")
    time_limit = quiz_limit = 0
    if timer_mode == "Har sawal par":
        pick = st.selectbox("Seconds", [10, 15, 20, 30, 45, 60, 90, 120, "Custom"], index=3)
        time_limit = int(st.number_input("Custom Sec", 5, 600, 30, 5)) if pick == "Custom" else int(pick)
    elif timer_mode == "Poore quiz ka":
        pick = st.selectbox("Minutes", [5, 10, 15, 20, 30, 45, 60, 90, "Custom"], index=1)
        mins = int(st.number_input("Custom Min", 1, 180, 10, 1)) if pick == "Custom" else int(pick)
        quiz_limit = mins * 60

    st.markdown(f"**{t('marking')}**")
    marks_correct = float(st.selectbox("Marks for Correct", [1, 2, 4, 5], index=0))
    neg_label = st.selectbox("Negative Marking", ["Nahi", "¼ (−0.25)", "⅓ (−0.33)", "½ (−0.5)", "Full (−1)"])
    neg_frac = {"Nahi": 0.0, "¼ (−0.25)": 0.25, "⅓ (−0.33)": 1 / 3, "½ (−0.5)": 0.5, "Full (−1)": 1.0}[neg_label]

    with st.expander("🔊 Audio & Theme"):
        sound_on = st.toggle("Sound Effects", value=True, key="sound_on")
        auto_read = st.toggle("Auto Read Question", value=False, key="auto_read")
        tts_rate = st.slider("Speech Rate", 0.6, 1.4, 1.0, 0.1, key="tts_rate")
        st.toggle("☀️ Light Mode", value=False, key="light")

    with st.expander("Advanced AI"):
        model = st.selectbox("Groq Model", MODELS)

    st.divider()
    nb = len(st.session_state.bookmarks)
    st.markdown(f"### {t('saved_questions')}")
    if nb:
        st.caption(f"{nb} saved")
        if st.session_state.stage != "quiz" and st.button(f"📇 {t('flashcards_btn')}", use_container_width=True):
            st.session_state.flash_cards = list(st.session_state.bookmarks.values())
            st.session_state.flash_i = 0
            st.session_state.flash_show = False
            st.session_state.flash_return = st.session_state.stage
            st.session_state.stage = "flash"
            st.rerun()

    st.divider()
    st.markdown(f"### {t('my_history')}")
    if st.session_state.history:
        for h in reversed(st.session_state.history[-5:]):
            st.markdown(f"**{esc(h['topic'])[:25]}** · {fmt_marks(h['marks'])}/{fmt_marks(h['max'])} marks")
    else:
        st.caption("No history yet.")

    st.divider()
    if AUTH_ENABLED and st.session_state.get("user"):
        _u = st.session_state["user"]
        st.markdown(f"### {t('account')}")
        st.caption(_u.get("email") or _u.get("phone") or "Logged in")
        if st.button(t("logout"), use_container_width=True):
            do_logout(CM)

# ─────────────────────────────────────────────────────────────
# MAIN HERO HEADER
# ─────────────────────────────────────────────────────────────
_order = {"setup": 0, "quiz": 1, "result": 2}
_cur = _order.get(st.session_state.stage, -1)
_steps = f"<span class='qf-step {'on' if _cur==0 else 'done'}'>{t('step_1')}</span>"
_steps += f"<span class='qf-step {'on' if _cur==1 else ('done' if _cur>1 else '')}'>{t('step_2')}</span>"
_steps += f"<span class='qf-step {'on' if _cur==2 else ''}'>{t('step_3')}</span>"

st.markdown(
    f"""
<div class="qf-hero">
  <div class="qf-title qf-display">{APP_NAME}</div>
  <div class="qf-sub">{t('hero_sub')}</div>
  <div class="qf-steps">{_steps}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════
# STAGE 1: SETUP
# ═════════════════════════════════════════════════════════════
if st.session_state.stage == "setup":
    hist = st.session_state.history
    best_pct = max(h["pct"] for h in hist) if hist else 0
    st.markdown(
        f"""<div class="qf-tiles">
  <div class="qf-tile"><div class="v">{lvl}</div><div class="l">{t('level')}</div></div>
  <div class="qf-tile"><div class="v" style="color:#F59E0B">{st.session_state.total_xp}</div><div class="l">{t('total_xp')}</div></div>
  <div class="qf-tile"><div class="v">{len(hist)}</div><div class="l">{t('quizzes_played')}</div></div>
  <div class="qf-tile"><div class="v" style="color:#10B981">{best_pct}%</div><div class="l">{t('best_score')}</div></div>
</div>""",
        unsafe_allow_html=True,
    )

    cfg = {
        "num_questions": num_questions, "difficulty": difficulty, "adaptive": adaptive, "type_keys": type_keys,
        "language": language, "mode": mode, "time_limit": time_limit, "quiz_limit": quiz_limit,
        "marks": marks_correct, "neg": neg_frac, "model": model,
    }
    tab_quiz, tab_pyq, tab_doubt = st.tabs([t("tab_quiz"), t("tab_pyq"), t("tab_doubt")])

    with tab_quiz:
        with st.container(key="srcpick"):
            source = st.radio(t("src_prompt"), ["💡 Topic", "📄 PDF", "🖼️ Photo", "📝 Notes"], horizontal=True)

        input_text, label, media = "", "", None

        with st.container(key="panel"):
            if source.startswith("💡"):
                topic = st.text_input(t("topic_input"), placeholder=t("topic_placeholder"))
                st.caption(t("quick_picks"))
                cols = st.columns(4)
                for c, pick in zip(cols, ["Python Basics", "World History", "Human Biology", "Indian Economy"]):
                    if c.button(pick, use_container_width=True, key=f"pick_{pick}"):
                        st.session_state["_picked"] = pick
                        st.rerun()
                if st.session_state.get("_picked") and not topic:
                    topic = st.session_state["_picked"]
                if topic.strip():
                    input_text = f"Topic: {topic.strip()}\nUse knowledge to cover this accurately."
                    label = topic.strip()

            elif source.startswith("📄"):
                up = st.file_uploader("Upload PDF", type=["pdf"])
                if up is not None:
                    _, total_pages = read_pdf(up, 1, 1)
                    up.seek(0)
                    rng = st.slider("Pages", 1, total_pages, (1, min(total_pages, 10))) if total_pages > 1 else (1, 1)
                    pdf_text, _ = read_pdf(up, rng[0], rng[1])
                    if pdf_text.strip():
                        st.success(f"Loaded {len(pdf_text):,} characters.")
                        input_text, label = pdf_text, f"PDF: {up.name}"

            elif source.startswith("🖼️"):
                photo_mode = st.radio("Photo Mode", ["📁 Upload File", "📸 Live Camera"], horizontal=True)
                mf = (
                    st.file_uploader("Upload Photo", type=["png", "jpg", "jpeg", "webp"])
                    if photo_mode.startswith("📁")
                    else st.camera_input("Take Photo")
                )
                if mf is not None:
                    data, mime = prepare_image(mf.getvalue(), getattr(mf, "type", "image/jpeg"))
                    st.image(data, use_container_width=True)
                    media = {"bytes": data, "mime": mime}
                    input_text, label = "(image)", "Photo Notes"

            else:
                pasted = st.text_area("Paste Notes Here", height=180)
                if pasted.strip():
                    input_text, label = pasted, "Notes"

        st.write("")
        if st.button(t("generate_btn"), type="primary", use_container_width=True):
            if input_text.strip():
                tkey = topic_key_for("ai", label)
                quiz = generate_with_progress(
                    input_text, cfg["num_questions"], cfg["difficulty"], cfg["type_keys"], cfg["language"], cfg["model"],
                    media=media, adaptive=cfg["adaptive"], avoid=get_seen_questions(tkey),
                )
                if quiz:
                    start_quiz(quiz, {
                        "label": label, "difficulty": cfg["difficulty"], "mode": cfg["mode"], "source": input_text,
                        "media": media, "types": cfg["type_keys"], "adaptive": cfg["adaptive"], "language": cfg["language"],
                        "model": cfg["model"], "time_limit": cfg["time_limit"], "quiz_limit": cfg["quiz_limit"],
                        "marks": cfg["marks"], "neg": cfg["neg"], "tkey": tkey
                    })
                    st.rerun()

    with tab_pyq:
        st.markdown("### 🏛️ Govt & Entrance Exam PYQs")
        with st.container(key="panel_pyq"):
            exam = st.selectbox("Target Exam", EXAM_LIST, key="pyq_exam")
            dataset = load_pyq_dataset(exam)
            subjects = ["All subjects"] + EXAM_SUBJECTS.get(exam, [])
            subject = st.selectbox("Subject", subjects, key=f"pyq_subj_{exam}")
            fresh_pool = [q for q in dataset if subject == "All subjects" or q["subject"].lower() == subject.lower()]
            st.info(f"{len(fresh_pool)} Questions available in dataset.")

            if st.button(t("start_pyq_btn"), type="primary", use_container_width=True):
                if fresh_pool:
                    quiz = [pyq_to_item(q) for q in random.sample(fresh_pool, min(cfg["num_questions"], len(fresh_pool)))]
                    start_quiz(quiz, {
                        "label": f"{exam} PYQ", "difficulty": "Medium", "mode": cfg["mode"], "source": exam,
                        "media": None, "types": ["mcq"], "adaptive": False, "language": cfg["language"],
                        "model": cfg["model"], "time_limit": cfg["time_limit"], "quiz_limit": cfg["quiz_limit"],
                        "marks": cfg["marks"], "neg": cfg["neg"], "tkey": f"pyq::{exam}"
                    })
                    st.rerun()

    with tab_doubt:
        st.markdown("### 🔍 AI Doubt Solver")
        q_txt = st.text_area("Ask any doubt...", height=120)
        if st.button("💡 Solve Doubt", type="primary", use_container_width=True):
            if q_txt.strip():
                st.session_state.doubt_thread = [{"role": "user", "content": q_txt.strip()}]
                st.session_state.doubt_pending = True
                st.rerun()

        for msg in st.session_state.get("doubt_thread", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.get("doubt_pending"):
            with st.chat_message("assistant"):
                msgs = [{"role": "system", "content": "You are a helpful tutor."}] + st.session_state.doubt_thread
                ans = st.write_stream(llm_stream(msgs, cfg["model"]))
                ans = "".join(ans) if isinstance(ans, list) else str(ans)
                st.session_state.doubt_thread.append({"role": "assistant", "content": ans})
                st.session_state.doubt_pending = False

# ═════════════════════════════════════════════════════════════
# STAGE 2: QUIZ PLAY
# ═════════════════════════════════════════════════════════════
elif st.session_state.stage == "quiz":
    ss = st.session_state
    quiz = ss.quiz
    total = len(quiz)
    i = ss.idx
    q = quiz[i]
    qid = ss.quiz_id
    instant = ss.meta.get("mode") in ("Practice", "Survival")

    top_l, top_r = st.columns([4, 1.4])
    top_l.progress((i + 1) / total, text=f"Question {i + 1} / {total}")
    top_r.markdown(f"**Score:** {sum(question_marks(j) for j in ss.locked)}")

    st.markdown(
        f"""<div class="qf-qcard">
        <div class="qf-qnum">Question {i + 1}</div>
        <div class="qf-qtext">{esc(q['question'])}</div></div>""",
        unsafe_allow_html=True,
    )

    h1, h2, h3 = st.columns([1.5, 1.2, 1.5])
    if q.get("hint") and not ss.locked.get(i):
        if h1.button(t("hint_btn"), key=f"hint_{i}"):
            ss.hints_used[i] = True
            st.rerun()

    saved = q["question"] in ss.bookmarks
    if h2.button(t("saved_btn") if saved else t("save_btn"), key=f"save_{i}"):
        toggle_bookmark(q)
        st.rerun()

    with h3:
        speak_button(speech_text(q))

    if ss.hints_used.get(i) and q.get("hint"):
        st.info(f"💡 {q['hint']}")

    prev = ss.answers.get(i)
    with st.container(key="optbox"):
        choice = answer_widget(q, qid, i, ss.locked.get(i, False), prev)

    if instant and ss.locked.get(i):
        st.markdown(feedback_html(i, q, ss.timed_out.get(i)), unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    if instant and not ss.locked.get(i):
        if b2.button(t("check_btn"), type="primary", use_container_width=True):
            ss.answers[i] = norm_answer(choice)
            ss.locked[i] = True
            record_time(i)
            queue_sound("correct" if is_correct(i) else "wrong")
            st.rerun()
        if b3.button(t("skip_btn"), use_container_width=True):
            ss.answers[i] = None
            ss.locked[i] = True
            if i == total - 1:
                finish_quiz()
            else:
                advance(i)
            st.rerun()
    else:
        btn_txt = t("finish_btn") if i == total - 1 else t("next_btn")
        if b3.button(btn_txt, type="primary", use_container_width=True):
            ss.answers[i] = norm_answer(choice)
            record_time(i)
            if i == total - 1:
                finish_quiz()
            else:
                advance(i)
            st.rerun()

# ═════════════════════════════════════════════════════════════
# STAGE 3: FLASHCARDS
# ═════════════════════════════════════════════════════════════
elif st.session_state.stage == "flash":
    ss = st.session_state
    cards = ss.flash_cards
    fi = ss.flash_i
    card = cards[fi]

    st.markdown(f"## 📇 {t('flashcards_btn')}")
    st.progress((fi + 1) / len(cards), text=f"Card {fi + 1} / {len(cards)}")

    if ss.flash_show:
        st.success(f"**Answer:** {correct_text(card)}\n\n{card['explanation']}")
    else:
        st.info(f"Question:")

    f1, f2, f3 = st.columns(3)
    if f1.button("⬅️ Previous", disabled=fi == 0):
        ss.flash_i -= 1
        ss.flash_show = False
        st.rerun()
    if f2.button("🔄 Flip Card", type="primary"):
        ss.flash_show = not ss.flash_show
        st.rerun()
    if f3.button("Next ➡️", disabled=fi == len(cards) - 1):
        ss.flash_i += 1
        ss.flash_show = False
        st.rerun()

    if st.button(t("back_btn")):
        ss.stage = ss.flash_return
        st.rerun()

# ═════════════════════════════════════════════════════════════
# STAGE 4: RESULT
# ═════════════════════════════════════════════════════════════
else:
    ss = st.session_state
    res = ss.result
    st.markdown("## 🏆 Quiz Results")

    st.markdown(
        f"""
    <div class="qf-tiles">
      <div class="qf-tile"><div class="v" style="color:#10B981">{res['score']} / {res['total']}</div><div class="l">Score</div></div>
      <div class="qf-tile"><div class="v" style="color:#06B6D4">{res['accuracy']}%</div><div class="l">Accuracy</div></div>
      <div class="qf-tile"><div class="v" style="color:#F59E0B">+{res['xp']}</div><div class="l">XP Earned</div></div>
      <div class="qf-tile"><div class="v">{res['best_streak']} 🔥</div><div class="l">Best Streak</div></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns(3)
    if a1.button(t("new_quiz"), type="primary", use_container_width=True):
        reset_all()
        st.rerun()
    if a2.button(t("retry_wrong"), use_container_width=True):
        wrong_q = [ss.quiz[k] for k in range(len(ss.quiz)) if not is_correct(k)]
        if wrong_q:
            start_quiz(wrong_q, ss.meta)
            st.rerun()
    if a3.button(t("restart_quiz"), use_container_width=True):
        start_quiz(ss.quiz, ss.meta)
        st.rerun()

    st.download_button("📄 Download HTML Report", build_report_html(), file_name="Quiz_Report.html", mime="text/html")

# ─────────────────────────────────────────────────────────────
# BROWSER ENGINE LAYER
# ─────────────────────────────────────────────────────────────
render_browser_layer(
    sound_on=st.session_state.get("sound_on", True),
    tts_lang="hi-IN" if st.session_state.get("app_lang") == "Hindi" else "en-IN",
    tts_rate=st.session_state.get("tts_rate", 1.0),
    auto_read=st.session_state.get("auto_read", False),
)
