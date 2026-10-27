import io
import os
import re
import json
import math
import time
import base64
import random
import difflib
import html
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from groq import Groq

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuizForge · AI Quiz Arena",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

LIGHT = bool(st.session_state.get("light", False))

# ─────────────────────────────────────────────────────────────
# STYLING — midnight ink, violet→cyan energy, amber highlights
# ─────────────────────────────────────────────────────────────
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
@property --p { syntax:'<number>'; inherits:false; initial-value:0; }

:root{
  --bg:#0B0F1E; --panel:rgba(255,255,255,.045); --panel-2:rgba(255,255,255,.07);
  --line:rgba(255,255,255,.12); --txt:#E8EAF6; --mute:#9AA3C7;
  --violet:#7C5CFF; --cyan:#22D3EE; --amber:#FFC857; --good:#34D399; --bad:#FB7185;
}
html, body, [class*="css"]{ font-family:'Plus Jakarta Sans',sans-serif; color:var(--txt); }
h1,h2,h3,.qf-display{ font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.02em; }
/* Hide watermark but keep the sidebar toggle usable (important on mobile) */
#MainMenu, footer{ visibility:hidden; height:0; }
header[data-testid="stHeader"]{ background:transparent !important; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarExpandButton"]{
  display:block !important; position:fixed !important; top:12px !important; left:12px !important; z-index:999999 !important;
  background-color:#1f2937 !important; border-radius:8px !important; border:1px solid var(--line) !important;
  box-shadow:0 4px 12px rgba(0,0,0,.5) !important;
}

