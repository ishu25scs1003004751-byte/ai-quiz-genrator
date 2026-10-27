import base64
import json
import os
import random
import re
import sqlite3
import time
from datetime import datetime
import streamlit as st
from pypdf import PdfReader

# ═════════════════════════════════════════════════════════════
# CONFIGURATION & PAGE SETUP
# ═════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="QuizForge - AI Quiz & PYQ Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

MAX_CHARS = 15000
MAX_IMG_BYTES = 3 * 1024 * 1024  # 3 MB
DEFAULT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "llama-3.2-11b-vision-preview"

# ═════════════════════════════════════════════════════════════
# ORIGINAL CLASSIC GLASSMORPHISM CUSTOM STYLING (CSS)
# ═════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }

    /* Glassmorphism Cards */
    div[data-testid="stVerticalBlock"] > div[element-id*="panel"],
    div[data-testid="stVerticalBlock"] > div[element-id*="panel_pyq"],
    div[data-testid="stVerticalBlock"] > div[element-id*="panel_doubt"] {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }

    /* Top Stats Dashboard Tiles */
    .qf-tiles {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 25px;
    }
    
    .qf-tile {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 18px 20px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .qf-tile:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    .qf-tile .v {
        font-size: 1.8rem;
        font-weight: 800;
        color: #818cf8;
    }
    
    .qf-tile .l {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(15, 23, 42, 0.6);
        padding: 8px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 12px;
        color: #94a3b8;
        font-weight: 600;
        border: none;
        padding: 0 20px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
    }

    /* Custom Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
        border: none;
        border-radius: 12px;
        font-weight: 700;
        letter-spacing: 0.3px;
        padding: 12px 24px;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        transition: all 0.2s ease;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
# DUMMY / GROQ LLM API PLACEHOLDERS
# ═════════════════════════════════════════════════════════════
def llm(messages, model_name=DEFAULT_MODEL):
    pass

def generate_with_progress(prompt, num_questions, difficulty, type_keys, language, model, media=None, adaptive=False):
    return []

def start_quiz(quiz_data, config):
    st.session_state.quiz = quiz_data
    st.session_state.config = config
    st.session_state.stage = "quiz"
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}

def friendly_error(e):
    return f"Kuch error aaya: {e}"

# ═════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════
def read_pdf(file, start_page, end_page):
    reader = PdfReader(file)
    text = ""
    for p in reader.pages[start_page - 1 : end_page]:
        t = p.extract_text()
        if t:
            text += t + "\n"
    return text, len(reader.pages)


def load_pyq_dataset():
    if os.path.exists("pyq_data.json"):
        try:
            with open("pyq_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


# ═════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═════════════════════════════════════════════════════════════
if "stage" not in st.session_state:
    st.session_state.stage = "setup"
if "history" not in st.session_state:
    st.session_state.history = []
if "total_xp" not in st.session_state:
    st.session_state.total_xp = 0

# ═════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION & SETTINGS
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚡ QuizForge")
    st.caption("AI-Powered Learning & PYQ Platform")
    st.divider()
    
    st.subheader("⚙️ Quiz Parameters")
    num_questions = st.slider("Questions ki sankhya", 5, 30, 10)
    difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])
    language = st.selectbox("Language", ["Hinglish", "English", "Hindi"])
    mode = st.radio("Quiz Mode", ["Practice Mode", "Exam Mode (Timer)"])
    time_limit = st.number_input("Time Limit (Minutes)", 1, 60, 10) if mode == "Exam Mode (Timer)" else 0
    marks_correct = st.number_input("Marks per correct answer", 1.0, 5.0, 1.0)
    neg_frac = st.selectbox("Negative Marking Penalty", [0.0, 0.25, 0.333, 0.5])
    adaptive = st.checkbox("Adaptive Difficulty Enable Karein", value=False)
    model = DEFAULT_MODEL
    type_keys = ["mcq"]
    quiz_limit = num_questions

lvl = st.session_state.total_xp // 100 + 1

# ═════════════════════════════════════════════════════════════
# STAGE · SETUP (MAIN DASHBOARD)
# ═════════════════════════════════════════════════════════════
if st.session_state.stage == "setup":
    hist = st.session_state.history
    best_pct = max(h["pct"] for h in hist) if hist else 0
    
    # Classic Colorful Dashboard Stats Tiles
    st.markdown(
        f"""<div class="qf-tiles">
  <div class="qf-tile"><div class="v">⭐ {lvl}</div><div class="l">Current Level</div></div>
  <div class="qf-tile"><div class="v" style="color:#FFC857">🔥 {st.session_state.total_xp}</div><div class="l">Total XP</div></div>
  <div class="qf-tile"><div class="v">🎯 {len(hist)}</div><div class="l">Quizzes Completed</div></div>
  <div class="qf-tile"><div class="v" style="color:#34D399">🏆 {best_pct}%</div><div class="l">Best Accuracy</div></div>
</div>""",
        unsafe_allow_html=True,
    )

    # 3-Tab Glassmorphism Navigation
    tab_quiz, tab_pyq, tab_doubt = st.tabs(["🧠 Quiz Arena", "🏛️ Govt Exam PYQs", "🔍 Doubt Solver & Theory"])

    with tab_quiz:
        with st.container(key="srcpick"):
            source = st.radio("Content Source Select Karein:", ["💡 Topic", "📄 PDF", "🖼️ Photo / Camera", "📝 Notes"], horizontal=True)

        input_text, label, media = "", "", None

        with st.container(key="panel"):
            if source.startswith("💡"):
                topic = st.text_input("Kis topic par quiz chahiye?", placeholder="e.g. Machine Learning basics, Indian Constitution, Python lists…")
                st.caption("🚀 Quick Topic Picks:")
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
                                st.warning(f"Text lamba hai — pehle {MAX_CHARS:,} characters use honge.")
                            input_text, label = pdf_text, f"PDF: {up.name}"
                        else:
                            st.error("Is PDF se text nahi nikla. Page ki **photo** upload karke try karo.")
                    except Exception as e:
                        st.error(f"PDF read error: {e}")

            elif source.startswith("🖼️"):
                st.caption("Photo upload karein ya direct camera se click karein.")
                photo_mode = st.radio("Photo Source:", ["📁 Upload File", "📸 Live Camera Click"], horizontal=True, key="quiz_photo_mode")
                
                mf = None
                if photo_mode == "📁 Upload File":
                    mf = st.file_uploader("Photo upload karo", type=["png", "jpg", "jpeg", "webp"], key="media_up")
                else:
                    mf = st.camera_input("Live Photo Click Karein", key="quiz_cam")

                if mf is not None:
                    data = mf.getvalue()
                    if len(data) > MAX_IMG_BYTES:
                        st.error("Photo 3 MB se badi hai.")
                    else:
                        st.image(data, caption="Selected Photo", use_container_width=True)
                        media = {"bytes": data, "mime": getattr(mf, "type", "image/jpeg") or "image/jpeg"}
                        input_text, label = "(attached image)", f"Photo: {getattr(mf, 'name', 'Camera Picture')}"

            else:
                pasted = st.text_area("Apne notes / article yahan paste karo", height=180, placeholder="Chapter ka text, notes, ya koi bhi article…")
                if pasted.strip():
                    st.caption(f"{len(pasted):,} characters")
                    input_text, label = pasted, "Pasted notes"

        st.write("")
        if st.button("✨ Generate AI Quiz", type="primary", use_container_width=True):
            if not input_text.strip():
                st.warning("Pehle topic likho, photo upload/click karo ya notes paste karo.")
            else:
                with st.spinner("AI sawal bana raha hai…"):
                    try:
                        quiz = generate_with_progress(input_text, num_questions, difficulty, type_keys, language, model, media=media, adaptive=adaptive)
                        if not quiz:
                            st.error("Valid sawal nahi ban paye. Dobara try karo.")
                        else:
                            start_quiz(
                                quiz,
                                {
                                    "label": label, "difficulty": difficulty, "mode": mode, "source": input_text, "media": media,
                                    "types": type_keys, "adaptive": adaptive, "language": language, "model": model, "time_limit": time_limit,
                                    "quiz_limit": quiz_limit, "marks": marks_correct, "neg": neg_frac,
                                },
                            )
                            st.session_state["_picked"] = ""
                            st.rerun()
                    except json.JSONDecodeError:
                        st.error("AI ka response samajh nahi aaya. Dobara try karo.")
                    except Exception as e:
                        st.error(friendly_error(e))

    with tab_pyq:
        # ── TAB 2: GOVT & ENTRANCE EXAM PYQs ──
        st.markdown("### 🏛️ Govt & Entrance Exam PYQs")
        st.caption("Exam aur Subject Select karein — Official negative marking rules automatic apply ho jayenge.")

        with st.container(key="panel_pyq"):
            target_exam = st.selectbox("Target Exam Select Karein:", [
                "SSC CGL", 
                "RRB NTPC", 
                "Banking (IBPS/SBI)", 
                "UP Police Constable", 
                "JEE (Main/Advanced)",
                "NEET UG",
                "UP CNET (B.Sc Nursing Entrance)",
                "AKTU Semester Exams (B.Tech)",
                "UPSC / State PCS", 
                "General All Exams"
            ])
            
            EXAM_SUBJECTS = {
                "SSC CGL": ["All Subjects Mixed", "General Awareness", "Quantitative Aptitude", "Reasoning", "English Comprehension"],
                "RRB NTPC": ["All Subjects Mixed", "General Awareness", "Mathematics", "General Intelligence & Reasoning"],
                "Banking (IBPS/SBI)": ["All Subjects Mixed", "Reasoning Ability", "Quantitative Aptitude", "English Language", "General/Banking Awareness"],
                "UP Police Constable": ["All Subjects Mixed", "General Knowledge", "General Hindi", "Numerical & Mental Ability", "Mental Aptitude/Reasoning"],
                "JEE (Main/Advanced)": ["All Subjects Mixed", "Physics", "Chemistry", "Mathematics"],
                "NEET UG": ["All Subjects Mixed", "Physics", "Chemistry", "Botany", "Zoology"],
                "UP CNET (B.Sc Nursing Entrance)": ["All Subjects Mixed", "Nursing Aptitude", "Physics", "Chemistry", "Biology", "English & General Knowledge"],
                "AKTU Semester Exams (B.Tech)": ["All Subjects Mixed", "Artificial Intelligence & ML", "Data Structures & C++", "Operating Systems", "Engineering Mathematics", "Computer Networks", "DBMS"],
                "UPSC / State PCS": ["All Subjects Mixed", "Indian Polity & Constitution", "History & Culture", "Geography", "Indian Economy", "Environment & Ecology", "General Science"],
                "General All Exams": ["All Subjects Mixed", "General Knowledge", "Mathematics", "Reasoning", "Science"]
            }
            
            subjects_list = EXAM_SUBJECTS.get(target_exam, ["All Subjects Mixed"])
            target_subject = st.selectbox("Subject / Unit Choose Karein:", subjects_list)

            EXAM_MARKING = {
                "SSC CGL": {"marks": 2.0, "neg": 0.25, "info": "+2.0 Sahi | −0.50 Galat (¼ Penalty)"},
                "RRB NTPC": {"marks": 1.0, "neg": 0.333, "info": "+1.0 Sahi | −0.33 Galat (⅓ Penalty)"},
                "Banking (IBPS/SBI)": {"marks": 1.0, "neg": 0.25, "info": "+1.0 Sahi | −0.25 Galat (¼ Penalty)"},
                "UP Police Constable": {"marks": 2.0, "neg": 0.25, "info": "+2.0 Sahi | −0.50 Galat (¼ Penalty)"},
                "JEE (Main/Advanced)": {"marks": 4.0, "neg": 0.25, "info": "+4.0 Sahi | −1.00 Galat (¼ Penalty)"},
                "NEET UG": {"marks": 4.0, "neg": 0.25, "info": "+4.0 Sahi | −1.00 Galat (¼ Penalty)"},
                "UP CNET (B.Sc Nursing Entrance)": {"marks": 1.0, "neg": 0.0, "info": "+1.0 Sahi | No Negative Marking"},
                "AKTU Semester Exams (B.Tech)": {"marks": 2.0, "neg": 0.0, "info": "+2.0 Sahi | No Negative Marking"},
                "UPSC / State PCS": {"marks": 2.0, "neg": 0.333, "info": "+2.0 Sahi | −0.66 Galat (⅓ Penalty)"},
                "General All Exams": {"marks": 1.0, "neg": 0.25, "info": "+1.0 Sahi | −0.25 Galat (¼ Penalty)"}
            }
            
            current_rule = EXAM_MARKING.get(target_exam, EXAM_MARKING["General All Exams"])
            st.info(f"⚖️ **Official Exam Marking:** {current_rule['info']}")

            pyq_dataset = load_pyq_dataset()
            filtered_pyqs = [
                q for q in pyq_dataset 
                if q.get("exam") == target_exam and (target_subject == "All Subjects Mixed" or q.get("subject") == target_subject)
            ]

            if filtered_pyqs:
                st.success(f"✅ {len(filtered_pyqs)} Genuine PYQs found in Database for {target_exam} ({target_subject})!")
            else:
                st.caption(f"ℹ️ Local database contains AI-generated standard PYQs for {target_exam} - {target_subject}.")

        st.write("")
        if st.button(f"🚀 Start {target_exam} ({target_subject}) Practice", type="primary", use_container_width=True, key="btn_start_pyq"):
            with st.spinner(f"Preparing {target_exam} - {target_subject} Questions..."):
                selected_quiz = []
                if filtered_pyqs:
                    raw_items = random.sample(filtered_pyqs, min(num_questions, len(filtered_pyqs)))
                    for item in raw_items:
                        opts = list(item["options"])
                        random.shuffle(opts)
                        selected_quiz.append({
                            "type": "mcq",
                            "question": item["question"],
                            "options": opts,
                            "answer": item["answer"],
                            "explanation": item.get("explanation", ""),
                            "hint": f"Asked in {item.get('year', 'Real Exam')}",
                            "topic": f"{item.get('exam')} ({item.get('subject', target_subject)})",
                            "level": 2
                        })
                else:
                    subj_filter = "" if target_subject == "All Subjects Mixed" else f" specifically for the subject '{target_subject}'"
                    pyq_prompt = f"Generate {num_questions} authentic past year exam questions (PYQs){subj_filter} strictly based on real exam patterns for: {target_exam}. Language: {language}."
                    selected_quiz = generate_with_progress(pyq_prompt, num_questions, difficulty, type_keys, language, model, adaptive=adaptive)

                if selected_quiz:
                    start_quiz(selected_quiz, {
                        "label": f"{target_exam} - {target_subject} PYQ Practice",
                        "difficulty": difficulty, 
                        "mode": mode, 
                        "source": f"{target_exam} ({target_subject})",
                        "types": type_keys, 
                        "adaptive": adaptive, 
                        "language": language, 
                        "model": model,
                        "time_limit": time_limit, 
                        "quiz_limit": quiz_limit, 
                        "marks": current_rule["marks"], 
                        "neg": current_rule["neg"]
                    })
                    st.rerun()

    with tab_doubt:
        # ── TAB 3: DOUBT SOLVER & THEORY ──
        st.markdown("### 🔍 AI Doubt Solver & Concept Explainer")
        st.caption("Question ki photo upload/click karein, text query write karein ya PDF bhejkar detailed theory & step-by-step solution pao.")

        with st.container(key="panel_doubt"):
            doubt_source = st.radio("Query type", ["📝 Question / Text", "🖼️ Photo / Screenshot", "📄 PDF Document"], horizontal=True, key="d_src")
            
            q_text = ""
            d_media = None
            
            if doubt_source.startswith("📝"):
                q_text = st.text_area("Apna doubt / query yahan type karein:", height=150, placeholder="e.g. Explain Binary Search Tree insertion with an example...", key="d_txt")
            elif doubt_source.startswith("🖼️"):
                st.caption("Book page ya question ki photo upload karein ya live photo lein.")
                d_photo_mode = st.radio("Photo Source:", ["📁 Upload File", "📸 Live Camera Click"], horizontal=True, key="doubt_photo_mode")
                
                d_file = None
                if d_photo_mode == "📁 Upload File":
                    d_file = st.file_uploader("Photo upload karein", type=["png", "jpg", "jpeg", "webp"], key="d_img")
                else:
                    d_file = st.camera_input("Question ki Live Photo Click Karein", key="d_cam")

                if d_file:
                    data = d_file.getvalue()
                    st.image(data, caption="Question Photo", use_container_width=True)
                    d_media = {"bytes": data, "mime": getattr(d_file, "type", "image/jpeg") or "image/jpeg"}
                    q_text = st.text_input("Koi extra instruction? (Optional)", placeholder="e.g. Step-by-step solution and key formulas", key="d_img_txt")
            else:
                d_pdf = st.file_uploader("PDF upload karein", type=["pdf"], key="d_pdf")
                if d_pdf:
                    try:
                        q_text, _ = read_pdf(d_pdf, 1, 5)
                        st.success("PDF Content loaded!")
                    except Exception as e:
                        st.error(f"PDF read error: {e}")

        st.write("")
        if st.button("💡 Solution & Theory Samjhao", type="primary", use_container_width=True, key="btn_solve_doubt"):
            if not q_text.strip() and not d_media:
                st.warning("Pehle doubt type karein ya photo upload/click karein.")
            else:
                with st.spinner("AI Doubt solve aur Theory generate kar raha hai..."):
                    try:
                        sys_prompt = f"""You are a helpful and friendly tutor. 
Solve and explain this doubt using **very simple, clear, and easy-to-understand English**.

Format your response using Markdown:
1. **Direct Solution / Answer**: Give a straightforward, simple step-by-step resolution. Avoid complex jargon.
2. **Simple Explanation & Concept**: Explain the core idea in plain English using a simple real-life analogy or easy example.
3. **Key Points to Remember**: 2-3 short bullet points summarizing the main takeaways or formulas.
"""
                        if d_media:
                            b64 = base64.b64encode(d_media["bytes"]).decode()
                            solution_res = llm([
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": [
                                    {"type": "text", "text": q_text or "Solve and explain this uploaded question in simple English."},
                                    {"type": "image_url", "image_url": {"url": f"data:{d_media['mime']};base64,{b64}"}}
                                ]}
                            ], VISION_MODEL)
                        else:
                            solution_res = llm([
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": q_text}
                            ], model)
                            
                        st.markdown("---")
                        st.markdown(solution_res)
                    except Exception as e:
                        st.error(friendly_error(e))

elif st.session_state.stage == "quiz":
    st.title("📝 Quiz Running...")
    st.write("Quiz active hai.")
    if st.button("End Quiz & Return"):
        st.session_state.stage = "setup"
        st.rerun()
