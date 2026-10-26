import os
import io
import json
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
# STYLING  (indigo ink + saffron accent, works in light & dark)
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

/* Hero */
.qf-hero{
  background: linear-gradient(135deg,var(--ink) 0%,#1B1950 100%);
  border-radius:22px; padding:34px 32px; color:#fff; margin-bottom:22px;
  position:relative; overflow:hidden; border:1px solid rgba(255,255,255,.08);
}
.qf-hero:after{
  content:"?"; position:absolute; right:18px; top:-30px; font-size:210px; font-weight:800;
  font-family:'Bricolage Grotesque',sans-serif; color:var(--saffron); opacity:.16; line-height:1;
}
.qf-title{ font-size:2.5rem; font-weight:800; margin:0; line-height:1.05; color:#fff; }
.qf-sub{ margin-top:10px; font-size:1.02rem; color:#C9C7F5; max-width:520px; }
.qf-chip{
  display:inline-block; padding:4px 12px; border-radius:99px; font-size:.78rem; font-weight:700;
  background:rgba(245,179,53,.18); color:var(--saffron); margin-right:6px; margin-top:14px;
}

/* Question card */
.qf-qcard{
  background:var(--card); border:1px solid var(--line); border-left:6px solid var(--saffron);
  border-radius:16px; padding:22px 24px; margin:14px 0 10px 0;
}
.qf-qnum{ font-size:.85rem; font-weight:700; color:var(--saffron); margin-bottom:6px; }
.qf-qtext{ font-size:1.28rem; font-weight:600; line-height:1.4; }

/* Feedback */
.qf-fb{ border-radius:14px; padding:14px 18px; margin:10px 0; font-size:.98rem; }
.qf-fb.ok{ background:rgba(31,166,122,.14); border:1px solid var(--good); }
.qf-fb.no{ background:rgba(229,72,77,.12); border:1px solid var(--bad); }
.qf-fb b{ font-weight:700; }

/* Stat tiles */
.qf-tiles{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:14px 0 8px; }
.qf-tile{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px; text-align:center; }
.qf-tile .v{ font-family:'Bricolage Grotesque',sans-serif; font-size:1.7rem; font-weight:800; }
.qf-tile .l{ font-size:.78rem; opacity:.75; }
@media (max-width:640px){ .qf-tiles{ grid-template-columns:repeat(2,1fr);} .qf-title{font-size:2rem;} }

/* Score ring */
.qf-ring{
  width:150px; height:150px; border-radius:50%; margin:6px auto 4px; display:flex; align-items:center; justify-content:center;
  background:conic-gradient(var(--ring-color) calc(var(--p)*1%), rgba(127,127,160,.22) 0);
}
.qf-ring-in{
  width:116px; height:116px; border-radius:50%; background:var(--bg-fallback,#0e1117);
  display:flex; flex-direction:column; align-items:center; justify-content:center;
}
.qf-ring-in .big{ font-family:'Bricolage Grotesque',sans-serif; font-size:2rem; font-weight:800; }
.qf-ring-in .sm{ font-size:.75rem; opacity:.7; }

/* Buttons */
.stButton>button, .stDownloadButton>button{
  border-radius:12px; font-weight:700; padding:.55rem 1.1rem; border:1px solid var(--line);
  transition:transform .08s ease;
}
.stButton>button:hover{ transform:translateY(-1px); }
.stButton>button[kind="primary"]{ background:var(--ink-2); border-color:var(--ink-2); color:#fff; }
.stButton>button:focus-visible{ outline:3px solid var(--saffron); }

/* Radio options look like pills */
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
DEFAULTS = {
    "stage": "setup",        # setup → quiz → result
    "quiz": [],
    "quiz_id": 0,
    "idx": 0,
    "answers": {},           # idx -> selected option
    "locked": {},            # idx -> bool (practice mode)
    "start_time": None,
    "end_time": None,
    "history": [],           # list of past attempts
    "meta": {},              # topic/difficulty etc. of current quiz
    "celebrated": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

MAX_CHARS = 30000  # keep prompt size safe


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def esc(s) -> str:
    return html.escape(str(s))


def clean_json(raw: str):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    if isinstance(data, dict):  # model wrapped it in {"questions": [...]}
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
        except Exception:
            continue
        if len(options) < 2 or not question:
            continue
        if answer not in options:
            # allow answer like "A" / "B" / index
            letters = "ABCDEFGH"
            if len(answer) == 1 and answer.upper() in letters[: len(options)]:
                answer = options[letters.index(answer.upper())]
            else:
                match = [o for o in options if o.lower() == answer.lower()]
                if match:
                    answer = match[0]
                else:
                    continue
        is_tf = {o.lower() for o in options} == {"true", "false"}
        if not is_tf:
            random.shuffle(options)
        good.append(
            {"question": question, "options": options, "answer": answer, "explanation": explanation}
        )
    return good


def generate_quiz(text, num_q, diff, qtype, lang, model):
    type_rule = {
        "Multiple Choice": "Every question must have exactly 4 options.",
        "True / False": 'Every question is a statement; options must be exactly ["True", "False"].',
        "Mixed": 'Mix of 4-option MCQs and True/False questions (True/False options are exactly ["True","False"]).',
    }[qtype]

    prompt = f"""You are an expert teacher and quiz designer.
Create {num_q} quiz questions from the content below.

Rules:
- Difficulty: {diff}.
- {type_rule}
- Write questions, options and explanations in: {lang}.
- Exactly one option is correct; "answer" must be the EXACT text of that option.
- Distractors must be plausible, not silly. Avoid "All of the above".
- Cover different parts of the content; no duplicate questions.
- Explanation: 1-2 short sentences explaining why the answer is correct.

Return ONLY a JSON array in this shape:
[{{"question": "...", "options": ["...", "..."], "answer": "...", "explanation": "..."}}]

Content:
\"\"\"
{text[:MAX_CHARS]}
\"\"\"
"""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.8,
        ),
    )
    return validate_and_shuffle(clean_json(response.text))


def start_quiz(quiz, meta):
    st.session_state.update(
        quiz=quiz,
        quiz_id=st.session_state.quiz_id + 1,
        idx=0,
        answers={},
        locked={},
        start_time=time.time(),
        end_time=None,
        stage="quiz",
        meta=meta,
        celebrated=False,
    )


def finish_quiz():
    st.session_state.end_time = time.time()
    quiz = st.session_state.quiz
    score = sum(
        1 for i, q in enumerate(quiz) if st.session_state.answers.get(i) == q["answer"]
    )
    st.session_state.history.append(
        {
            "time": datetime.now().strftime("%d %b, %H:%M"),
            "topic": st.session_state.meta.get("label", "Quiz"),
            "difficulty": st.session_state.meta.get("difficulty", "-"),
            "score": score,
            "total": len(quiz),
        }
    )
    st.session_state.stage = "result"


def reset_all():
    for k in ("quiz", "answers", "locked"):
        st.session_state[k] = DEFAULTS[k].copy() if hasattr(DEFAULTS[k], "copy") else DEFAULTS[k]
    st.session_state.stage = "setup"
    st.session_state.idx = 0


def read_pdf(file, start_page, end_page):
    reader = PdfReader(file)
    text = ""
    for p in reader.pages[start_page - 1 : end_page]:
        t = p.extract_text()
        if t:
            text += t + "\n"
    return text, len(reader.pages)


def fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60}m {seconds % 60:02d}s"


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
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
    with st.expander("Advanced"):
        model = st.selectbox(
            "AI model",
            ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"],
            help="Flash = fast. Pro = zyada accurate, thoda slow.",
        )

    st.divider()
    st.markdown("### 🏆 Meri History")
    if st.session_state.history:
        for h in reversed(st.session_state.history[-6:]):
            pct = round(h["score"] / h["total"] * 100)
            st.markdown(
                f"**{esc(h['topic'])[:28]}**  \n"
                f"{h['score']}/{h['total']} · {pct}% · {h['difficulty']}  \n"
                f"<small style='opacity:.6'>{h['time']}</small>",
                unsafe_allow_html=True,
            )
        best = max(h["score"] / h["total"] for h in st.session_state.history)
        st.caption(f"⭐ Best score: {round(best * 100)}%")
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Abhi koi quiz nahi diya. Pehla quiz banao!")

# ─────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="qf-hero">
  <div class="qf-title">QuizForge</div>
  <div class="qf-sub">Koi bhi topic ya PDF do — AI turant tumhare liye quiz bana dega. Practice karo, score dekho, aur weak areas pakdo.</div>
  <span class="qf-chip">Topic</span><span class="qf-chip">PDF</span><span class="qf-chip">Pasted notes</span>
</div>
""",
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════
# STAGE 1 · SETUP
# ═════════════════════════════════════════════════════════════
if st.session_state.stage == "setup":
    tab_topic, tab_pdf, tab_text = st.tabs(["💡 Topic", "📄 PDF", "📝 Paste notes"])

    input_text, label = "", ""

    with tab_topic:
        topic = st.text_input(
            "Kis topic par quiz chahiye?",
            placeholder="e.g. Machine Learning basics, Indian Constitution, Python lists…",
        )
        st.caption("Quick picks:")
        cols = st.columns(4)
        picks = ["Python Basics", "World History", "Human Biology", "Indian Economy"]
        for c, p in zip(cols, picks):
            if c.button(p, use_container_width=True, key=f"pick_{p}"):
                st.session_state["_picked"] = p
                st.rerun()
        if st.session_state.get("_picked") and not topic:
            topic = st.session_state["_picked"]
            st.info(f"Selected topic: **{topic}**")
        if topic.strip():
            input_text = f"Topic: {topic.strip()}\nUse your own knowledge to cover this topic accurately."
            label = topic.strip()

    with tab_pdf:
        up = st.file_uploader("PDF upload karo", type=["pdf"])
        if up is not None:
            try:
                _, total_pages = read_pdf(up, 1, 1)
                up.seek(0)
                if total_pages > 1:
                    rng = st.slider("Page range", 1, total_pages, (1, min(total_pages, 10)))
                else:
                    rng = (1, 1)
                pdf_text, _ = read_pdf(up, rng[0], rng[1])
                if pdf_text.strip():
                    st.success(
                        f"✅ {rng[1] - rng[0] + 1} page(s) padhe · {len(pdf_text):,} characters"
                    )
                    if len(pdf_text) > MAX_CHARS:
                        st.warning(
                            f"Text bahut lamba hai, pehle {MAX_CHARS:,} characters use honge. "
                            "Chhota page range chuno."
                        )
                    input_text = pdf_text
                    label = f"PDF: {up.name}"
                else:
                    st.error("Is PDF se text nahi nikla (shayad scanned image hai).")
            except Exception as e:
                st.error(f"PDF read nahi ho paya: {e}")

    with tab_text:
        pasted = st.text_area(
            "Apne notes / article yahan paste karo",
            height=200,
            placeholder="Chapter ka text, notes, ya koi bhi article…",
        )
        if pasted.strip():
            st.caption(f"{len(pasted):,} characters")
            input_text = pasted
            label = "Pasted notes"

    st.write("")
    go = st.button("✨ Quiz banao", type="primary", use_container_width=True)

    if go:
        if not input_text.strip():
            st.warning("Pehle topic likho, PDF upload karo ya notes paste karo.")
        else:
            with st.spinner("AI sawal bana raha hai…"):
                try:
                    quiz = generate_quiz(
                        input_text, num_questions, difficulty, qtype, language, model
                    )
                    if not quiz:
                        st.error("Valid sawal nahi ban paye. Dobara try karo.")
                    else:
                        start_quiz(
                            quiz,
                            {
                                "label": label,
                                "difficulty": difficulty,
                                "mode": mode,
                                "source": input_text,
                            },
                        )
                        st.session_state["_picked"] = ""
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("AI ka response samajh nahi aaya. Dobara try karo.")
                except Exception as e:
                    st.error(f"Quiz generate karne me error: {e}")

# ═════════════════════════════════════════════════════════════
# STAGE 2 · QUIZ
# ═════════════════════════════════════════════════════════════
elif st.session_state.stage == "quiz":
    quiz = st.session_state.quiz
    total = len(quiz)
    i = st.session_state.idx
    q = quiz[i]
    practice = st.session_state.meta.get("mode") == "Practice"
    qid = st.session_state.quiz_id

    answered = sum(1 for a in st.session_state.answers.values() if a is not None)
    top_l, top_r = st.columns([4, 1])
    top_l.progress(i / total, text=f"Question {i + 1} of {total}")
    top_r.markdown(
        f"<div style='text-align:right;font-weight:700'>✅ {answered}/{total}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""<div class="qf-qcard">
        <div class="qf-qnum">Question {i + 1}</div>
        <div class="qf-qtext">{esc(q['question'])}</div></div>""",
        unsafe_allow_html=True,
    )

    locked = st.session_state.locked.get(i, False)
    prev = st.session_state.answers.get(i)
    start_index = q["options"].index(prev) if prev in q["options"] else None

    choice = st.radio(
        "Apna answer chuno",
        q["options"],
        index=start_index,
        key=f"radio_{qid}_{i}",
        disabled=locked,
        label_visibility="collapsed",
    )

    # Feedback (practice mode)
    if practice and locked:
        if prev == q["answer"]:
            st.markdown(
                f"<div class='qf-fb ok'>✅ <b>Sahi jawab!</b><br>{esc(q['explanation'])}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='qf-fb no'>❌ <b>Galat.</b> Sahi answer: <b>{esc(q['answer'])}</b>"
                f"<br>{esc(q['explanation'])}</div>",
                unsafe_allow_html=True,
            )

    st.write("")
    b1, b2, b3 = st.columns([1, 1, 1])
    last = i == total - 1

    # Back (exam mode only)
    if not practice and i > 0:
        if b1.button("⬅️ Back", use_container_width=True):
            st.session_state.answers[i] = choice
            st.session_state.idx -= 1
            st.rerun()

    if practice and not locked:
        if b2.button("Check answer", type="primary", use_container_width=True, disabled=choice is None):
            st.session_state.answers[i] = choice
            st.session_state.locked[i] = True
            st.rerun()
        if b3.button("Skip ⏭️", use_container_width=True):
            st.session_state.answers[i] = None
            st.session_state.locked[i] = True
            if last:
                finish_quiz()
            else:
                st.session_state.idx += 1
            st.rerun()
    else:
        label_next = "Finish 🏁" if last else "Next ➡️"
        if b3.button(label_next, type="primary", use_container_width=True):
            if not practice:
                st.session_state.answers[i] = choice
            if last:
                finish_quiz()
            else:
                st.session_state.idx += 1
            st.rerun()

    st.write("")
    if st.button("✖ Quiz chhodo"):
        reset_all()
        st.rerun()

# ═════════════════════════════════════════════════════════════
# STAGE 3 · RESULT
# ═════════════════════════════════════════════════════════════
else:
    quiz = st.session_state.quiz
    total = len(quiz)
    answers = st.session_state.answers
    correct_idx = [i for i, q in enumerate(quiz) if answers.get(i) == q["answer"]]
    skipped_idx = [i for i in range(total) if answers.get(i) is None]
    wrong_idx = [i for i in range(total) if i not in correct_idx and i not in skipped_idx]
    score = len(correct_idx)
    pct = round(score / total * 100)
    elapsed = (st.session_state.end_time or time.time()) - (st.session_state.start_time or time.time())

    if pct >= 80:
        color, title, msg = "#1FA67A", "Zabardast! 🏆", "Topic par tumhari pakad mast hai."
    elif pct >= 50:
        color, title, msg = "#F5B335", "Achha try! 👍", "Thodi aur practice se top score aa jayega."
    else:
        color, title, msg = "#E5484D", "Keep going 💪", "Explanations padho aur dobara try karo."

    if not st.session_state.celebrated:
        if pct >= 80:
            st.balloons()
        st.session_state.celebrated = True

    st.markdown(f"## {title}")
    st.caption(msg)
    st.markdown(
        f"""
<div class="qf-ring" style="--p:{pct};--ring-color:{color}">
  <div class="qf-ring-in"><div class="big">{pct}%</div><div class="sm">{score} / {total}</div></div>
</div>
<div class="qf-tiles">
  <div class="qf-tile"><div class="v" style="color:#1FA67A">{score}</div><div class="l">Sahi</div></div>
  <div class="qf-tile"><div class="v" style="color:#E5484D">{len(wrong_idx)}</div><div class="l">Galat</div></div>
  <div class="qf-tile"><div class="v">{len(skipped_idx)}</div><div class="l">Skipped</div></div>
  <div class="qf-tile"><div class="v">{fmt_time(elapsed)}</div><div class="l">Time</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Action row
    a1, a2, a3 = st.columns(3)
    if a1.button("🔁 Naya quiz", use_container_width=True, type="primary"):
        reset_all()
        st.rerun()
    if a2.button(
        "🎯 Sirf galat dobara",
        use_container_width=True,
        disabled=not (wrong_idx or skipped_idx),
        help="Sirf galat/skip kiye hue sawal phir se solve karo",
    ):
        redo = [quiz[i] for i in wrong_idx + skipped_idx]
        for q in redo:
            if {o.lower() for o in q["options"]} != {"true", "false"}:
                random.shuffle(q["options"])
        meta = dict(st.session_state.meta)
        meta["label"] = "Retry · " + meta.get("label", "Quiz")
        start_quiz(redo, meta)
        st.rerun()
    if a3.button("🔄 Wahi quiz phir se", use_container_width=True):
        start_quiz(quiz, dict(st.session_state.meta))
        st.rerun()

    # Review
    st.markdown("### 🔍 Review")
    for i, q in enumerate(quiz):
        sel = answers.get(i)
        if sel == q["answer"]:
            icon = "✅"
        elif sel is None:
            icon = "⏭️"
        else:
            icon = "❌"
        with st.expander(f"{icon}  Q{i + 1}. {q['question'][:90]}"):
            st.markdown(f"**{q['question']}**")
            for o in q["options"]:
                if o == q["answer"]:
                    st.markdown(f"- ✅ **{o}**")
                elif o == sel:
                    st.markdown(f"- ❌ ~~{o}~~ (tumhara answer)")
                else:
                    st.markdown(f"- {o}")
            if sel is None:
                st.caption("Tumne ye sawal skip kiya tha.")
            st.info(f"💡 {q['explanation']}")

    # Downloads
    st.markdown("### 📥 Download")
    df = pd.DataFrame(
        [
            {
                "No": i + 1,
                "Question": q["question"],
                "Options": " | ".join(q["options"]),
                "Your answer": answers.get(i) or "—",
                "Correct answer": q["answer"],
                "Result": "Correct" if answers.get(i) == q["answer"] else "Wrong/Skipped",
                "Explanation": q["explanation"],
            }
            for i, q in enumerate(quiz)
        ]
    )
    d1, d2 = st.columns(2)
    d1.download_button(
        "Results (CSV)",
        df.to_csv(index=False).encode("utf-8-sig"),
        file_name="quiz_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    d2.download_button(
        "Quiz (JSON)",
        json.dumps(quiz, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="quiz.json",
        mime="application/json",
        use_container_width=True,
    )
