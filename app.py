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
import streamlit as st

# Main screen par hi settings ka dropdown box
with st.expander("⚙️ Quiz Settings (Number of Questions & Difficulty)", expanded=True):
    num_questions = st.number_input("Kitne questions chahiye?", min_value=1, max_value=20, value=5)
    difficulty = st.selectbox("Difficulty level select karo", ["Easy", "Medium", "Hard"])

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
#MainMenu, footer, header[data-testid="stHeader"]{ visibility:hidden; height:0; }

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
.st-key-panel, .st-key-optbox{
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
        "grades": {}, "cur_level": 2, "result": None, "study_plan": "", "celebrated": False,
        "start_time": None, "end_time": None,
    }


GLOBAL_DEFAULTS = {
    "stage": "setup", "quiz_id": 0, "history": [], "meta": {}, "total_xp": 0, "bookmarks": {}, "deep": {},
    "flash_cards": [], "flash_i": 0, "flash_show": False, "flash_return": "setup",
    "q_key": None, "q_start": time.time(), "_picked": "",
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
def generate_quiz(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False):
    type_keys = [t for t in type_keys if t in TYPE_SPECS] or ["mcq"]
    shapes = "\n".join(f"- {t}: {TYPE_SPECS[t]}" for t in type_keys)
    level_rule = (
        '- Give each question a numeric "level": 1 (easy), 2 (medium) or 3 (hard), roughly a third each.'
        if adaptive
        else f'- Every question has "level": {DIFF_LEVEL[diff]}. Overall difficulty: {diff}.'
    )
    avoid_rule = ""
    if avoid:
        avoid_rule = "- Do NOT repeat or rephrase these earlier questions:\n  " + "\n  ".join(f"* {a}" for a in avoid[:30])
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


def compute_badges(pct, best_streak, avg_time, hints, diff, survival_win, n_types):
    badges = []
    if pct == 100:
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
    pct = round(correct / total * 100)
    avg_time = sum(ss.times.values()) / len(ss.times) if ss.times else 0
    hints = sum(1 for v in ss.hints_used.values() if v)
    survival_win = ss.meta.get("mode") == "Survival" and len(ss.locked) == total and lives_left() > 0
    n_types = len({q["type"] for q in quiz})

    old_level = level_of(ss.total_xp)
    ss.total_xp += xp
    ss.history.append(
        {"time": datetime.now().strftime("%d %b, %H:%M"), "topic": ss.meta.get("label", "Quiz"), "difficulty": diff, "score": correct, "total": total}
    )
    ss.result = {
        "score": correct, "total": total, "pct": pct, "xp": xp, "best_streak": best, "avg_time": avg_time, "hints": hints,
        "leveled_up": level_of(ss.total_xp) > old_level,
        "badges": compute_badges(pct, best, avg_time, hints, diff, survival_win, n_types),
    }
    queue_sound("win" if pct >= 50 else "lose")
    ss.stage = "result"


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
<p class="s"><b>Score:</b> {r['score']}/{r['total']} ({r['pct']}%) &nbsp; <b>XP:</b> {r['xp']} &nbsp; <b>Best streak:</b> {r['best_streak']}</p>
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


_fragment = getattr(st, "fragment", None)
countdown = _fragment(run_every=1)(_countdown) if _fragment else None

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    lvl = level_of(st.session_state.total_xp)
    st.markdown(f"### 🎖️ Level {lvl}")
    st.progress((st.session_state.total_xp % 100) / 100, text=f"{st.session_state.total_xp} XP · agle level tak {100 - st.session_state.total_xp % 100}")

    st.markdown("### ⚙️ Quiz Settings")
    num_questions = st.slider("Questions", 3, 20, 5)
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
    timer_opt = st.selectbox("Timer per question", ["Off", "15 sec", "30 sec", "60 sec"], help="Time khatam hote hi answer auto-submit.")
    time_limit = 0 if timer_opt == "Off" else int(timer_opt.split()[0])
    if time_limit and countdown is None:
        st.warning("Timer ke liye Streamlit ≥ 1.37 chahiye.")

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
            pct_h = round(h["score"] / h["total"] * 100)
            st.markdown(
                f"**{esc(h['topic'])[:28]}**  \n{h['score']}/{h['total']} · {pct_h}% · {h['difficulty']}  \n"
                f"<small style='opacity:.6'>{h['time']}</small>",
                unsafe_allow_html=True,
            )
        st.caption(f"⭐ Best score: {round(max(h['score'] / h['total'] for h in st.session_state.history) * 100)}%")
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Abhi koi quiz nahi diya. Pehla quiz banao!")

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
if st.session_state.stage == "setup":
    hist = st.session_state.history
    best_pct = round(max(h["score"] / h["total"] for h in hist) * 100) if hist else 0
    st.markdown(
        f"""<div class="qf-tiles">
  <div class="qf-tile"><div class="v">{lvl}</div><div class="l">Level</div></div>
  <div class="qf-tile"><div class="v" style="color:#FFC857">{st.session_state.total_xp}</div><div class="l">Total XP</div></div>
  <div class="qf-tile"><div class="v">{len(hist)}</div><div class="l">Quizzes khele</div></div>
  <div class="qf-tile"><div class="v" style="color:#34D399">{best_pct}%</div><div class="l">Best score</div></div>
</div>""",
        unsafe_allow_html=True,
    )

    with st.container(key="srcpick"):
        source = st.radio("Content kahan se aayega?", ["💡 Topic", "📄 PDF", "🖼️ Photo", "📝 Notes"], horizontal=True)

    input_text, label, media = "", "", None

    with st.container(key="panel"):
        if source.startswith("💡"):
            topic = st.text_input("Kis topic par quiz chahiye?", placeholder="e.g. Machine Learning basics, Indian Constitution, Python lists…")
            st.caption("Quick picks")
            cols = st.columns(4)
            for c, p in zip(cols, ["Python Basics", "World History", "Human Biology", "Indian Economy"]):
                if c.button(p, use_container_width=True, key=f"pick_{p}"):
                    st.session_state["_picked"] = p
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
                        st.error("Is PDF se text nahi nikla (scanned lagta hai). Uske page ki **photo** upload karke try karo.")
                except Exception as e:
                    st.error(f"PDF read nahi ho paya: {e}")

        elif source.startswith("🖼️"):
            st.caption("Notes / book page ki photo (PNG, JPG, WEBP, max 3 MB). AI ise seedha dekhkar padhega — handwriting bhi.")
            mf = st.file_uploader("Photo upload karo", type=["png", "jpg", "jpeg", "webp"], key="media_up")
            if mf is not None:
                data = mf.getvalue()
                if len(data) > MAX_IMG_BYTES:
                    st.error("Photo 3 MB se badi hai. Chhoti ya compress ki hui photo use karo.")
                else:
                    st.image(data, caption=mf.name, use_container_width=True)
                    media = {"bytes": data, "mime": mf.type or "image/jpeg"}
                    input_text, label = "(attached image)", f"Photo: {mf.name}"

        else:
            pasted = st.text_area("Apne notes / article yahan paste karo", height=200, placeholder="Chapter ka text, notes, ya koi bhi article…")
            if pasted.strip():
                st.caption(f"{len(pasted):,} characters")
                input_text, label = pasted, "Pasted notes"

    st.write("")
    if st.button("✨ Quiz banao", type="primary", use_container_width=True):
        if not input_text.strip():
            st.warning("Pehle topic likho, photo upload karo ya notes paste karo.")
        else:
            with st.spinner("AI sawal bana raha hai…"):
                try:
                    quiz = generate_quiz(input_text, num_questions, difficulty, type_keys, language, model, media=media, adaptive=adaptive)
                    if not quiz:
                        st.error("Valid sawal nahi ban paye. Dobara try karo.")
                    else:
                        start_quiz(
                            quiz,
                            {
                                "label": label, "difficulty": difficulty, "mode": mode, "source": input_text, "media": media,
                                "types": type_keys, "adaptive": adaptive, "language": language, "model": model, "time_limit": time_limit,
                            },
                        )
                        st.session_state["_picked"] = ""
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("AI ka response samajh nahi aaya. Dobara try karo ya doosra model chuno.")
                except Exception as e:
                    st.error(friendly_error(e))

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
        top_r.markdown(f"<div style='text-align:right;font-weight:700'>✅ {answered}/{total}</div>", unsafe_allow_html=True)

    locked = ss.locked.get(i, False)
    if limit and countdown is not None and not locked:
        countdown(limit, qid, i, total, instant)

    type_label = {"mcq": "MCQ", "tf": "True/False", "multi": "Multi-select", "blank": "Fill in the blank", "short": "Short answer"}[qtype_now]
    lv_tag = f"<span class='qf-tag lv'>🎚️ {LEVEL_NAME[q['level']]}</span>" if is_adaptive else ""
    st.markdown(
        f"""<div class="qf-qcard"><div class="qf-tags">{lv_tag}<span class='qf-tag'>{type_label}</span><span class='qf-tag'>{esc(q['topic'])}</span></div>
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
    elapsed = (ss.end_time or time.time()) - (ss.start_time or time.time())

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
    st.markdown(
        f"""
<div class="qf-ring" style="--t:{pct};--ring-color:{color}">
  <div class="qf-ring-in"><div class="big">{pct}%</div><div class="sm">{score} / {total}</div></div>
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
                new_quiz = generate_quiz(
                    m.get("source", ""), len(quiz), m.get("difficulty", "Medium"), m.get("types", ["mcq"]), lang, mdl,
                    media=m.get("media"), avoid=[q["question"] for q in quiz], adaptive=m.get("adaptive", False),
                )
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
