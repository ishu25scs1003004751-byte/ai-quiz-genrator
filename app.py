import os
import json
import streamlit as st
from pypdf import PdfReader
from groq import Groq

# Page Config
st.set_page_config(page_title="AI Quiz Generator", page_icon="🧠", layout="wide")

# API Key Setup (Groq)
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API Key nahi mili! Streamlit Cloud Secrets me GROQ_API_KEY add karein.")
    st.stop()

client = Groq(api_key=api_key)
# Session State
if "stage" not in st.session_state:
    st.session_state.stage = "setup"
if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "answers" not in st.session_state:
    st.session_state.answers = {}

def clean_json(raw: str):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

def generate_quiz(text, num_q, diff, qtype, lang):
    prompt = f"""You are an expert teacher. Create {num_q} quiz questions based on the content below.
Difficulty: {diff}. Type: {qtype}. Language: {lang}.

Return ONLY a valid JSON array of objects with keys: "question", "options" (array of 4 strings), "answer" (exact text of correct option), "explanation".
Content:
{text}
"""
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a JSON generator. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        response_format={"type": "json_object"}
    )
    
    res_text = completion.choices[0].message.content
    data = clean_json(res_text)
    # Extract array if wrapped in object
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return data

# Sidebar
st.sidebar.header("⚙️ Quiz Settings")
num_questions = st.sidebar.slider("Number of Questions", 3, 15, 5)
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
qtype = st.sidebar.selectbox("Question Type", ["Multiple Choice", "True / False"])
language = st.sidebar.selectbox("Language", ["English", "Hinglish", "Hindi"])

st.title("🧠 AI Quiz Generator (Powered by Groq)")
st.write("Topic likho ya PDF upload karo aur instant Quiz pao!")
st.divider()

# STAGE 1: SETUP
if st.session_state.stage == "setup":
    option = st.radio("Choose Input Type:", ("Topic / Text", "PDF Upload"))
    input_text = ""

    if option == "Topic / Text":
        input_text = st.text_area("Topic ya Text yahan likho:", height=150, placeholder="Example: Python lists, Data Science basics...")
    else:
        uploaded_file = st.file_uploader("PDF File Upload Karo", type=["pdf"])
        if uploaded_file is not None:
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    input_text += extracted + "\n"
            st.success("PDF Read Successful!")

    if st.button("✨ Quiz Banao", type="primary"):
        if not input_text.strip():
            st.warning("Kripya pehle text likhein ya PDF upload karein!")
        else:
            with st.spinner("AI Quiz generate kar raha hai..."):
                try:
                    quiz_data = generate_quiz(input_text, num_questions, difficulty, qtype, language)
                    st.session_state.quiz = quiz_data
                    st.session_state.stage = "quiz"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error aaya: {e}")

# STAGE 2: QUIZ
elif st.session_state.stage == "quiz":
    quiz = st.session_state.quiz
    st.subheader("📝 Answer the Questions")
    
    with st.form("quiz_form"):
        user_answers = {}
        for idx, q in enumerate(quiz):
            st.markdown(f"**Q{idx+1}: {q['question']}**")
            user_answers[idx] = st.radio(
                "Options:", 
                q["options"], 
                key=f"q_{idx}",
                index=None
            )
            st.write("---")
            
        submitted = st.form_submit_button("Submit Answers 🚀")
        if submitted:
            st.session_state.answers = user_answers
            st.session_state.stage = "result"
            st.rerun()

# STAGE 3: RESULT
elif st.session_state.stage == "result":
    quiz = st.session_state.quiz
    answers = st.session_state.answers
    score = 0
    
    st.subheader("📊 Quiz Results")
    for idx, q in enumerate(quiz):
        selected = answers.get(idx)
        correct = q["answer"]
        
        if selected == correct:
            score += 1
            st.success(f"**Q{idx+1}: Correct!** ✅")
        else:
            st.error(f"**Q{idx+1}: Incorrect!** ❌ (Aapka Answer: {selected} | Sahi Answer: {correct})")
        
        st.caption(f"💡 Explanation: {q['explanation']}")
        st.write("---")
        
    st.balloons()
    st.info(f"**Final Score: {score} / {len(quiz)}**")
    
    if st.button("🔁 Clear & Start New Quiz"):
        st.session_state.stage = "setup"
        st.session_state.quiz = []
        st.session_state.answers = {}
        st.rerun()