.stApp{
  background:
    radial-gradient(1100px 560px at 8% -10%, rgba(124,92,255,.25), transparent 60%),
    radial-gradient(900px 480px at 100% 0%, rgba(34,211,238,.15), transparent 55%),
    var(--bg);
}
.block-container{ padding-top:1.4rem; max-width:860px; }
section[data-testid="stSidebar"]{ background:#0E1330; border-right:1px solid var(--line); }

/* Hero */
.qf-hero{
  position:relative; overflow:hidden; border-radius:26px; padding:38px 34px 28px; margin-bottom:18px;
  border:1px solid var(--line);
  background:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px) 0 0/28px 28px,
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px) 0 0/28px 28px,
    linear-gradient(135deg, rgba(124,92,255,.35), rgba(34,211,238,.12) 70%, rgba(11,15,30,.4));
}
.qf-hero:after{
  content:""; position:absolute; width:340px; height:340px; right:-90px; top:-120px; border-radius:50%;
  background:radial-gradient(circle, rgba(255,200,87,.38), transparent 65%); filter:blur(6px);
}
.qf-title{
  font-size:3.3rem; font-weight:700; line-height:1; margin:0; position:relative; z-index:1;
  background:linear-gradient(90deg,#fff 10%,#C9BEFF 45%,#7BE7F7 90%); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent;
}
.qf-sub{ margin-top:12px; color:#C3C9EA; font-size:1.05rem; max-width:560px; position:relative; z-index:1; }
.qf-steps{ display:flex; gap:8px; margin-top:20px; position:relative; z-index:1; flex-wrap:wrap; }
.qf-step{ padding:6px 14px; border-radius:99px; font-size:.82rem; font-weight:600; color:#AEB6DD; border:1px solid rgba(255,255,255,.18); background:rgba(0,0,0,.2); }
.qf-step.on{ color:#0B0F1E; background:var(--amber); border-color:var(--amber); }
.qf-step.done{ color:var(--good); border-color:rgba(52,211,153,.5); }

/* Glass panels */
.st-key-panel, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-optbox, .st-key-morebox{
  background:var(--panel); border:1px solid var(--line); border-radius:20px; padding:20px 22px; backdrop-filter:blur(6px);
}
.st-key-optbox{ padding:14px 16px; counter-reset:opt; }

/* Source picker → pills */
.st-key-srcpick div[role="radiogroup"]{ gap:8px; flex-wrap:wrap; }
.st-key-srcpick label[data-baseweb="radio"]{ background:var(--panel); border:1px solid var(--line); border-radius:99px; padding:8px 16px; margin:0; }
.st-key-srcpick label[data-baseweb="radio"]:has(input:checked){ background:rgba(124,92,255,.28); border-color:var(--violet); }
.st-key-srcpick label[data-baseweb="radio"] > div:first-of-type{ display:none; }

/* Answer options → numbered cards */
.st-key-optbox div[role="radiogroup"]{ gap:0; }
.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]{
  display:flex; align-items:center; gap:12px;
  background:var(--panel-2); border:1.5px solid var(--line); border-radius:14px; padding:12px 14px; margin:0 0 10px; width:100%;
  transition:border-color .12s, background .12s, transform .08s;
}
.st-key-optbox label[data-baseweb="radio"]::before, .st-key-optbox label[data-baseweb="checkbox"]::before{
  counter-increment:opt; content:counter(opt); flex:0 0 auto; width:28px; height:28px; border-radius:9px;
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:.85rem;
  background:rgba(124,92,255,.22); color:var(--txt); border:1px solid var(--line);
}
.st-key-optbox label[data-baseweb="radio"] > div:first-of-type{ display:none; }
.st-key-optbox label[data-baseweb="radio"]:hover, .st-key-optbox label[data-baseweb="checkbox"]:hover{ border-color:var(--cyan); transform:translateX(2px); }
.st-key-optbox label:has(input:checked){ border-color:var(--violet); background:rgba(124,92,255,.22); }
.st-key-optbox label:has(input:checked)::before{ background:var(--violet); color:#fff; border-color:var(--violet); }

/* Question card */
@keyframes qf-rise{ from{ opacity:0; transform:translateY(8px); } to{ opacity:1; transform:none; } }
.qf-qcard{
  position:relative; background:linear-gradient(160deg, rgba(124,92,255,.18), rgba(255,255,255,.04));
  border:1px solid var(--line); border-radius:20px; padding:24px 26px; margin:12px 0 12px; animation:qf-rise .35s ease-out;
}
.qf-qcard:before{ content:""; position:absolute; left:0; top:20px; bottom:20px; width:5px; border-radius:0 6px 6px 0; background:var(--amber); }
.qf-qnum{ font-size:.82rem; font-weight:700; color:var(--amber); margin-bottom:8px; }
.qf-qtext{ font-family:'Space Grotesk',sans-serif; font-size:1.4rem; font-weight:500; line-height:1.38; }
.qf-tags{ float:right; display:flex; gap:6px; }
.qf-tag{ font-size:.74rem; padding:3px 11px; border-radius:99px; border:1px solid var(--line); color:var(--mute); }
.qf-tag.lv{ border-color:var(--cyan); color:var(--cyan); }
.qf-kbd{ font-size:.78rem; color:var(--mute); margin:2px 0 12px; }
.qf-kbd kbd{ background:var(--panel-2); border:1px solid var(--line); border-bottom-width:2px; border-radius:6px; padding:1px 7px; font-family:inherit; font-size:.76rem; color:var(--txt); }

.qf-fb{ border-radius:14px; padding:14px 18px; margin:10px 0; }
.qf-fb.ok{ background:rgba(52,211,153,.12); border:1px solid var(--good); }
.qf-fb.no{ background:rgba(251,113,133,.12); border:1px solid var(--bad); }
.qf-fb.mid{ background:rgba(255,200,87,.1); border:1px solid var(--amber); }
.qf-hint{ background:rgba(255,200,87,.1); border:1px dashed var(--amber); border-radius:12px; padding:10px 14px; margin:8px 0; }
.qf-hearts{ text-align:right; font-size:1.15rem; letter-spacing:2px; }

/* Stats */
.qf-tiles{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:14px 0 10px; }
.qf-tile{ background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:14px 10px; text-align:center; }
.qf-tile .v{ font-family:'Space Grotesk',sans-serif; font-size:1.5rem; font-weight:700; }
.qf-tile .l{ font-size:.76rem; color:var(--mute); }
@media (max-width:640px){ .qf-tiles{ grid-template-columns:repeat(2,1fr);} .qf-title{ font-size:2.4rem; } }

.qf-ring{ --t:0; position:relative; width:170px; height:170px; margin:8px auto 6px; display:flex; align-items:center; justify-content:center; }
.qf-ring:before{
  content:""; position:absolute; inset:0; border-radius:50%;
  background:conic-gradient(var(--ring-color) calc(var(--p)*1%), rgba(127,127,160,.25) 0);
  -webkit-mask:radial-gradient(farthest-side, transparent calc(100% - 15px), #000 calc(100% - 14px));
          mask:radial-gradient(farthest-side, transparent calc(100% - 15px), #000 calc(100% - 14px));
  animation:qf-fill 1.3s cubic-bezier(.2,.8,.2,1) forwards;
}
@keyframes qf-fill{ from{ --p:0; } to{ --p:var(--t); } }
.qf-ring-in{ position:relative; text-align:center; }
.qf-ring-in .big{ font-family:'Space Grotesk',sans-serif; font-size:2.5rem; font-weight:700; line-height:1; }
.qf-ring-in .sm{ font-size:.85rem; color:var(--mute); }
@media (prefers-reduced-motion:reduce){ .qf-ring:before{ animation:none; --p:var(--t); } .qf-qcard{ animation:none; } }

.qf-badges{ display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:10px 0; }
.qf-badge{ background:rgba(255,200,87,.12); border:1px solid var(--amber); color:var(--amber); border-radius:99px; padding:6px 14px; font-weight:700; font-size:.86rem; }

.qf-flash{
  min-height:210px; display:flex; align-items:center; justify-content:center; text-align:center; margin:12px 0;
  background:linear-gradient(160deg, rgba(124,92,255,.2), rgba(255,255,255,.04)); border:1px solid var(--line);
  border-radius:22px; padding:30px; font-family:'Space Grotesk',sans-serif; font-size:1.45rem; font-weight:500;
}
.qf-flash.back{ border-color:var(--good); background:rgba(52,211,153,.1); }

/* Buttons & inputs */
.stButton>button, .stDownloadButton>button{
  border-radius:13px; font-weight:700; padding:.6rem 1.1rem; border:1px solid var(--line);
  background:var(--panel-2); color:var(--txt); transition:transform .08s ease, border-color .12s;
}
.stButton>button:hover, .stDownloadButton>button:hover{ transform:translateY(-1px); border-color:var(--cyan); }
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,var(--violet),#4F8CFF 55%,var(--cyan)); border:0; color:#fff;
  box-shadow:0 8px 24px rgba(124,92,255,.35);
}
.stButton>button:focus-visible{ outline:3px solid var(--amber); }
.stTextInput input, .stTextArea textarea{ background:rgba(255,255,255,.05) !important; border-radius:12px !important; border:1px solid var(--line) !important; }
div[data-testid="stExpander"]{ background:var(--panel); border:1px solid var(--line); border-radius:14px; }
.stProgress > div > div > div > div{ background-image:linear-gradient(90deg,var(--violet),var(--cyan)); }
iframe{ border:0; }
</style>
"""

LIGHT_CSS = """
<style>
:root{
  --bg:#F4F5FC; --panel:rgba(255,255,255,.78); --panel-2:#FFFFFF;
  --line:rgba(30,35,80,.16); --txt:#1B1F3B; --mute:#5B6390;
}
.stApp{
  background:
    radial-gradient(1000px 500px at 5% -10%, rgba(124,92,255,.14), transparent 60%),
    radial-gradient(800px 420px at 100% 0%, rgba(34,211,238,.12), transparent 55%),
    #F4F5FC !important;
}
section[data-testid="stSidebar"]{ background:#FFFFFF !important; }
.stApp [data-testid="stMarkdownContainer"] :is(p,li,h1,h2,h3,h4,strong,em,span,small):not([class*="qf-"]),
.stApp [data-testid="stWidgetLabel"] *, .stApp [data-testid="stCaptionContainer"] *,
.stApp label, .stApp [data-testid="stExpander"] summary *{ color:var(--txt) !important; }
.stApp [data-testid="stCaptionContainer"] *{ color:var(--mute) !important; }
.stApp button [data-testid="stMarkdownContainer"] *{ color:inherit !important; }
.stApp [data-testid="stBaseButton-primary"], .stApp [data-testid="stBaseButton-primary"] *{ color:#fff !important; }
.qf-hero{ background:linear-gradient(135deg,#4B3FD1,#6D5BFF 55%,#1CA7C9) !important; }
.qf-hero .qf-sub{ color:#E6E9FF !important; }
.qf-hero .qf-step{ color:#fff !important; border-color:rgba(255,255,255,.45); }
.qf-hero .qf-step.on{ color:#0B0F1E !important; }
.qf-badge{ color:#8A5A00; background:rgba(255,200,87,.25); }
.qf-qnum{ color:#B77900; }
.qf-qcard{ background:linear-gradient(160deg, rgba(124,92,255,.12), rgba(255,255,255,.9)); }
.qf-flash{ background:linear-gradient(160deg, rgba(124,92,255,.12), rgba(255,255,255,.9)); }
.qf-tag.lv{ color:#0A7C93; border-color:#0A7C93; }
.stTextInput input, .stTextArea textarea{ background:#fff !important; color:var(--txt) !important; }
div[data-baseweb="select"] > div{ background:#fff !important; }
div[data-baseweb="select"] *{ color:var(--txt) !important; }
.st-key-optbox label[data-baseweb="radio"]::before, .st-key-optbox label[data-baseweb="checkbox"]::before{ background:rgba(124,92,255,.14); }
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)
if LIGHT:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)
    st.markdown(BASE_CSS, unsafe_allow_html=True)
if LIGHT:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)

# Top header aur Fork button hide karne ke liye ye add karein:
st.markdown("""
<style>
    header[data-testid="stHeader"] {
        display: none !important;
    }
    .main .block-container {
        padding-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

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

MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_CHARS = 24000
MAX_IMG_BYTES = 3 * 1024 * 1024
MAX_TOTAL_Q = 200  # cap for one quiz, including 'aur sawal' extensions
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
}
TYPE_ALIASES = {
    "mcq": "mcq", "multiple choice": "mcq", "multiple_choice": "mcq",
    "tf": "tf", "true/false": "tf", "true_false": "tf", "true / false": "tf", "truefalse": "tf",
    "multi": "multi", "multi-select": "multi", "multiselect": "multi", "multi_select": "multi",
    "blank": "blank", "fill": "blank", "fill in the blank": "blank", "fill_in_the_blank": "blank",
    "short": "short", "short answer": "short", "short_answer": "short",
}
TYPE_SPECS = {
    "mcq": '{"type":"mcq","question":"...","options":["A","B","C","D"],"answer":"<exact text of the correct option>"}',
    "tf": '{"type":"tf","question":"<a statement>","options":["True","False"],"answer":"True"}',
    "multi": '{"type":"multi","question":"... (select all that apply)","options":["..","..","..","..",".."],"answers":["<exact option>","<exact option>"]}',
    "blank": '{"type":"blank","question":"A sentence with ____ in place of the missing word","answer":"missing word or phrase","accept":["acceptable alternative"]}',
    "short": '{"type":"short","question":"open question answerable in 1-3 sentences","answer":"model answer in 1-2 sentences"}',
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
    "stage": "setup", "quiz_id": 0, "history": [], "meta": {}, "total_xp": 0, "bookmarks": {}, "deep": {},
    "flash_cards": [], "flash_i": 0, "flash_show": False, "flash_return": "setup",
    "q_key": None, "q_start": time.time(), "_picked": "",
    "pyq_uploaded": [], "doubt_thread": [], "doubt_pending": False, "doubt_opts": {},
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


def llm_stream(messages, model, temperature=0.85):
    """Yield text chunks so answers appear word by word (used by the Doubt Solver)."""
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
# AI CALLS
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
    """Generate in batches of 10 so big quizzes (up to 50) stay reliable; later batches avoid earlier questions."""
    quiz, seen = [], set()
    avoid_list = list(avoid or [])
    attempts, max_attempts = 0, num_q // 5 + 4
    while len(quiz) < num_q and attempts < max_attempts:
        attempts += 1
        n = min(10, num_q - len(quiz))
        try:
            batch = generate_quiz(text, n, diff, type_keys, lang, model, media=media, avoid=avoid_list, adaptive=adaptive, exam=exam)
        except Exception:
            if quiz:
                break  # keep what we already have
            raise
        for b in batch:
            key = b["question"].strip().lower()
            if key not in seen:
                seen.add(key)
                quiz.append(b)
        avoid_list += [b["question"] for b in batch]
        if progress:
            progress(min(len(quiz) / num_q, 1.0), f"{min(len(quiz), num_q)} / {num_q} sawal ban gaye…")
    return quiz[:num_q]


def generate_with_progress(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, exam=None):
    bar = st.progress(0.0, text="Sawal ban rahe hain…")

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
# QUIZ FLOW
# ─────────────────────────────────────────────────────────────
def start_quiz(quiz, meta):
    st.session_state.update(fresh_run_state())
    st.session_state.update(
        quiz=quiz, quiz_id=st.session_state.quiz_id + 1, start_time=time.time(), stage="quiz", meta=meta, q_key=None
    )


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
    """Move to the next question; in adaptive mode pick the next one by current level."""
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
    """+marks for correct, -penalty for a wrong attempt, 0 for skip. Short answers get partial credit."""
    ss = st.session_state
    q = ss.quiz[i]
    m = ss.meta.get("marks", 1.0)
    pen = m * ss.meta.get("neg", 0.0)
    if is_skipped(i):
        return 0.0
    if q["type"] == "short":
        return round(m * ss.grades.get(i, {}).get("score", 0.0), 2)
    return m if is_correct(i) else -pen


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
    ss.history.append(
        {
            "time": datetime.now().strftime("%d %b, %H:%M"), "topic": ss.meta.get("label", "Quiz"), "difficulty": diff,
            "score": correct, "total": total, "marks": marks, "max": max_marks, "acc": accuracy, "pct": pct,
        }
    )
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
# PYQ DATABASE, MORE-QUESTIONS, PROGRESS BACKUP
# ─────────────────────────────────────────────────────────────
PYQ_FILE = "pyq_data.json"
EXAM_LIST = ["SSC CGL", "RRB NTPC", "Banking (IBPS/SBI)", "UP Police Constable", "UPSC / State PCS", "General All Exams"]
EXAM_SUBJECTS = {
    "SSC CGL": ["Quantitative Aptitude", "General Intelligence & Reasoning", "English Comprehension", "General Awareness"],
    "RRB NTPC": ["Mathematics", "General Intelligence & Reasoning", "General Awareness"],
    "Banking (IBPS/SBI)": ["Quantitative Aptitude", "Reasoning Ability", "English Language", "General/Financial Awareness", "Computer Aptitude"],
    "UP Police Constable": ["General Knowledge", "General Hindi", "Numerical & Mental Ability", "Mental Aptitude / Reasoning"],
    "UPSC / State PCS": ["History", "Geography", "Polity", "Economy", "Science & Technology", "Environment", "Current Affairs"],
    "General All Exams": ["Mixed"],
}
# Approximate patterns (neg = fraction of the marks per question). Patterns change — verify with the official notification.
EXAM_PRESETS = {
    "SSC CGL": {"n": 100, "minutes": 60, "marks": 2.0, "neg": 0.25},
    "RRB NTPC": {"n": 100, "minutes": 90, "marks": 1.0, "neg": 1 / 3},
    "Banking (IBPS/SBI)": {"n": 100, "minutes": 60, "marks": 1.0, "neg": 0.25},
    "UP Police Constable": {"n": 150, "minutes": 120, "marks": 2.0, "neg": 0.25},
    "UPSC / State PCS": {"n": 100, "minutes": 120, "marks": 2.0, "neg": 1 / 3},
}
PYQ_TEMPLATE = json.dumps(
    [
        {"exam": "SSC CGL", "subject": "General Awareness", "year": "2022", "question": "SAMPLE (replace me): Which planet is known as the Red Planet?",
         "options": ["Venus", "Mars", "Jupiter", "Saturn"], "answer": "Mars", "explanation": "Mars looks red due to iron oxide."},
        {"exam": "SSC CGL", "subject": "Quantitative Aptitude", "year": "2021", "question": "SAMPLE (replace me): 15% of 200 = ?",
         "options": ["20", "25", "30", "35"], "answer": "C", "explanation": "0.15 x 200 = 30. 'answer' can be the option text or its letter A-D."},
    ],
    ensure_ascii=False,
    indent=2,
)


def normalize_pyq(items):
    out = []
    if not isinstance(items, list):
        return out
    for it in items:
        try:
            opts = [str(o).strip() for o in it["options"] if str(o).strip()]
            ans = resolve_option(it.get("answer", it.get("correct", "")), opts)
            question = str(it["question"]).strip()
            if len(opts) < 2 or ans is None or not question:
                continue
            out.append(
                {
                    "exam": str(it.get("exam", "General All Exams")).strip() or "General All Exams",
                    "subject": str(it.get("subject", "General")).strip() or "General",
                    "year": str(it.get("year", "")).strip(),
                    "question": question,
                    "options": opts,
                    "answer": ans,
                    "explanation": str(it.get("explanation", "")).strip(),
                }
            )
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


def load_pyq_dataset():
    base = _load_pyq_file(PYQ_FILE, os.path.getmtime(PYQ_FILE)) if os.path.exists(PYQ_FILE) else []
    return list(base) + list(st.session_state.get("pyq_uploaded", []))


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
                "question": cell(r, "question"), "options": opts, "answer": cell(r, "answer"), "explanation": cell(r, "explanation"),
            }
        )
    return normalize_pyq(items)


def pyq_to_item(x):
    opts = list(x["options"])
    random.shuffle(opts)
    return {
        "type": "mcq", "question": x["question"], "options": opts, "answer": x["answer"], "answers": [], "accept": [],
        "explanation": x.get("explanation") or "Is sawal ka explanation dataset me nahi hai.",
        "hint": "", "topic": (x.get("subject") or "General")[:30], "level": 2,
        "src": f"{x['exam']} {x['year']}".strip(),
    }


def pick_from_pool(pool, n, exclude):
    fresh = [x for x in pool if x["question"].strip().lower() not in exclude]
    return [pyq_to_item(x) for x in random.sample(fresh, min(n, len(fresh)))]


def more_questions(n, avoid_texts):
    """Next n questions for the running quiz: unseen real PYQs first (if any), then AI for the rest."""
    m = st.session_state.meta
    pool = m.get("pyq_pool") or []
    got = pick_from_pool(pool, n, {t.strip().lower() for t in avoid_texts}) if pool else []
    need = n - len(got)
    if need > 0 and (not pool or m.get("pyq_fill_ai", True)):
        got += generate_with_progress(
            m.get("source", ""), need, m.get("difficulty", "Medium"), m.get("types", ["mcq"]),
            m.get("language", "English"), m.get("model", MODELS[0]), media=m.get("media"),
            avoid=list(avoid_texts) + [g["question"] for g in got], adaptive=m.get("adaptive", False), exam=m.get("exam"),
        )
    return got


HIST_KEYS = ("time", "topic", "difficulty", "score", "total", "marks", "max", "acc", "pct")


def restore_progress(data):
    ss = st.session_state
    if not isinstance(data, dict):
        raise ValueError("File ka format galat hai.")
    hist = []
    for h in data.get("history", []):
        if isinstance(h, dict) and all(k in h for k in HIST_KEYS):
            try:
                hist.append(
                    {
                        "time": str(h["time"]), "topic": str(h["topic"]), "difficulty": str(h["difficulty"]),
                        "score": int(h["score"]), "total": max(1, int(h["total"])), "marks": float(h["marks"]),
                        "max": float(h["max"]), "acc": int(h["acc"]), "pct": int(h["pct"]),
                    }
                )
            except Exception:
                continue
    bms = validate_and_shuffle(data.get("bookmarks", []), 2, False)
    ss.total_xp = max(0, int(data.get("xp", 0)))
    ss.history = hist[-200:]
    ss.bookmarks = {b["question"]: b for b in bms}
    return len(ss.history), len(ss.bookmarks)


def extend_quiz(n):
    """Append n fresh questions (no repeats) to the current quiz and resume from the first new one.
    Scores, accuracy, XP and history are recomputed for the whole quiz when it is finished again."""
    ss = st.session_state
    m = ss.meta
    new = more_questions(n, [q["question"] for q in ss.quiz])
    if not new:
        return 0

    # undo the previous "finish" so the extended quiz is counted once, as a whole
    if ss.result:
        ss.total_xp = max(0, ss.total_xp - ss.result["xp"])
        if ss.history:
            ss.history.pop()

    # whole-quiz timer: give the new batch its own proportional budget
    if m.get("quiz_limit"):
        per_q = m.get("quiz_per_q") or m["quiz_limit"] / max(len(ss.quiz), 1)
        m["quiz_per_q"] = per_q
        m["quiz_limit"] = max(30, round(per_q * len(new)))

    ss.elapsed_before += (ss.end_time or time.time()) - (ss.start_time or time.time())
    ss.start_time = time.time()
    start = len(ss.quiz)
    ss.quiz.extend(new)
    ss.idx = start
    ss.result = None
    ss.end_time = None
    ss.celebrated = False
    ss.study_plan = ""
    ss.quiz_time_up = False
    ss.q_key = None
    ss.stage = "quiz"
    return len(new)


def reset_all():
    st.session_state.update(fresh_run_state())
    st.session_state.stage = "setup"


def read_pdf(file, start_page, end_page):
    reader = PdfReader(file)
    text = ""
    for p in reader.pages[start_page - 1 : end_page]:
        t = p.extract_text()
        if t:
            text += t + "\n"
    return text, len(reader.pages)


def toggle_bookmark(q):
    bm = st.session_state.bookmarks
    if q["question"] in bm:
        bm.pop(q["question"], None)
    else:
        bm[q["question"]] = q


def current_choice(q, qid, i):
    s, t = st.session_state, q["type"]
    if t in ("mcq", "tf"):
        return s.get(f"radio_{qid}_{i}")
    if t == "multi":
        return [o for n, o in enumerate(q["options"]) if s.get(f"cb_{qid}_{i}_{n}")]
    if t == "blank":
        return s.get(f"txt_{qid}_{i}")
    return s.get(f"ta_{qid}_{i}")


def answer_widget(q, qid, i, locked, prev):
    t = q["type"]
    if t in ("mcq", "tf"):
        idx = q["options"].index(prev) if prev in q["options"] else None
        return st.radio("Apna answer chuno", q["options"], index=idx, key=f"radio_{qid}_{i}", disabled=locked, label_visibility="collapsed")
    if t == "multi":
        st.caption("Ek se zyada sahi options chuno")
        chosen = set(prev or [])
        sel = []
        for n, o in enumerate(q["options"]):
            if st.checkbox(o, value=(o in chosen), key=f"cb_{qid}_{i}_{n}", disabled=locked):
                sel.append(o)
        return sel
    if t == "blank":
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
            f"<td>{esc(correct_text(q))}</td><td style='color:{'#1FA67A' if ok else '#E5484D'}'>{'✔' if ok else '✘'}</td>"
            f"<td>{esc(q['explanation'])}</td></tr>"
        )
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>QuizForge Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 16px;color:#222}}
h1{{color:#4B3FD1}} table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:8px;font-size:14px;vertical-align:top}}
th{{background:#4B3FD1;color:#fff}} .s{{font-size:20px;margin:10px 0}}</style></head><body>
<h1>QuizForge · Result Report</h1>
<p>{esc(ss.meta.get('label', 'Quiz'))} · {esc(ss.meta.get('difficulty', ''))} · {datetime.now().strftime('%d %b %Y, %H:%M')}</p>
<p class="s"><b>Marks:</b> {fmt_marks(r['marks'])}/{fmt_marks(r['max_marks'])} &nbsp; <b>Accuracy:</b> {r['accuracy']}% &nbsp; <b>Correct:</b> {r['score']}/{r['total']} &nbsp; <b>XP:</b> {r['xp']} &nbsp; <b>Best streak:</b> {r['best_streak']}</p>
<table><tr><th>#</th><th>Question</th><th>Your answer</th><th>Correct</th><th></th><th>Explanation</th></tr>{rows}</table>
</body></html>"""


# ─────────────────────────────────────────────────────────────
# BROWSER LAYER: sound effects, text-to-speech, keyboard shortcuts
# (a small script is injected once into the parent page)
# ─────────────────────────────────────────────────────────────
QF_VERSION = 3
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

SPEAK_BTN_TEMPLATE = """<style>
body{margin:0;display:flex;gap:6px;font-family:'Plus Jakarta Sans',Arial,sans-serif}
button{flex:1;height:40px;border-radius:13px;border:1px solid __LINE__;background:__BG__;color:__FG__;font-weight:700;font-size:14px;cursor:pointer}
button:hover{border-color:#22D3EE}
#stop{flex:0 0 44px}
</style>
<button id="b" title="Sawal sunao (R)">🔊 Sunao</button><button id="stop" title="Roko">⏹</button>
<script>
var T=__TEXT__;
document.getElementById('b').onclick=function(){var q=window.parent.qf;if(q){q.cur={text:T};q.speakCur();}};
document.getElementById('stop').onclick=function(){var s=window.parent.speechSynthesis;if(s)s.cancel();};
</script>"""


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
    code = SPEAK_BTN_TEMPLATE.replace("__TEXT__", json.dumps(text))
    for k, v in colors.items():
        code = code.replace(k, v)
    components.html(code, height=42)


# ─────────────────────────────────────────────────────────────
# COUNTDOWN (auto-refreshing fragment, Streamlit ≥ 1.37)
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
        st.progress(max(left / total_secs, 0.0), text=f"⏳ Quiz ka time bacha: {m:02d}:{sec:02d}")
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
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    lvl = level_of(st.session_state.total_xp)
    st.markdown(f"### 🎖️ Level {lvl}")
    st.progress((st.session_state.total_xp % 100) / 100, text=f"{st.session_state.total_xp} XP · agle level tak {100 - st.session_state.total_xp % 100}")

    st.markdown("### ⚙️ Quiz Settings")
    num_questions = st.slider("Questions", 3, 50, 5, help="10 se zyada sawal batches me bante hain, thoda time lag sakta hai.")
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    adaptive = st.toggle("🎚️ Adaptive difficulty", value=False, help="Sahi karte jao to sawal mushkil, galat par aasaan hote jayenge.")
    type_sel = st.multiselect("Question types", list(TYPE_MAP.keys()), default=["Multiple Choice", "True / False"])
    type_keys = [TYPE_MAP[x] for x in type_sel] or ["mcq"]
    language = st.selectbox("Language", ["English", "Hinglish", "Hindi"])
    mode = st.radio(
        "Mode",
        ["Practice", "Exam", "Survival"],
        help="Practice: har sawal ke baad turant answer.\nExam: result end me.\nSurvival: sirf 3 lives — 3 galat answer par game over!",
    )
    st.markdown("**⏱️ Timer**")
    timer_mode = st.selectbox("Timer type", ["Off", "Har sawal par", "Poore quiz ka"], label_visibility="collapsed")
    time_limit = quiz_limit = 0
    if timer_mode == "Har sawal par":
        pick = st.selectbox("Seconds per sawal", [10, 15, 20, 30, 45, 60, 90, 120, "Custom"], index=3)
        time_limit = int(st.number_input("Custom seconds", 5, 600, 30, 5)) if pick == "Custom" else int(pick)
        st.caption("Time khatam hote hi answer auto-submit ho jata hai.")
    elif timer_mode == "Poore quiz ka":
        pick = st.selectbox("Minutes (poore quiz ke)", [5, 10, 15, 20, 30, 45, 60, 90, "Custom"], index=1)
        mins = int(st.number_input("Custom minutes", 1, 180, 10, 1)) if pick == "Custom" else int(pick)
        quiz_limit = mins * 60
        st.caption(f"≈ {quiz_limit / max(num_questions, 1):.0f} sec per sawal. Time khatam to quiz apne aap submit.")
    if (time_limit or quiz_limit) and countdown is None:
        st.warning("Timer ke liye Streamlit ≥ 1.37 chahiye.")

    st.markdown("**🎯 Marking**")
    marks_correct = float(st.selectbox("Marks per sahi answer", [1, 2, 4, 5], index=0))
    neg_label = st.selectbox(
        "Negative marking (galat par)",
        ["Nahi", "¼ (−0.25)", "⅓ (−0.33)", "½ (−0.5)", "Full (−1)"],
        help="Galat answer par sahi-marks ka itna hissa katega. Skip par 0. Short answer me partial marks milte hain, negative nahi.",
    )
    neg_frac = {"Nahi": 0.0, "¼ (−0.25)": 0.25, "⅓ (−0.33)": 1 / 3, "½ (−0.5)": 0.5, "Full (−1)": 1.0}[neg_label]
    st.caption(f"+{fmt_marks(marks_correct)} sahi · −{fmt_marks(marks_correct * neg_frac)} galat · 0 skip")

    with st.expander("🔊 Awaaz & Look"):
        sound_on = st.toggle("Sound effects", value=True, key="sound_on")
        auto_read = st.toggle("Sawal khud padhkar sunao", value=False, key="auto_read", help="Agar awaaz na aaye to pehle page par ek click karo ya 🔊 button dabao.")
        tts_rate = st.slider("Bolne ki speed", 0.6, 1.4, 1.0, 0.1, key="tts_rate")
        st.toggle("☀️ Light mode", value=False, key="light")
    with st.expander("Advanced"):
        model = st.selectbox("AI model", MODELS, help="120b = sabse accurate. 8b-instant = sabse fast.")

    st.divider()
    nb = len(st.session_state.bookmarks)
    st.markdown("### 🔖 Saved questions")
    if nb:
        st.caption(f"{nb} question(s) saved")
        if st.session_state.stage != "quiz" and st.button("📇 Flashcards se padho", use_container_width=True):
            st.session_state.flash_cards = list(st.session_state.bookmarks.values())
            st.session_state.flash_i = 0
            st.session_state.flash_show = False
            st.session_state.flash_return = st.session_state.stage
            st.session_state.stage = "flash"
            st.rerun()
    else:
        st.caption("Quiz ke dauran 🔖 dabao, sawal yahan save ho jayega.")

    st.divider()
    st.markdown("### 🏆 Meri History")
    if st.session_state.history:
        for h in reversed(st.session_state.history[-6:]):
            st.markdown(
                f"**{esc(h['topic'])[:28]}**  \n{fmt_marks(h['marks'])}/{fmt_marks(h['max'])} marks · {h['acc']}% acc · {h['difficulty']}  \n"
                f"<small style='opacity:.6'>{h['time']}</small>",
                unsafe_allow_html=True,
            )
        st.caption(f"⭐ Best score: {max(h['pct'] for h in st.session_state.history)}%")
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Abhi koi quiz nahi diya. Pehla quiz banao!")

    st.divider()
    st.markdown("### 💾 Progress backup")
    st.caption("Login abhi nahi hai — apna XP, history aur saved questions file me save karo aur kabhi bhi wapas load karo.")
    _backup = json.dumps(
        {"v": 1, "xp": st.session_state.total_xp, "history": st.session_state.history, "bookmarks": list(st.session_state.bookmarks.values())},
        ensure_ascii=False,
    )
    st.download_button("⬇️ Progress save karo", _backup.encode("utf-8"), file_name="quizforge_progress.json", mime="application/json", use_container_width=True)
    _up = st.file_uploader("Progress load karo", type=["json"], key="prog_up")
    if _up is not None:
        _sig = (_up.name, _up.size)
        if st.session_state.get("_prog_sig") != _sig:
            try:
                _nh, _nb = restore_progress(json.loads(_up.getvalue().decode("utf-8-sig")))
                st.session_state["_prog_sig"] = _sig
                st.session_state["_prog_msg"] = f"✅ {_nh} quiz history aur {_nb} saved sawal wapas aa gaye."
                st.rerun()
            except Exception as e:
                st.error(f"Load nahi hua: {e}")
    if st.session_state.get("_prog_msg"):
        st.success(st.session_state["_prog_msg"])

# ─────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────
_order = {"setup": 0, "quiz": 1, "result": 2}
_cur = _order.get(st.session_state.stage, -1)
_steps = ""
for n, name in enumerate(["Content chuno", "Quiz khelo", "Result dekho"]):
    cls = "on" if n == _cur else ("done" if 0 <= _cur and n < _cur else "")
    _steps += f"<span class='qf-step {cls}'>{n + 1} · {name}</span>"

st.markdown(
    f"""
<div class="qf-hero">
  <div class="qf-title qf-display">QuizForge</div>
  <div class="qf-sub">Topic, PDF ya notes ki photo do — AI turant quiz banata hai. Awaaz, timer, lives, XP aur badges ke saath seekho.</div>
  <div class="qf-steps">{_steps}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════
# STAGE · SETUP
# ═════════════════════════════════════════════════════════════
def base_meta(cfg, label, source, media=None, **extra):
    m = {
        "label": label, "difficulty": cfg["difficulty"], "mode": cfg["mode"], "source": source, "media": media,
        "types": cfg["type_keys"], "adaptive": cfg["adaptive"], "language": cfg["language"], "model": cfg["model"],
        "time_limit": cfg["time_limit"], "quiz_limit": cfg["quiz_limit"], "marks": cfg["marks"], "neg": cfg["neg"],
    }
    m.update(extra)
    return m


def launch_quiz(input_text, label, cfg, media=None):
    with st.spinner("AI sawal bana raha hai…"):
        try:
            quiz = generate_with_progress(
                input_text, cfg["num_questions"], cfg["difficulty"], cfg["type_keys"], cfg["language"], cfg["model"],
                media=media, adaptive=cfg["adaptive"],
            )
            if not quiz:
                st.error("Valid sawal nahi ban paye. Dobara try karo.")
                return
            start_quiz(quiz, base_meta(cfg, label, input_text, media))
            st.session_state["_picked"] = ""
            st.rerun()
        except json.JSONDecodeError:
            st.error("AI ka response samajh nahi aaya. Dobara try karo ya doosra model chuno.")
        except Exception as e:
            st.error(friendly_error(e))


# ── TAB 1 · QUIZ ARENA ───────────────────────────────────────
def render_quiz_tab(cfg):
    with st.container(key="srcpick"):
        source = st.radio("Content kahan se aayega?", ["💡 Topic", "📄 PDF", "🖼️ Photo / Camera", "📝 Notes"], horizontal=True)

    input_text, label, media = "", "", None

    with st.container(key="panel"):
        if source.startswith("💡"):
            topic = st.text_input("Kis topic par quiz chahiye?", placeholder="e.g. Machine Learning basics, Indian Constitution, Python lists…")
            st.caption("Quick picks")
            cols = st.columns(4)
            for c, pick in zip(cols, ["Python Basics", "World History", "Human Biology", "Indian Economy"]):
                if c.button(pick, use_container_width=True, key=f"pick_{pick}"):
                    st.session_state["_picked"] = pick
                    st.rerun()
            if st.session_state.get("_picked") and not topic:
                topic = st.session_state["_picked"]
                st.info(f"Selected topic: **{topic}**")
            if topic.strip():
                input_text = f"Topic: {topic.strip()}\nUse your own knowledge to cover this topic accurately."
                label = topic.strip()

        elif source.startswith("📄"):
            up = st.file_uploader("PDF upload karo", type=["pdf"])
            if up is not None:
                try:
                    _, total_pages = read_pdf(up, 1, 1)
                    up.seek(0)
                    rng = st.slider("Page range", 1, total_pages, (1, min(total_pages, 10))) if total_pages > 1 else (1, 1)
                    pdf_text, _ = read_pdf(up, rng[0], rng[1])
                    if pdf_text.strip():
                        st.success(f"✅ {rng[1] - rng[0] + 1} page(s) padhe · {len(pdf_text):,} characters")
                        if len(pdf_text) > MAX_CHARS:
                            st.warning(f"Text lamba hai — pehle {MAX_CHARS:,} characters use honge. Page range chhota karo.")
                        input_text, label = pdf_text, f"PDF: {up.name}"
                    else:
                        st.error("Is PDF se text nahi nikla (scanned lagta hai). Uske page ki **photo** lekar try karo.")
                except Exception as e:
                    st.error(f"PDF read nahi ho paya: {e}")

        elif source.startswith("🖼️"):
            st.caption("Photo upload karo ya camera se seedha click karo.")
            photo_mode = st.radio("Photo mode", ["📁 Upload File", "📸 Live Camera Click"], horizontal=True, key="quiz_photo_mode")
            mf = (
                st.file_uploader("Photo upload karo", type=["png", "jpg", "jpeg", "webp"], key="media_up")
                if photo_mode == "📁 Upload File"
                else st.camera_input("Live photo click karo", key="quiz_cam")
            )
            if mf is not None:
                data = mf.getvalue()
                if len(data) > MAX_IMG_BYTES:
                    st.error("Photo 3 MB se badi hai. Chhoti ya compress ki hui photo use karo.")
                else:
                    st.image(data, caption="Selected photo", use_container_width=True)
                    media = {"bytes": data, "mime": getattr(mf, "type", None) or "image/jpeg"}
                    input_text, label = "(attached image)", f"Photo: {getattr(mf, 'name', 'Camera picture')}"

        else:
            pasted = st.text_area("Apne notes / article yahan paste karo", height=200, placeholder="Chapter ka text, notes, ya koi bhi article…")
            if pasted.strip():
                st.caption(f"{len(pasted):,} characters")
                input_text, label = pasted, "Pasted notes"

    st.write("")
    if st.button("✨ Quiz banao", type="primary", use_container_width=True):
        if not input_text.strip():
            st.warning("Pehle topic likho, photo upload/click karo ya notes paste karo.")
        else:
            launch_quiz(input_text, label, cfg, media)


# ── TAB 2 · GOVT EXAM PYQ ────────────────────────────────────
def render_pyq_tab(cfg):
    ss = st.session_state
    st.markdown("### 🏛️ Govt Exam PYQ Practice")
    st.caption(
        "Apne dataset ke **asli purane sawal** (📜 tag ke saath) ya AI ke **exam-pattern practice sawal**. "
        "AI ke sawal asli paper ke nahi hote — dono ko alag dikhaya jata hai."
    )
    dataset = load_pyq_dataset()

    with st.container(key="panel_pyq"):
        exam = st.selectbox("Target exam", EXAM_LIST, key="pyq_exam")
        known = sorted({q["subject"] for q in dataset if q["exam"] == exam})
        subjects = ["All subjects"] + sorted(set(EXAM_SUBJECTS.get(exam, [])) | set(known))
        subject = st.selectbox("Subject", subjects, key=f"pyq_subject_{exam}")
        pool_all = [q for q in dataset if q["exam"] == exam and (subject == "All subjects" or q["subject"] == subject)]
        years = sorted({q["year"] for q in pool_all if q["year"]}, reverse=True)
        sel_years = st.multiselect("Year (optional)", years, key=f"pyq_years_{exam}_{subject}") if years else []
        pool = [q for q in pool_all if not sel_years or q["year"] in sel_years]

        if pool:
            st.success(f"✅ Tumhare dataset me {len(pool)} asli PYQ mile.")
        else:
            st.info("Is filter ke liye dataset me PYQ nahi hain — AI exam-pattern wale practice sawal banayega (asli paper ke nahi).")
        fill_ai = st.toggle("Dataset me kam pade to AI se bharo", value=True, key="pyq_fill") if pool else True

        preset = EXAM_PRESETS.get(exam)
        use_pattern = False
        if preset:
            use_pattern = st.toggle("📝 Full mock test pattern", key="pyq_pattern", help="Exam jaisa timer, sawal ginti aur marking.")
            if use_pattern:
                st.caption(
                    f"{preset['n']} sawal · {preset['minutes']} min · +{fmt_marks(preset['marks'])} sahi · "
                    f"−{fmt_marks(preset['marks'] * preset['neg'])} galat. ⚠️ Pattern approximate hai — official notification se confirm karo. "
                    "100+ sawal me AI ko kuch minute lag sakte hain."
                )

    with st.expander("➕ Apna PYQ dataset jodo (JSON / CSV)"):
        st.caption(
            "Asli PYQ ke liye apna dataset do. Har sawal me: exam, subject, year, question, options, answer (text ya A-D), explanation. "
            "`exam` ka naam upar ki list jaisa hi likho (jaise `SSC CGL`). Hamesha ke liye rakhna ho to file ko repo me `pyq_data.json` naam se daalo."
        )
        st.download_button("📄 Template (JSON)", PYQ_TEMPLATE.encode("utf-8"), file_name="pyq_template.json", mime="application/json")
        up = st.file_uploader("PYQ file", type=["json", "csv"], key="pyq_up")
        if up is not None:
            sig = (up.name, up.size)
            if ss.get("_pyq_sig") != sig:
                try:
                    items = parse_pyq_upload(up)
                    have = {q["question"].strip().lower() for q in ss.pyq_uploaded}
                    fresh = [q for q in items if q["question"].strip().lower() not in have]
                    ss.pyq_uploaded += fresh
                    ss["_pyq_sig"] = sig
                    ss["_pyq_msg"] = f"✅ {len(fresh)} sawal jude ({len(items) - len(fresh)} duplicate chhode)."
                    st.rerun()
                except Exception as e:
                    st.error(f"File padh nahi paya: {e}")
        if ss.get("_pyq_msg"):
            st.success(ss["_pyq_msg"])
        if ss.pyq_uploaded:
            st.caption(f"Is session me {len(ss.pyq_uploaded)} uploaded PYQ hain.")
            if st.button("🗑️ Uploaded PYQ hatao", key="pyq_clear"):
                ss.pyq_uploaded = []
                ss["_pyq_sig"] = None
                ss["_pyq_msg"] = ""
                st.rerun()

    st.write("")
    if st.button(f"🚀 {exam} practice shuru karo", type="primary", use_container_width=True, key="btn_start_pyq"):
        n = preset["n"] if (preset and use_pattern) else cfg["num_questions"]
        label_exam = exam if subject == "All subjects" else f"{exam} · {subject}"
        subj_txt = "mixed subjects of the syllabus" if subject == "All subjects" else subject
        src = f"Exam: {exam}\nSubject: {subj_txt}\nCreate practice questions matching the real exam pattern."
        quiz = [pyq_to_item(x) for x in random.sample(pool, min(n, len(pool)))] if pool else []
        need = n - len(quiz)
        if need > 0 and (not pool or fill_ai):
            with st.spinner("AI exam-pattern sawal bana raha hai…"):
                try:
                    quiz += generate_with_progress(
                        src, need, cfg["difficulty"], ["mcq"], cfg["language"], cfg["model"],
                        avoid=[q["question"] for q in quiz], adaptive=False, exam=label_exam,
                    )
                except Exception as e:
                    if quiz:
                        st.warning(f"AI se baaki sawal nahi ban paye ({friendly_error(e)}). Dataset ke {len(quiz)} sawal se shuru kar rahe hain.")
                    else:
                        st.error(friendly_error(e))
                        return
        if not quiz:
            st.error("Is filter par koi sawal nahi bana. Filter badlo ya dobara try karo.")
            return
        random.shuffle(quiz)
        mock = bool(preset and use_pattern)
        meta = base_meta(
            cfg, f"{label_exam} · {'Mock' if mock else 'PYQ'}", src, None,
            types=["mcq"], adaptive=False, exam=label_exam, pyq_pool=pool, pyq_fill_ai=fill_ai,
            mode="Exam" if mock else cfg["mode"],
            marks=preset["marks"] if mock else cfg["marks"], neg=preset["neg"] if mock else cfg["neg"],
            time_limit=0 if mock else cfg["time_limit"], quiz_limit=preset["minutes"] * 60 if mock else cfg["quiz_limit"],
        )
        start_quiz(quiz, meta)
        st.rerun()


# ── TAB 3 · DOUBT SOLVER (chat with follow-ups) ──────────────
DEPTH_RULES = {
    "Step-by-step": "Give a clear step-by-step solution, then a short concept explanation.",
    "Quick answer": "Give the final answer first in 1-2 lines, then a brief reason (max 5 lines).",
    "ELI5 (bahut simple)": "Explain like I am 12: very simple words, one everyday analogy, no jargon.",
    "Exam-ready notes": "Give crisp exam-ready notes: definition, key formulae/points, one example, common mistakes.",
}
LANG_RULES = {
    "Simple English": "very simple, clear English",
    "Hinglish": "Hinglish (Hindi written in Roman script, mixed with common English words)",
    "Hindi": "Hindi in Devanagari script",
}


def doubt_system_prompt(lang, depth):
    return (
        f"You are a patient, friendly tutor. Answer in {LANG_RULES[lang]}. {DEPTH_RULES[depth]} "
        "Use Markdown and short sentences; show calculations clearly. If the question is ambiguous or the photo is unreadable, "
        "say so and state your assumption. End with '**Yaad rakho:**' and 2-3 bullets."
    )


def doubt_llm_messages(thread, system_prompt, with_image):
    msgs = [{"role": "system", "content": system_prompt}]
    for n, t in enumerate(thread):
        if n == 0 and t["role"] == "user" and t.get("image"):
            if with_image:
                b64 = base64.b64encode(t["image"]["bytes"]).decode()
                msgs.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": t["content"] or "Solve and explain this question."},
                            {"type": "image_url", "image_url": {"url": f"data:{t['image']['mime']};base64,{b64}"}},
                        ],
                    }
                )
            else:
                msgs.append({"role": "user", "content": (t["content"] or "Question from a photo") + " (the photo was shared earlier; see the solution below)"})
        else:
            msgs.append({"role": t["role"], "content": t["content"]})
    return msgs


def render_doubt_tab(cfg):
    ss = st.session_state
    st.markdown("### 🔍 AI Doubt Solver")
    st.caption("Doubt poochho (text, photo, camera ya PDF). Jawab word-by-word aata hai, aur tum follow-up sawal bhi pooch sakte ho.")
    thread = ss.doubt_thread

    if not thread:
        with st.container(key="panel_doubt"):
            c1, c2 = st.columns(2)
            lang_opts = list(LANG_RULES.keys())
            d_lang = c1.selectbox("Jawab ki bhasha", lang_opts, index={"English": 0, "Hinglish": 1, "Hindi": 2}.get(cfg["language"], 0), key="d_lang")
            d_depth = c2.selectbox("Style", list(DEPTH_RULES.keys()), key="d_depth")
            src = st.radio("Query type", ["📝 Text", "🖼️ Photo / Camera", "📄 PDF"], horizontal=True, key="d_src")
            q_text, d_media = "", None

            if src.startswith("📝"):
                q_text = st.text_area("Apna doubt yahan likho", height=140, placeholder="e.g. Binary Search Tree me insertion kaise hota hai? Example ke saath samjhao.", key="d_txt")
            elif src.startswith("🖼️"):
                mode_p = st.radio("Photo source", ["📁 Upload File", "📸 Live Camera Click"], horizontal=True, key="doubt_photo_mode")
                d_file = (
                    st.file_uploader("Photo upload karo", type=["png", "jpg", "jpeg", "webp"], key="d_img")
                    if mode_p == "📁 Upload File"
                    else st.camera_input("Question ki photo click karo", key="d_cam")
                )
                if d_file is not None:
                    data = d_file.getvalue()
                    if len(data) > MAX_IMG_BYTES:
                        st.error("Photo 3 MB se badi hai. Chhoti photo use karo.")
                    else:
                        st.image(data, caption="Question photo", use_container_width=True)
                        d_media = {"bytes": data, "mime": getattr(d_file, "type", None) or "image/jpeg"}
                q_text = st.text_input("Koi extra instruction? (optional)", placeholder="e.g. Sirf Q3 solve karo", key="d_img_txt")
            else:
                d_pdf = st.file_uploader("PDF upload karo", type=["pdf"], key="d_pdf")
                extra = st.text_input("PDF me se kya poochna hai?", placeholder="e.g. Is chapter ka summary do", key="d_pdf_txt")
                if d_pdf is not None:
                    try:
                        pdf_text, _ = read_pdf(d_pdf, 1, 5)
                        if pdf_text.strip():
                            st.success("PDF ke pehle 5 pages load ho gaye.")
                            q_text = f"Document text:\n{pdf_text[:MAX_CHARS]}\n\nRequest: {extra or 'Explain the key ideas simply.'}"
                        else:
                            st.error("PDF se text nahi nikla. Page ki photo upload karo.")
                    except Exception as e:
                        st.error(f"PDF read error: {e}")

        st.write("")
        if st.button("💡 Samjhao", type="primary", use_container_width=True, key="btn_solve_doubt"):
            if not q_text.strip() and not d_media:
                st.warning("Pehle doubt likho ya photo do.")
            else:
                ss.doubt_thread = [{"role": "user", "content": q_text.strip(), "image": d_media}]
                ss.doubt_opts = {"lang": d_lang, "depth": d_depth}
                ss.doubt_pending = True
                st.rerun()
        return

    # ── conversation view ──
    for t in thread:
        with st.chat_message(t["role"]):
            if t.get("image"):
                st.image(t["image"]["bytes"], width=280)
            st.markdown(t["content"] or "📷 *Photo se doubt*")

    opts = ss.doubt_opts or {"lang": "Simple English", "depth": "Step-by-step"}
    if ss.doubt_pending:
        use_vision = len(thread) == 1 and bool(thread[0].get("image"))
        msgs = doubt_llm_messages(thread, doubt_system_prompt(opts["lang"], opts["depth"]), use_vision)
        with st.chat_message("assistant"):
            try:
                text = st.write_stream(llm_stream(msgs, VISION_MODEL if use_vision else cfg["model"]))
                text = "".join(text) if isinstance(text, list) else str(text)
                if text.strip():
                    thread.append({"role": "assistant", "content": text})
            except Exception as e:
                st.error(friendly_error(e))
        ss.doubt_pending = False

    if thread and thread[-1]["role"] == "user":
        if st.button("🔁 Jawab dobara generate karo", key="d_retry"):
            ss.doubt_pending = True
            st.rerun()

    with st.form("doubt_follow", clear_on_submit=True):
        fu = st.text_input("Follow-up poochho", placeholder="e.g. Ek aur example se samjhao / Is step me ye kyun hua?")
        sent = st.form_submit_button("Bhejo ➤")
    if sent and fu.strip():
        thread.append({"role": "user", "content": fu.strip()})
        ss.doubt_pending = True
        st.rerun()

    a1, a2, a3 = st.columns(3)
    if a1.button("🧹 Naya doubt", use_container_width=True, key="d_new"):
        ss.doubt_thread = []
        ss.doubt_pending = False
        st.rerun()
    can_quiz = any(t["role"] == "assistant" for t in thread)
    if a2.button("📝 Is par quiz banao", use_container_width=True, disabled=not can_quiz, key="d_quiz"):
        transcript = "\n\n".join(t["content"] for t in thread if t["content"])[-MAX_CHARS:]
        launch_quiz(transcript, "Doubt: " + (thread[0]["content"] or "photo")[:40], cfg)
    md = "\n\n".join(f"**{'Tum' if t['role'] == 'user' else 'AI'}:** {t['content']}" for t in thread if t["content"])
    a3.download_button("⬇️ Notes (.md)", md.encode("utf-8"), file_name="doubt_notes.md", mime="text/markdown", use_container_width=True, key="d_dl")


# ═════════════════════════════════════════════════════════════
# STAGE · SETUP
# ═════════════════════════════════════════════════════════════
if st.session_state.stage == "setup":
    hist = st.session_state.history
    best_pct = max(h["pct"] for h in hist) if hist else 0
    st.markdown(
        f"""<div class="qf-tiles">
  <div class="qf-tile"><div class="v">{lvl}</div><div class="l">Level</div></div>
  <div class="qf-tile"><div class="v" style="color:#FFC857">{st.session_state.total_xp}</div><div class="l">Total XP</div></div>
  <div class="qf-tile"><div class="v">{len(hist)}</div><div class="l">Quizzes khele</div></div>
  <div class="qf-tile"><div class="v" style="color:#34D399">{best_pct}%</div><div class="l">Best score</div></div>
</div>""",
        unsafe_allow_html=True,
    )

    cfg = {
        "num_questions": num_questions, "difficulty": difficulty, "adaptive": adaptive, "type_keys": type_keys,
        "language": language, "mode": mode, "time_limit": time_limit, "quiz_limit": quiz_limit,
        "marks": marks_correct, "neg": neg_frac, "model": model,
    }
    tab_quiz, tab_pyq, tab_doubt = st.tabs(["🧠 Quiz Arena", "🏛️ Govt Exam PYQs", "🔍 Doubt Solver"])
    with tab_quiz:
        render_quiz_tab(cfg)
    with tab_pyq:
        render_pyq_tab(cfg)
    with tab_doubt:
        render_doubt_tab(cfg)

# ═════════════════════════════════════════════════════════════
# STAGE · QUIZ
# ═════════════════════════════════════════════════════════════
elif st.session_state.stage == "quiz":
    ss = st.session_state
    quiz = ss.quiz
    total = len(quiz)
    i = ss.idx
    q = quiz[i]
    qid = ss.quiz_id
    qtype_now = q["type"]
    choice_type = qtype_now in ("mcq", "tf", "multi")
    mode_now = ss.meta.get("mode", "Practice")
    survival = mode_now == "Survival"
    instant = mode_now in ("Practice", "Survival")
    limit = ss.meta.get("time_limit", 0)
    quiz_limit = ss.meta.get("quiz_limit", 0)
    is_adaptive = ss.meta.get("adaptive", False)
    lang, mdl = ss.meta.get("language", "English"), ss.meta.get("model", MODELS[0])

    if ss.q_key != (qid, i):
        ss.q_key = (qid, i)
        ss.q_start = time.time()

    answered = sum(1 for a in ss.answers.values() if a not in (None, "", []))
    top_l, top_r = st.columns([4, 1.4])
    top_l.progress(i / total, text=f"Question {i + 1} of {total}")
    if survival:
        left = lives_left()
        top_r.markdown(f"<div class='qf-hearts'>{'❤️' * left}{'🖤' * (LIVES - left)}</div>", unsafe_allow_html=True)
    else:
        running = f"🎯 {fmt_marks(sum(question_marks(j) for j in ss.locked))} · " if instant else ""
        top_r.markdown(f"<div style='text-align:right;font-weight:700'>{running}✅ {answered}/{total}</div>", unsafe_allow_html=True)

    locked = ss.locked.get(i, False)
    if limit and countdown is not None and not locked:
        countdown(limit, qid, i, total, instant)
    if quiz_limit and quiz_countdown is not None:
        quiz_countdown(quiz_limit, qid, i)

    type_label = {"mcq": "MCQ", "tf": "True/False", "multi": "Multi-select", "blank": "Fill in the blank", "short": "Short answer"}[qtype_now]
    lv_tag = f"<span class='qf-tag lv'>🎚️ {LEVEL_NAME[q['level']]}</span>" if is_adaptive else ""
    src_tag = f"<span class='qf-tag lv'>📜 {esc(q['src'])}</span>" if q.get("src") else ""
    _m, _pen = ss.meta.get("marks", 1.0), ss.meta.get("marks", 1.0) * ss.meta.get("neg", 0.0)
    mk_tag = f"<span class='qf-tag'>+{fmt_marks(_m)}" + (f" / −{fmt_marks(_pen)}" if _pen and qtype_now != "short" else "") + "</span>"
    st.markdown(
        f"""<div class="qf-qcard"><div class="qf-tags">{src_tag}{lv_tag}{mk_tag}<span class='qf-tag'>{type_label}</span><span class='qf-tag'>{esc(q['topic'])}</span></div>
        <div class="qf-qnum">Question {i + 1}</div>
        <div class="qf-qtext">{esc(q['question'])}</div></div>""",
        unsafe_allow_html=True,
    )

    h1, h2, h3, _sp = st.columns([1.35, 1.0, 1.35, 0.4])
    if q.get("hint") and not locked and not ss.hints_used.get(i):
        if h1.button("💡 Hint (−5 XP)", key=f"hint_{qid}_{i}", use_container_width=True):
            ss.hints_used[i] = True
            st.rerun()
    is_saved = q["question"] in ss.bookmarks
    if h2.button("📌 Saved" if is_saved else "🔖 Save", key=f"bm_{qid}_{i}", use_container_width=True):
        toggle_bookmark(q)
        st.rerun()
    with h3:
        speak_button(speech_text(q))
    if ss.hints_used.get(i) and q.get("hint"):
        st.markdown(f"<div class='qf-hint'>💡 {esc(q['hint'])}</div>", unsafe_allow_html=True)

    prev = ss.answers.get(i)
    with st.container(key="optbox"):
        choice = answer_widget(q, qid, i, locked, prev)

    if choice_type and not locked:
        extra = "<kbd>S</kbd> skip · " if instant else ""
        st.markdown(
            f"<div class='qf-kbd'>⌨️ <kbd>1</kbd>–<kbd>{len(q['options'])}</kbd> chuno · <kbd>Enter</kbd> aage · <kbd>H</kbd> hint · {extra}<kbd>R</kbd> sunao</div>",
            unsafe_allow_html=True,
        )

    game_over = survival and locked and lives_left() <= 0

    if instant and locked:
        st.markdown(feedback_html(i, q, ss.timed_out.get(i)), unsafe_allow_html=True)
        if game_over:
            st.error("💀 Saari lives khatam! Game over.")
        if st.button("🧠 Aur detail me samjhao", key=f"deep_{qid}_{i}"):
            with st.spinner("Soch raha hoon…"):
                try:
                    explain_more(q, user_text(i), lang, mdl)
                except Exception as e:
                    st.error(friendly_error(e))
        if q["question"] in ss.deep:
            st.info(ss.deep[q["question"]])

    st.write("")
    if not instant and not limit and not is_adaptive and total > 1:
        with st.expander("🧭 Question palette (kisi bhi sawal par jao)"):
            st.caption("✅ = answer diya hua · baaki khali. Neela button = abhi wala sawal.")
            per_row = 8
            for r0 in range(0, total, per_row):
                pal_cols = st.columns(per_row)
                for k, pc in enumerate(pal_cols):
                    j = r0 + k
                    if j >= total:
                        break
                    done_j = ss.answers.get(j) not in (None, "", [])
                    if pc.button(f"{'✅' if done_j else ''}{j + 1}", key=f"pal_{qid}_{j}", type="primary" if j == i else "secondary", use_container_width=True):
                        ss.answers[i] = norm_answer(choice)
                        ss.idx = j
                        st.rerun()

    b1, b2, b3 = st.columns(3)
    last = i == total - 1

    if not instant and not limit and not is_adaptive and i > 0:
        if b1.button("⬅️ Back", use_container_width=True):
            ss.answers[i] = norm_answer(choice)
            ss.idx -= 1
            st.rerun()

    if instant and not locked:
        if b2.button("Check answer", type="primary", use_container_width=True, disabled=(choice_type and not has_answer(choice))):
            ss.answers[i] = norm_answer(choice)
            if qtype_now == "short":
                with st.spinner("AI tumhara answer check kar raha hai…"):
                    grade_short(i)
            ss.locked[i] = True
            record_time(i)
            queue_sound("correct" if is_correct(i) else "wrong")
            st.rerun()
        if b3.button("Skip ⏭️", use_container_width=True):
            ss.answers[i] = None
            ss.locked[i] = True
            record_time(i)
            queue_sound("wrong")
            if last:
                finish_quiz()
            else:
                advance(i)
            st.rerun()
    else:
        btn_label = "Result dekho 💀" if game_over else ("Finish 🏁" if last else "Next ➡️")
        if b3.button(btn_label, type="primary", use_container_width=True):
            if not instant:
                ss.answers[i] = norm_answer(choice)
                record_time(i)
            if last or game_over:
                finish_quiz()
            else:
                advance(i)
            st.rerun()

    st.write("")
    if st.button("✖ Quiz chhodo"):
        reset_all()
        st.rerun()

# ═════════════════════════════════════════════════════════════
# STAGE · FLASHCARDS
# ═════════════════════════════════════════════════════════════
elif st.session_state.stage == "flash":
    ss = st.session_state
    cards = ss.flash_cards
    fi = ss.flash_i
    card = cards[fi]
    st.markdown("## 📇 Flashcards")
    st.progress((fi + 1) / len(cards), text=f"Card {fi + 1} of {len(cards)}")

    if ss.flash_show:
        st.markdown(
            f"<div class='qf-flash back'><div>✅ {esc(correct_text(card))}"
            f"<div style='font-family:Plus Jakarta Sans;font-size:.95rem;font-weight:400;color:var(--mute);margin-top:10px'>{esc(card['explanation'])}</div></div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<div class='qf-flash'>{esc(card['question'])}</div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    if f1.button("⬅️ Pichhla", use_container_width=True, disabled=fi == 0):
        ss.flash_i -= 1
        ss.flash_show = False
        st.rerun()
    if f2.button("🔄 Answer dikhao" if not ss.flash_show else "🔄 Sawal dikhao", type="primary", use_container_width=True):
        ss.flash_show = not ss.flash_show
        st.rerun()
    if f3.button("Agla ➡️", use_container_width=True, disabled=fi == len(cards) - 1):
        ss.flash_i += 1
        ss.flash_show = False
        st.rerun()

    st.write("")
    if st.button("← Wapas jao"):
        ss.stage = "result" if (ss.flash_return == "result" and ss.result) else "setup"
        st.rerun()

# ═════════════════════════════════════════════════════════════
# STAGE · RESULT
# ═════════════════════════════════════════════════════════════
else:
    ss = st.session_state
    quiz, answers, res = ss.quiz, ss.answers, ss.result
    total = len(quiz)
    lang, mdl = ss.meta.get("language", "English"), ss.meta.get("model", MODELS[0])

    correct_idx = [i for i in range(total) if is_correct(i)]
    skipped_idx = [i for i in range(total) if is_skipped(i)]
    wrong_idx = [i for i in range(total) if i not in correct_idx and i not in skipped_idx]
    pct, score = res["pct"], res["score"]
    elapsed = ss.elapsed_before + (ss.end_time or time.time()) - (ss.start_time or time.time())

    if pct >= 80:
        color, title, msg = "#34D399", "Zabardast! 🏆", "Topic par tumhari pakad mast hai."
    elif pct >= 50:
        color, title, msg = "#FFC857", "Achha try! 👍", "Thodi aur practice se top score aa jayega."
    else:
        color, title, msg = "#FB7185", "Keep going 💪", "Explanations padho aur dobara try karo."

    if not ss.celebrated:
        if pct >= 80:
            st.balloons()
        ss.celebrated = True

    st.markdown(f"## {title}")
    st.caption(msg)
    _m = ss.meta.get("marks", 1.0)
    st.caption(f"Marking: +{fmt_marks(_m)} sahi · −{fmt_marks(_m * ss.meta.get('neg', 0.0))} galat · 0 skip  |  Accuracy = sahi ÷ attempted")
    if res.get("time_up"):
        st.warning("⏰ Quiz ka total time khatam ho gaya — bache hue sawal skip maane gaye.")
    st.markdown(
        f"""
<div class="qf-ring" style="--t:{pct};--ring-color:{color}">
  <div class="qf-ring-in"><div class="big">{pct}%</div><div class="sm">{fmt_marks(res['marks'])} / {fmt_marks(res['max_marks'])} marks</div></div>
</div>
<div class="qf-tiles">
  <div class="qf-tile"><div class="v" style="color:#FFC857">{fmt_marks(res['marks'])}<span style="font-size:.9rem;opacity:.7"> / {fmt_marks(res['max_marks'])}</span></div><div class="l">Marks</div></div>
  <div class="qf-tile"><div class="v" style="color:#22D3EE">{res['accuracy']}%</div><div class="l">Accuracy</div></div>
  <div class="qf-tile"><div class="v">{res['attempted']}<span style="font-size:.9rem;opacity:.7"> / {total}</span></div><div class="l">Attempted</div></div>
  <div class="qf-tile"><div class="v" style="color:#FB7185">−{fmt_marks(res['neg_lost'])}</div><div class="l">Negative marks</div></div>
</div>
<div class="qf-tiles">
  <div class="qf-tile"><div class="v" style="color:#34D399">{score}</div><div class="l">Sahi</div></div>
  <div class="qf-tile"><div class="v" style="color:#FB7185">{len(wrong_idx)}</div><div class="l">Galat</div></div>
  <div class="qf-tile"><div class="v">{len(skipped_idx)}</div><div class="l">Skipped</div></div>
  <div class="qf-tile"><div class="v">{fmt_time(elapsed)}</div><div class="l">Total time</div></div>
  <div class="qf-tile"><div class="v" style="color:#FFC857">+{res['xp']}</div><div class="l">XP earned</div></div>
  <div class="qf-tile"><div class="v">{res['best_streak']}🔥</div><div class="l">Best streak</div></div>
  <div class="qf-tile"><div class="v">{res['avg_time']:.1f}s</div><div class="l">Avg / question</div></div>
  <div class="qf-tile"><div class="v">{res['hints']}</div><div class="l">Hints used</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    if res["leveled_up"]:
        st.success(f"🎉 Level up! Ab tum **Level {level_of(ss.total_xp)}** par ho.")
    if res["badges"]:
        st.markdown(
            "<div class='qf-badges'>" + "".join(f"<span class='qf-badge'>{esc(b)}</span>" for b in res["badges"]) + "</div>",
            unsafe_allow_html=True,
        )

    with st.container(key="morebox"):
        game_over_now = ss.meta.get("mode") == "Survival" and lives_left() <= 0
        st.markdown(f"**➕ Aur sawal chahiye?**  Abhi tak **{total}** sawal ho chuke hain.")
        mc1, mc2 = st.columns([1, 2])
        more_n = int(mc1.number_input("Kitne aur sawal?", 1, 50, 10, 1, key="more_n", label_visibility="collapsed"))
        can_more = (not game_over_now) and total + more_n <= MAX_TOTAL_Q
        if mc2.button(f"➕ {more_n} aur sawal jodo", type="primary", use_container_width=True, disabled=not can_more):
            with st.spinner("Naye sawal ban rahe hain…"):
                try:
                    if extend_quiz(more_n):
                        st.rerun()
                    else:
                        st.error("Naye sawal nahi ban paye. Dobara try karo.")
                except Exception as e:
                    st.error(friendly_error(e))
        note = "Naye sawal isi quiz me jud jayenge — marks, accuracy aur XP poore quiz ka milkar banega."
        if game_over_now:
            note = "Survival me saari lives khatam ho chuki hain, isliye aur sawal nahi jud sakte."
        elif total + more_n > MAX_TOTAL_Q:
            note = f"Ek quiz me maximum {MAX_TOTAL_Q} sawal ho sakte hain."
        st.caption(note)
    st.write("")

    a1, a2 = st.columns(2)
    if a1.button("🔁 Naya quiz", use_container_width=True, type="primary"):
        reset_all()
        st.rerun()
    if a2.button("🎯 Sirf galat dobara", use_container_width=True, disabled=not (wrong_idx or skipped_idx), help="Sirf galat/skip kiye hue sawal phir se solve karo"):
        redo = [reshuffle(quiz[i]) for i in wrong_idx + skipped_idx]
        meta = dict(ss.meta)
        meta["label"] = "Retry · " + meta.get("label", "Quiz")
        start_quiz(redo, meta)
        st.rerun()

    a3, a4 = st.columns(2)
    if a3.button("🔄 Wahi quiz phir se", use_container_width=True):
        start_quiz([reshuffle(q) for q in quiz], dict(ss.meta))
        st.rerun()
    if a4.button("🆕 Naye sawal (same source)", use_container_width=True):
        m = ss.meta
        with st.spinner("Naye sawal ban rahe hain…"):
            try:
                new_quiz = more_questions(len(quiz), [q["question"] for q in quiz])
                if new_quiz:
                    start_quiz(new_quiz, dict(m))
                    st.rerun()
                else:
                    st.error("Naye sawal nahi ban paye.")
            except Exception as e:
                st.error(friendly_error(e))

    if st.button("📇 Is quiz ke flashcards", use_container_width=True):
        ss.flash_cards = [dict(q) for q in quiz]
        ss.flash_i, ss.flash_show, ss.flash_return = 0, False, "result"
        ss.stage = "flash"
        st.rerun()

    st.markdown("### 📊 Topic-wise performance")
    topic_df = pd.DataFrame([{"Topic": q["topic"], "Correct": int(is_correct(i))} for i, q in enumerate(quiz)])
    agg = topic_df.groupby("Topic")["Correct"].agg(["sum", "count"]).reset_index()
    agg["Accuracy %"] = (agg["sum"] / agg["count"] * 100).round(0)
    if len(agg) > 1:
        st.bar_chart(agg.set_index("Topic")["Accuracy %"])
    weak = agg[agg["Accuracy %"] < 60]["Topic"].tolist()
    strong = agg[agg["Accuracy %"] >= 80]["Topic"].tolist()
    if strong:
        st.success("💪 Strong: " + ", ".join(strong))
    if weak:
        st.warning("📌 Revise karo: " + ", ".join(weak))

    if wrong_idx or skipped_idx:
        if st.button("🧭 AI study plan banao", use_container_width=True):
            with st.spinner("Study plan ban raha hai…"):
                try:
                    ss.study_plan = make_study_plan([quiz[i] for i in wrong_idx + skipped_idx], lang, mdl)
                except Exception as e:
                    st.error(friendly_error(e))
        if ss.study_plan:
            st.markdown(ss.study_plan)

    st.markdown("### 🔍 Review")
    for i, q in enumerate(quiz):
        icon = "✅" if is_correct(i) else ("⏭️" if is_skipped(i) else "❌")
        with st.expander(f"{icon}  Q{i + 1}. {q['question'][:90]}"):
            st.markdown(f"**{q['question']}**")
            sel = answers.get(i)
            if q["type"] in ("mcq", "tf"):
                for o in q["options"]:
                    if o == q["answer"]:
                        st.markdown(f"- ✅ **{o}**")
                    elif o == sel:
                        st.markdown(f"- ❌ ~~{o}~~ (tumhara answer)")
                    else:
                        st.markdown(f"- {o}")
            elif q["type"] == "multi":
                chosen = set(sel or [])
                for o in q["options"]:
                    right = o in q["answers"]
                    if right and o in chosen:
                        st.markdown(f"- ✅ **{o}**")
                    elif right:
                        st.markdown(f"- ✅ **{o}** (tumne miss kiya)")
                    elif o in chosen:
                        st.markdown(f"- ❌ ~~{o}~~ (galat chuna)")
                    else:
                        st.markdown(f"- {o}")
            else:
                st.markdown(f"**Tumhara answer:** {user_text(i)}")
                st.markdown(f"**Sahi answer:** {q['answer']}")
                if q["type"] == "short" and i in ss.grades:
                    g = ss.grades[i]
                    st.markdown(f"🧪 **AI score:** {g['score']:.1f}/1 — {g['feedback']}")
            if is_skipped(i):
                st.caption("Ye sawal skip hua / time khatam ho gaya / game over ho gaya.")
            _mk = question_marks(i)
            st.caption(f"🎯 Marks: {'+' if _mk > 0 else ''}{fmt_marks(_mk)}")
            st.info(f"💡 {q['explanation']}")
            c1, c2 = st.columns(2)
            if c1.button("🧠 Aur detail me samjhao", key=f"rv_deep_{ss.quiz_id}_{i}"):
                with st.spinner("Soch raha hoon…"):
                    try:
                        explain_more(q, user_text(i), lang, mdl)
                    except Exception as e:
                        st.error(friendly_error(e))
            saved = q["question"] in ss.bookmarks
            if c2.button("📌 Saved" if saved else "🔖 Save", key=f"rv_bm_{ss.quiz_id}_{i}"):
                toggle_bookmark(q)
                st.rerun()
            if q["question"] in ss.deep:
                st.markdown(ss.deep[q["question"]])

    st.markdown("### 📥 Download")
    df = pd.DataFrame(
        [
            {
                "No": i + 1,
                "Type": q["type"],
                "Topic": q["topic"],
                "Question": q["question"],
                "Options": " | ".join(q["options"]),
                "Your answer": user_text(i),
                "Correct answer": correct_text(q),
                "Result": "Correct" if is_correct(i) else "Wrong/Skipped",
                "Marks": question_marks(i),
                "Explanation": q["explanation"],
            }
            for i, q in enumerate(quiz)
        ]
    )
    d1, d2, d3 = st.columns(3)
    d1.download_button("Report (HTML)", build_report_html().encode("utf-8"), file_name="quiz_report.html", mime="text/html", use_container_width=True)
    d2.download_button("Results (CSV)", df.to_csv(index=False).encode("utf-8-sig"), file_name="quiz_results.csv", mime="text/csv", use_container_width=True)
    d3.download_button("Quiz (JSON)", json.dumps(quiz, ensure_ascii=False, indent=2).encode("utf-8"), file_name="quiz.json", mime="application/json", use_container_width=True)

# ─────────────────────────────────────────────────────────────
# Browser layer (sound / voice / shortcuts) — keep at the very end
# ─────────────────────────────────────────────────────────────
_run_lang = st.session_state.meta.get("language", language) if st.session_state.stage == "quiz" else language
render_browser_layer(
    sound_on=sound_on,
    tts_lang="hi-IN" if _run_lang == "Hindi" else "en-IN",
    tts_rate=tts_rate,
    auto_read=auto_read,
)
