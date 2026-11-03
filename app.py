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

LOCALSTORAGE_JS = """
<script>
(function() {
    const savedLang = localStorage.getItem('app_ui_lang');
    if (savedLang) {
        // Sync language setting seamlessly
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

# ─────────────────────────────────────────────────────────────
# API KEY & GROQ CLIENT
# ─────────────────────────────────────────────────────────────
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
# SESSION STATE INITIALIZATION
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
    "user": None, "sb": None, "tokens": {}, "is_admin": False, "seen_local": {}, "bank_cache": {}, "otp": {},
}
for _k, _v in {**GLOBAL_DEFAULTS, **fresh_run_state()}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────
# HELPERS & UTILITIES
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
        return "Groq rate limit reached. Please wait 20-30 seconds or choose a smaller model."
    if "api key" in low or "401" in low or "invalid_api_key" in low:
        return "API key appears invalid. Please check `GROQ_API_KEY` in Secrets."
    if "model" in low and ("not found" in low or "decommissioned" in low or "does not exist" in low):
        return "This model is currently unavailable. Choose another model in Sidebar."
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
                "explanation": str(q.get("explanation", "")).strip() or "Explanation unavailable.",
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
            else:
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
        t += ". True or False?"
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
        f"- Write in the style, difficulty and syllabus of {exam} previous-year papers."
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

Allowed question types and their JSON shapes:
{shapes}

Every question object must ALSO contain: "explanation", "hint", "topic".

Rules:
{level_rule}
- Write questions, options, hints and explanations in: {i18n.QUIZ_LANG_OF.get(lang, 'English')}.
- Exactly one correct option for mcq/tf; multi needs 2-3 correct options out of 5.
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
            prog_txt = f"{min(len(quiz), num_q)} / {num_q} questions generated..."
            progress(min(len(quiz) / num_q, 1.0), prog_txt)
    return quiz[:num_q]

def generate_with_progress(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, exam=None):
    bar = st.progress(0.0, text="Generating questions...")
    def cb(frac, msg):
        bar.progress(min(max(frac, 0.0), 1.0), text=i18n.tr(msg))
    try:
        return generate_quiz_batched(text, num_q, diff, type_keys, lang, model, media, avoid, adaptive, progress=cb, exam=exam)
    finally:
        bar.empty()

# ─────────────────────────────────────────────────────────────
# AUTHENTICATION & DATABASE
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
    raise last or ValueError("Invalid OTP.")

def render_login(cm):
    ss = st.session_state
    sub_title = "Log in to preserve your history, XP and saved questions."
    st.markdown(
        f"""<div class="qf-hero"><div class="qf-title qf-display">{APP_NAME}</div>
