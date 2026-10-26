import os
import json
import streamlit as st
from pypdf import PdfReader
from google import genai

# Fetch API Key from Streamlit Secrets or Environment Variable
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="AI Quiz Generator", page_icon="❓", layout="wide")

st.title("🤖 AI Quiz Generator")
st.write("Apna topic likho ya PDF upload karo aur instant Quiz pao!")

if not api_key:
    st.error("API Key nahi mili! Streamlit Cloud me Secrets setup karein.")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=api_key)

# Sidebar options
st.sidebar.header("Quiz Settings")
num_questions = st.sidebar.slider("Number of Questions", min_value=3, max_value=15, value=5)
difficulty = st.sidebar.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])

# Input Selection
option = st.radio("Choose Input Type:", ("Topic / Text", "PDF Upload"))

input_text = ""

if option == "Topic / Text":
    input_text = st.text_area("Topic ya Text yahan likho:", height=150, placeholder="Example: Machine Learning basics ya Python Data Structures...")
else:
    uploaded_file = st.file_uploader("PDF File Upload Karo", type=["pdf"])
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                input_text += extracted + "\n"
        st.success("PDF successfully read!")

# Function to generate quiz using Gemini API
def generate_quiz(text, num_q, diff):
    prompt = f"""
    You are an expert quiz generator. Generate {num_q} multiple-choice questions based on the following content.
    Difficulty level: {diff}.

    Content:
    {text}

    Return the response ONLY in a valid JSON array format. Do not add markdown backticks like ```json or text before/after.
    The output format must strictly be:
    [
        {{
            "question": "Question text here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Correct Option exact text",
            "explanation": "Short explanation why this is correct"
        }}
    ]
    """
    
    response = client.models.generate_content(
        model="openai/gpt-oss-120b",
        contents=prompt
    )
    return response.text

if st.button("Generate Quiz 🚀"):
    if not input_text.strip():
        st.warning("Kripya pehle text likhein ya PDF upload karein!")
    else:
        with st.spinner("Quiz generate ho raha hai..."):
            try:
                raw_response = generate_quiz(input_text, num_questions, difficulty)
                
                # Clean up if markdown code blocks were returned
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                
                quiz_data = json.loads(cleaned_response.strip())
                st.session_state["quiz"] = quiz_data
                st.success("Quiz Ready!")
            except Exception as e:
                st.error(f"Quiz generate karne me error aaya: {e}")

# Display Quiz
if "quiz" in st.session_state:
    st.subheader("📝 Your Quiz")
    quiz = st.session_state["quiz"]
    
    user_answers = {}
    with st.form("quiz_form"):
        for idx, q in enumerate(quiz):
            st.markdown(f"**Q{idx+1}: {q['question']}**")
            user_answers[idx] = st.radio(
                f"Select answer for Q{idx+1}:", 
                q["options"], 
                key=f"q_{idx}",
                index=None
            )
            st.write("---")
            
        submitted = st.form_submit_button("Submit Answers")
        
    if submitted:
        score = 0
        st.subheader("📊 Quiz Results")
        for idx, q in enumerate(quiz):
            selected = user_answers.get(idx)
            correct = q["answer"]
            
            if selected == correct:
                score += 1
                st.success(f"**Q{idx+1}: Correct!** ✅")
            else:
                st.error(f"**Q{idx+1}: Incorrect!** ❌ (Aapka Answer: {selected} | Sahi Answer: {correct})")
            
            st.caption(f"💡 Explanation: {q['explanation']}")
            st.write("")
            
        st.balloons()
        st.info(f"**Final Score:** {score} / {len(quiz)}")
