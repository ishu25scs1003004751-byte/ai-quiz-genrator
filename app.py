import os
import json
import math
import time
import random
import html
from datetime import datetime

import pandas as pd
import streamlit as st
from pypdf import PdfReader
from google import genai
from google.genai import types

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuizForge · AI Quiz Generator",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# STYLING (indigo ink + saffron accent, works in light & dark)
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=DM+Sans:wght@400;500;700&display=swap');

:root{
  --ink:#2D2A6E; --ink-2:#4B46B8; --saffron:#F5B335;
  --good:#1FA67A; --bad:#E5484D; --card:rgba(127,127,160,.10); --line:rgba(127,127,160,.28);
}
html, body, [class*="css"]{ font-family:'DM Sans',sans-serif; }
h1,h2,h3,.qf-title{ font-family:'Bricolage Grotesque',sans-serif !important; letter-spacing:-.02em; }
#MainMenu, footer{ visibility:hidden; }
.block-container{ padding-top:1.6rem; max-width:820px; }

.qf-hero{
  background:linear-gradient(135deg,var(--ink) 0%,#1B1950 100%);
  border-radius:22px; padding:34px 32px; color:#fff; margin-bottom:22px;
  position:relative; overflow:hidden; border:1px solid rgba(255,255,255,.08);
}
.qf-hero:after{
  content:"?"; position:absolute; right:18px; top:-30px; font-size:210px; font-weight:800;
  font-family:'Bricolage Grotesque',sans-serif; color:var(--saffron); opacity:.16; line-height:1;
}
.qf-title{ font-size:2.5rem; font-weight:800; margin:0; line-height:1.05; color:#fff; }
.qf-sub{ margin-top:10px; font-size:1.02rem; color:#C9C7F5; max-width:540px; }
.qf-chip{
  display:inline-block; padding:4px 12px; border-radius:99px; font-size:.78rem; font-weight:700;
  background:rgba(245,179,53,.18); color:var(--saffron); margin-right:6px; margin-top:14px;
}

.qf-qcard{
  background:var(--card); border:1px solid var(--line); border-left:6px solid var(--saffron);
  border-radius:16px; padding:22px 24px; margin:14px 0 10px 0;
}
.qf-qnum{ font-size:.85rem; font-weight:700; color:var(--saffron); margin-bottom:6px; }
.qf-qtext{ font-size:1.28rem; font-weight:600; line-height:1.4; }
.qf-topic{ float:right; font-size:.75rem; padding:2px 10px; border-radius:99px; border:1px solid var(--line); opacity:.8; }

.qf-fb{ border-radius:14px; padding:14px 18px; margin:10px 0; font-size:.98rem; }
.qf-fb.ok{ background:rgba(31,166,122,.14); border:1px solid var(--good); }
.qf-fb.no{ background:rgba(229,72,77,.12); border:1px solid var(--bad); }
.qf-hint{ background:rgba(245,179,53,.14); border:1px dashed var(--saffron); border-radius:12px; padding:10px 14px; margin:8px 0; }

.qf-tiles{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:14px 0 8px; }
.qf-tile{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px; text-align:center; }
.qf-tile .v{ font-family:'Bricolage Grotesque',sans-serif; font-size:1.6rem; font-weight:800; }
.qf-tile .l{ font-size:.78rem; opacity:.75; }
@media (max-width:640px){ .qf-tiles{ grid-template-columns:repeat(2,1fr);} .qf-title{font-size:2rem;} }

.qf-ring{ position:relative; width:150px; height:150px; margin:6px auto 4px; display:flex; align-items:center; justify-content:center; }
.qf-ring:before{
  content:""; position:absolute; inset:0; border-radius:50%;
  background:conic-gradient(var(--ring-color) calc(var(--p)*1%), rgba(127,127,160,.22) 0);
  -webkit-mask:radial-gradient(farthest-side, transparent calc(100% - 14px), #000 calc(100% - 13px));
          mask:radial-gradient(farthest-side, transparent calc(100% - 14px), #000 calc(100% - 13px));
}
.qf-ring-in{ position:relative; text-align:center; }
.qf-ring-in .big{ font-family:'Bricolage Grotesque',sans-serif; font-size:2.1rem; font-weight:800; line-height:1; }
.qf-ring-in .sm{ font-size:.8rem; opacity:.7; }

.qf-badges{ display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:10px 0 4px; }
.qf-badge{ background:rgba(245,179,53,.16); border:1px solid var(--saffron); border-radius:99px; padding:6px 14px; font-weight:700; font-size:.88rem; }

.qf-flash{
  min-height:190px; display:flex; align-items:center; justify-content:center; text-align:center;
  background:var(--card); border:1px solid var(--line); border-radius:20px; padding:28px; margin:12px 0;
  font-size:1.3rem; font-weight:600;
}
.qf-flash.back{ border-color:var(--good); background:rgba(31,166,122,.10); }

.stButton>button, .stDownloadButton>button{
  border-radius:12px; font-weight:700; padding:.55rem 1.1rem; border:1px solid var(--line);
  transition:transform .08s ease;
}
.stButton>button:hover{ transform:translateY(-1px); }
.stButton>button[kind="primary"]{ background:var(--ink-2); border-color:var(--ink-2); color:#fff; }
.stButton>button:focus-visible{ outline:3px solid var(--saffron); }

div[role="radiogroup"] > label{
  background:var(--card); border:1px solid var(--line); border-radius:12px;
  padding:10px 14px; margin-bottom:8px; width:100%;
}
div[role="radiogroup"] > label:hover{ border-color:var(--saffron); }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# API KEY / CLIENT
# ─────────────────────────────────────────────────────────────
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    api_key = None
api_key = api_key or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error(
        "API key nahi mili. Streamlit Cloud ke **Secrets** me `GEMINI_API_KEY` add karein "
        "ya environment variable set karein."
    )
    st.stop()


@st.cache_resource
def get_client(key: str):
    return genai.Client(api_key=key)


client = get_client(api_key)

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
def fresh_run_state():
    return {
        "quiz": [],
        "idx": 0,
        "answers": {},
        "locked": {},
        "hints_used": {},
        "times": {},
        "timed_out": {},
        "result": None,
        "study_plan": "",
        "celebrated": False,
        "start_time": None,
        "end_time": None,
    }


GLOBAL_DEFAULTS = {
    "stage": "setup",
    "quiz_id": 0,
    "history": [],
    "meta": {},
    "total_xp": 0,
    "bookmarks": {},
    "deep": {},
    "flash_cards": [],
    "flash_i": 0,
    "flash_show": False,
    "flash_return": "setup",
    "q_key": None,
    "q_start": time.time(),
    "_picked": "",
}
for k, v in {**GLOBAL_DEFAULTS, **fresh_run_state()}.items():
    if k not in st.session_state:
        st.session_state[k] = v

MAX_CHARS = 30000
XP_BASE = {"Easy": 10, "Medium": 15, "Hard": 20}


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def esc(s) -> str:
    return html.escape(str(s))


def fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60}m {seconds % 60:02d}s"


def level_of(xp):
    return xp // 100 + 1


def clean_json(raw: str):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                data = v
                break
    return data


def validate_and_shuffle(items):
    good = []
    for q in items:
        try:
            question = str(q["question"]).strip()
            options = [str(o).strip() for o in q["options"]]
            answer = str(q["answer"]).strip()
            explanation = str(q.get("explanation", "")).strip() or "Explanation available nahi hai."
            hint = str(q.get("hint", "")).strip()
            topic = str(q.get("topic", "General")).strip()[:30] or "General"
        except Exception:
            continue
        if len(options) < 2 or not question:
            continue
        if answer not in options:
            letters = "ABCDEFGH"
            if len(answer) == 1 and answer.upper() in letters[: len(options)]:
                answer = options[letters.index(answer.upper())]
            else:
                match = [o for o in options if o.lower() == answer.lower()]
                if not match:
                    continue
                answer = match[0]
        is_tf = {o.lower() for o in options} == {"true", "false"}
        if not is_tf:
            random.shuffle(options)
        good.append(
            {
                "question": question,
                "options": options,
                "answer": answer,
                "explanation": explanation,
                "hint": hint,
                "topic": topic,
            }
        )
    return good


def generate_quiz(text, num_q, diff, qtype, lang, model, media=None, avoid=None):
    type_rule = {
        "Multiple Choice": "Every question must have exactly 4 options.",
        "True / False": 'Every question is a statement; options must be exactly ["True", "False"].',
        "Mixed": 'Mix of 4-option MCQs and True/False questions (True/False options are exactly ["True","False"]).',
    }[qtype]
    avoid_rule = ""
    if avoid:
        avoid_rule = "- Do NOT repeat or rephrase these earlier questions:\n  " + "\n  ".join(
            f"* {a}" for a in avoid[:30]
        )
    content_block = (
        "Use the attached file (photo/scan/PDF) as the content. Read it carefully, including handwriting if present."
        if media
        else f'Content:\n"""\n{text[:MAX_CHARS]}\n"""'
    )

    prompt = f"""You are an expert teacher and quiz designer.
Create {num_q} quiz questions from the content below.

Rules:
- Difficulty: {diff}.
- {type_rule}
- Write questions, options, hints and explanations in: {lang}.
- Exactly one option is correct; "answer" must be the EXACT text of that option.
- Distractors must be plausible, not silly. Avoid "All of the above".
- Cover different parts of the content; no duplicate questions.
- "hint": a short nudge that helps think, WITHOUT revealing the answer.
- "explanation": 1-2 short sentences explaining why the answer is correct.
- "topic": a 1-3 word sub-topic label for the question (e.g. "Photosynthesis").
{avoid_rule}

Return ONLY a JSON array in this shape:
[{{\"question\": \"...\", \"options\": [\"...\", \"...\"], \"answer\": \"...\", \"explanation\": \"...\", \"hint\": \"...\", \"topic\": \"...\"}}]

{content_block}
"""
    contents = [prompt]
    if media:
        contents = [types.Part.from_bytes(data=media["bytes"], mime_type=media["mime"]), prompt]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.8),
    )
    return validate_and_shuffle(clean_json(response.text))


def explain_more(q, user_ans, lang, model):
    key = q["question"]
    if key in st.session_state.deep:
        return st.session_state.deep[key]
    prompt = f"""Explain this quiz question in more depth for a student. Language: {lang}.
Question: {q['question']}
Options: {q['options']}
Correct answer: {q['answer']}
Student's answer: {user_ans or 'skipped'}
Give: (1) why the correct answer is right, (2) why the student's choice (if wrong) is tempting but wrong,
(3) one simple real-life example or memory trick. Keep it under 150 words, use short bullet points."""
    resp = client.models.generate_content(model=model, contents=prompt)
    st.session_state.deep[key] = resp.text
    return resp.text


def make_study_plan(wrong_qs, lang, model):
    items = "\n".join(
        f"- [{q['topic']}] {q['question']} (correct: {q['answer']})" for q in wrong_qs
    )
    prompt = f"""A student got these quiz questions wrong or skipped them. Language: {lang}.
{items}

Write a compact revision plan:
1. "Weak areas" - 2-4 bullets naming the concepts to revise.
2. "Quick notes" - the key facts to remember, as short bullets.
3. "Next steps" - 3 concrete practice tips.
Keep it under 220 words."""
    resp = client.models.generate_content(model=model, contents=prompt)
    return resp.text


def start_quiz(quiz, meta):
    st.session_state.update(fresh_run_state())
    st.session_state.update(
        quiz=quiz,
        quiz_id=st.session_state.quiz_id + 1,
        start_time=time.time(),
        stage="quiz",
        meta=meta,
        q_key=None,
    )


def record_time(i):
    if i not in st.session_state.times:
        st.session_state.times[i] = time.time() - st.session_state.q_start


def compute_badges(pct, best_streak, avg_time, hints, diff):
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
    if len(st.session_state.history) >= 3:
        badges.append("📚 Regular Learner")
    return badges


def finish_quiz():
    ss = st.session_state
    ss.end_time = time.time()
    quiz, answers = ss.quiz, ss.answers
    diff = ss.meta.get("difficulty", "Medium")

    xp = streak = best = correct = 0
    for i, q in enumerate(quiz):
        if answers.get(i) == q["answer"]:
            correct += 1
            streak += 1
            best = max(best, streak)
            pts = XP_BASE.get(diff, 15)
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

    old_level = level_of(ss.total_xp)
    ss.total_xp += xp
    ss.history.append(
        {
            "time": datetime.now().strftime("%d %b, %H:%M"),
            "topic": ss.meta.get("label", "Quiz"),
            "difficulty": diff,
            "score": correct,
            "total": total,
        }
    )
    ss.result = {
        "score": correct,
        "total": total,
        "pct": pct,
        "xp": xp,
        "best_streak": best,
        "avg_time": avg_time,
        "hints": hints,
        "leveled_up": level_of(ss.total_xp) > old_level,
        "badges": compute_badges(pct, best, avg_time, hints, diff),
    }
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


def build_report_html():
    ss = st.session_state
    r = ss.result
    rows = ""
    for i, q in enumerate(ss.quiz):
        sel = ss.answers.get(i)
        ok = sel == q["answer"]
        rows += (
            f"<tr><td>{i + 1}</td><td>{esc(q['question'])}</td><td>{esc(sel or '—')}</td>"
            f"<td>{esc(q['answer'])}</td><td style='color:{'#1FA67A' if ok else '#E5484D'}'>"
            f"{'✔' if ok else '✘'}</td><td>{esc(q['explanation'])}</td></tr>"
        )
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>QuizForge Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 16px;color:#222}}
h1{{color:#2D2A6E}} table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:8px;font-size:14px;vertical-align:top}}
th{{background:#2D2A6E;color:#fff}} .s{{font-size:20px;margin:10px 0}}</style></head><body>
<h1>QuizForge · Result Report</h1>
<p>{esc(ss.meta.get('label', 'Quiz'))} · {esc(ss.meta.get('difficulty', ''))} · {datetime.now().strftime('%d %b %Y, %H:%M')}</p>
<p class="s"><b>Score:</b> {r['score']}/{r['total']} ({r['pct']}%) &nbsp; <b>XP:</b> {r['xp']} &nbsp; <b>Best streak:</b> {r['best_streak']}</p>
<table><tr><th>#</th><th>Question</th><th>Your answer</th><th>Correct</th><th></th><th>Explanation</th></tr>{rows}</table>
</body></html>"""


# ─────────────────────────────────────────────────────────────
# COUNTDOWN (auto-refreshing fragment, Streamlit ≥ 1.37)
# ─────────────────────────────────────────────────────────────
def _countdown(limit, qid, i, total, practice):
    left = limit - (time.time() - st.session_state.q_start)
    if left > 0:
        st.progress(max(left / limit, 0.0), text=f"⏱️ {math.ceil(left)} sec bache hain")
        return
    sel = st.session_state.get(f"radio_{qid}_{i}")
    st.session_state.answers[i] = sel
    record_time(i)
    if practice:
        st.session_state.locked[i] = True
        st.session_state.timed_out[i] = True
    elif i == total - 1:
        finish_quiz()
    else:
        st.session_state.idx += 1
    st.rerun()


_fragment = getattr(st, "fragment", None)
countdown = _fragment(run_every=1)(_countdown) if _fragment else None

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    lvl = level_of(st.session_state.total_xp)
    st.markdown(f"### 🎖️ Level {lvl}")
    st.progress((st.session_state.total_xp % 100) / 100, text=f"{st.session_state.total_xp} XP")

    st.markdown("### ⚙️ Quiz Settings")
    num_questions = st.slider("Questions", 3, 20, 5)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    qtype = st.selectbox("Question type", ["Multiple Choice", "True / False", "Mixed"])
    language = st.selectbox("Language", ["English", "Hinglish", "Hindi"])
    mode = st.radio(
        "Mode",
        ["Practice", "Exam"],
        help="Practice: har sawal ke baad turant answer + explanation.\nExam: sab solve karo, result end me.",
    )
    timer_opt = st.selectbox(
        "Timer per question",
        ["Off", "15 sec", "30 sec", "60 sec"],
        help="Time khatam hote hi answer auto-submit ho jata hai.",
    )
    time_limit = 0 if timer_opt == "Off" else int(timer_opt.split()[0])
    if time_limit and countdown is None:
        st.warning("Timer ke liye Streamlit ≥ 1.37 chahiye.")
    
    with st.expander("Advanced"):
        model = st.selectbox(
            "AI model",
            ["gemini-3.8-flash", "gemini-3.8-pro"],
            help="Flash = fast. Pro = zyada accurate, thoda slow.",
        )

    st.divider()