<div class="qf-sub">{sub_title}</div></div>""",
        unsafe_allow_html=True,
    )
    otp = ss.get("otp") or {}
    with st.container(key="panel_login"):
        if not otp:
            ch_opts = ["📧 Email", "📱 Mobile number"]
            ch = st.radio("Login method", ch_opts, horizontal=True, key="login_ch")
            is_email = "Email" in ch
            raw = st.text_input(
                "Email address" if is_email else "Mobile number", key="login_id_email" if is_email else "login_id_phone",
                placeholder="you@example.com" if is_email else "98765 43210",
            )
            if st.button("📨 Send OTP", type="primary", use_container_width=True, key="otp_send_btn"):
                ident = (raw or "").strip().lower()
                if not ident or (is_email and not EMAIL_RE.match(ident)):
                    st.error("Please enter a valid email address.")
                else:
                    channel = "email" if is_email else "phone"
                    with st.spinner("Sending OTP..."):
                        try:
                            otp_send(channel, ident)
                            ss["otp"] = {"channel": channel, "ident": ident, "sent": time.time()}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            return False

        st.success(f"OTP sent to: **{otp['ident']}**")
        code = st.text_input("Enter OTP", max_chars=10, key="otp_code", placeholder="123456")
        c1, c2 = st.columns(2)
        if c1.button("✅ Verify", type="primary", use_container_width=True, key="otp_verify_btn"):
            token = re.sub(r"\s", "", code or "")
            if not token:
                st.warning("Please enter the OTP.")
            else:
                with st.spinner("Verifying..."):
                    try:
                        res = otp_verify(otp["channel"], otp["ident"], token)
                        ss["user"] = {"id": str(res.user.id)}
                        ss["otp"] = {}
                        return True
                    except Exception as e:
                        st.error(f"Verification error: {e}")
        if c2.button("🔁 Resend OTP", use_container_width=True, key="otp_resend_btn"):
            try:
                otp_send(otp["channel"], otp["ident"])
                st.success("New OTP sent.")
            except Exception as e:
                st.error(f"Error: {e}")
        if st.button("← Back", key="otp_back"):
            ss["otp"] = {}
            st.rerun()
    return False

def ensure_auth():
    ss = st.session_state
    if not AUTH_CONFIGURED or create_client is None:
        return None
    cm = None
    if stx is not None:
        try:
            cm = stx.CookieManager(key="qa_cm")
        except Exception:
            cm = None
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
# QUIZ STATE ENGINE
# ─────────────────────────────────────────────────────────────
def start_quiz(quiz, meta):
    st.session_state.update(fresh_run_state())
    st.session_state.update(
        quiz=quiz, quiz_id=st.session_state.quiz_id + 1, start_time=time.time(), stage="quiz", meta=meta, q_key=None
    )

def record_time(i):
    if i not in st.session_state.times:
        st.session_state.times[i] = time.time() - st.session_state.q_start

def advance(i):
    st.session_state.idx += 1

def finish_quiz():
    ss = st.session_state
    ss.end_time = time.time()
    correct = sum(1 for i in range(len(ss.quiz)) if is_correct(i))
    total = len(ss.quiz)
    pct = round((correct / total) * 100) if total else 0
    ss.result = {"score": correct, "total": total, "pct": pct, "xp": correct * 10}
    ss.stage = "result"

def read_pdf(file, start_page=1, end_page=10):
    reader = PdfReader(file)
    text = ""
    pages = min(end_page, len(reader.pages))
    for p in range(start_page - 1, pages):
        t = reader.pages[p].extract_text()
        if t:
            text += t + "\n"
    return text, len(reader.pages)

# ─────────────────────────────────────────────────────────────
# MAIN EXECUTION & SIDEBAR
# ─────────────────────────────────────────────────────────────
CM = ensure_auth()

i18n.init_ui_lang()

# ── SLEEK GLASS SIDEBAR ──
with st.sidebar:
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("### 🌐 Application Language")
    selected_lang_str = st.selectbox(
        "Select Language",
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
    st.markdown('</div>', unsafe_allow_html=True)

    lvl = level_of(st.session_state.total_xp)
    st.markdown(f'<div class="sidebar-card"><h3 style="margin-top:0;">🎖️ Level {lvl}</h3>', unsafe_allow_html=True)
    st.progress((st.session_state.total_xp % 100) / 100, text=f"{st.session_state.total_xp} Total XP")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Quiz Settings")
    num_questions = st.slider("Questions", 3, 50, 5)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    adaptive = st.toggle("🎚️ Adaptive difficulty", value=False)
    type_sel = st.multiselect("Question types", list(TYPE_MAP.keys()), default=["Multiple Choice", "True / False"])
    type_keys = [TYPE_MAP[x] for x in type_sel] or ["mcq"]
    mode = st.radio("Mode", ["Practice", "Exam", "Survival"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("### ⏱️ Timer & Marking")
    timer_mode = st.selectbox("Timer type", ["Off", "Per question", "Whole quiz"])
    time_limit = quiz_limit = 0
    if timer_mode == "Per question":
        time_limit = int(st.number_input("Seconds per question", 5, 300, 30))
    elif timer_mode == "Whole quiz":
        quiz_limit = int(st.number_input("Minutes (whole quiz)", 1, 180, 10)) * 60

    marks_correct = float(st.number_input("Marks per correct answer", 1.0, 10.0, 1.0))
    neg_frac = 0.25 if st.checkbox("Enable Negative Marking") else 0.0
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    with st.expander("🔊 Audio & Model Controls"):
        sound_on = st.toggle("Sound effects", value=True)
        auto_read = st.toggle("Auto-read questions", value=False)
        tts_rate = st.slider("Speaking speed", 0.6, 1.4, 1.0, 0.1)
        st.toggle("☀️ Light mode", value=False, key="light")
        model = st.selectbox("AI Model", MODELS)
    st.markdown('</div>', unsafe_allow_html=True)

cfg = {
    "num_questions": num_questions, "difficulty": difficulty, "adaptive": adaptive, "type_keys": type_keys,
    "language": i18n.cur(), "mode": mode, "time_limit": time_limit, "quiz_limit": quiz_limit,
    "marks": marks_correct, "neg": neg_frac, "model": model,
}

# ── HERO HEADER ──
st.markdown(
    theme.hero_html(APP_NAME, i18n.t("app_tag"), show_chips=True),
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────────────────────
# TAB NAVIGATION & FEATURES
# ─────────────────────────────────────────────────────────────
if st.session_state.stage == "setup":
    tab_quiz, tab_pyq, tab_doubt = st.tabs(["🧠 Quiz Arena", "🏛️ Govt Exam PYQs", "🔍 Doubt Solver"])
    
    with tab_quiz:
        st.markdown("### " + i18n.tr("🧠 Quiz Arena"))
        source = st.radio("Where will the content come from?", ["💡 Topic", "📄 PDF", "🖼️ Photo / Camera", "📝 Notes"], horizontal=True)
        
        input_text, label, media = "", "", None
        with st.container(key="panel"):
            if "Topic" in source:
                topic = st.text_input("Which topic do you want a quiz on?", placeholder="e.g. Machine Learning, Indian Constitution...")
                if topic.strip():
                    input_text, label = f"Topic: {topic.strip()}", topic.strip()
            elif "PDF" in source:
                up = st.file_uploader("Upload a PDF file", type=["pdf"])
                if up:
                    pdf_text, _ = read_pdf(up, 1, 10)
                    if pdf_text.strip():
                        input_text, label = pdf_text, f"PDF: {up.name}"
            elif "Photo" in source:
                photo_mode = st.radio("Photo mode", ["📁 Upload File", "📸 Live Camera Click"], horizontal=True)
                mf = st.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"]) if "Upload" in photo_mode else st.camera_input("Take a live photo")
                if mf:
                    data, mime = prepare_image(mf.getvalue())
                    media = {"bytes": data, "mime": mime}
                    input_text, label = "(attached image)", "Photo Quiz"
            else:
                pasted = st.text_area("Paste your notes / article here", height=150)
                if pasted.strip():
                    input_text, label = pasted, "Notes Quiz"

        if st.button("✨ Make quiz", type="primary", use_container_width=True):
            if not input_text.strip() and not media:
                st.warning("First write a topic, upload/click a photo or paste notes.")
            else:
                with st.spinner("AI is making questions…"):
                    try:
                        quiz = generate_with_progress(input_text, cfg["num_questions"], cfg["difficulty"], cfg["type_keys"], cfg["language"], cfg["model"], media=media, adaptive=cfg["adaptive"])
                        if quiz:
                            start_quiz(quiz, {"label": label, "difficulty": cfg["difficulty"], "mode": cfg["mode"], "source": input_text, "media": media, "types": cfg["type_keys"], "adaptive": cfg["adaptive"], "language": cfg["language"], "model": cfg["model"], "time_limit": cfg["time_limit"], "quiz_limit": cfg["quiz_limit"], "marks": cfg["marks"], "neg": cfg["neg"]})
                            st.rerun()
                        else:
                            st.error("Couldn't make valid questions. Please try again.")
                    except Exception as e:
                        st.error(friendly_error(e))

    with tab_pyq:
        st.markdown("### " + i18n.tr("🏛️ Govt & Entrance Exam Practice"))
        st.info("Select a government exam to practice authentic previous year questions.")

    # ── FULL FEATURE DOUBT SOLVER ──
    with tab_doubt:
        st.markdown("### " + i18n.tr("🔍 AI Doubt Solver"))
        st.caption("Ask your doubt via Text, Camera, Photo Upload or PDF Document.")
        
        doubt_src = st.radio(
            "How do you want to ask?",
            ["📝 Text", "📸 Live Camera", "🖼️ Photo Upload", "📄 PDF"],
            horizontal=True,
            key="doubt_source_radio"
        )
        
        q_text, d_media = "", None
        
        with st.container(key="panel_doubt"):
            if doubt_src.startswith("📝"):
                q_text = st.text_area("Write your doubt here", height=140, placeholder="e.g. Explain Binary Search Tree insertion with an example...", key="d_txt_input")
            elif doubt_src.startswith("📸"):
                d_file = st.camera_input("Take a live photo of the question", key="d_cam_input")
                q_text = st.text_input("Any extra instructions? (optional)", placeholder="e.g. Solve Q2 only", key="d_cam_txt")
                if d_file:
                    data, mime = prepare_image(d_file.getvalue())
                    d_media = {"bytes": data, "mime": mime}
            elif doubt_src.startswith("🖼️"):
                d_file = st.file_uploader("Upload a photo of the question", type=["png", "jpg", "jpeg", "webp"], key="d_img_input")
                q_text = st.text_input("Any extra instructions? (optional)", placeholder="e.g. Explain step 3", key="d_img_txt")
                if d_file:
                    data, mime = prepare_image(d_file.getvalue())
                    d_media = {"bytes": data, "mime": mime}
                    st.image(data, caption="Uploaded Question", width=300)
            else:
                d_pdf = st.file_uploader("Upload PDF Document", type=["pdf"], key="d_pdf_input")
                extra = st.text_input("What do you want to ask from this PDF?", placeholder="e.g. Summarize Chapter 2", key="d_pdf_txt")
                if d_pdf:
                    try:
                        pdf_text, _ = read_pdf(d_pdf, 1, 5)
                        if pdf_text.strip():
                            st.success("PDF loaded successfully.")
                            q_text = f"Document content:\n{pdf_text[:MAX_CHARS]}\n\nQuestion: {extra or 'Explain the key concepts.'}"
                    except Exception as e:
                        st.error(f"PDF read error: {e}")

        if st.button("💡 Explain", type="primary", use_container_width=True, key="btn_solve_doubt"):
            if not q_text.strip() and not d_media:
                st.warning("Please write a doubt, upload a file or take a photo.")
            else:
                with st.spinner("AI is analyzing your doubt..."):
                    try:
                        if d_media:
                            b64 = base64.b64encode(d_media["bytes"]).decode()
                            msg = [
                                {"role": "system", "content": "You are an expert tutor. Provide a clear step-by-step solution."},
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": q_text or "Solve and explain this problem."},
                                        {"type": "image_url", "image_url": {"url": f"data:{d_media['mime']};base64,{b64}"}}
                                    ]
                                }
                            ]
                            res = llm(msg, VISION_MODEL)
                        else:
                            msg = [
                                {"role": "system", "content": "You are an expert tutor. Provide a clear step-by-step solution."},
                                {"role": "user", "content": q_text}
                            ]
                            res = llm(msg, cfg["model"])
                        
                        st.markdown("### 💡 AI Solution")
                        st.markdown(res)
                    except Exception as e:
                        st.error(friendly_error(e))

elif st.session_state.stage == "quiz":
    ss = st.session_state
    quiz = ss.quiz
    i = ss.idx
    q = quiz[i]
    st.progress((i + 1) / len(quiz), text=f"Question {i + 1} of {len(quiz)}")
    st.markdown(f"### Q{i + 1}. {q['question']}")
    
    choice = st.radio("Options", q['options'], key=f"q_{i}")
    if st.button("Next Question", type="primary"):
        ss.answers[i] = choice
        if i + 1 < len(quiz):
            advance(i)
            st.rerun()
        else:
            finish_quiz()
            st.rerun()

else:
    ss = st.session_state
    res = ss.result
    st.markdown("## Quiz Finished! 🏆")
    st.metric("Score", f"{res['score']} / {res['total']}")
    if st.button("Start New Quiz", type="primary"):
        reset_all()
        st.rerun()
