import json
import streamlit as st
from google import genai
import pypdf
import io

st.set_page_config(
    page_title="AI Mock Test and Revision App", page_icon="📝", layout="wide"
)

st.title("AI Mock Test and Revision App (Testbook Style)")
st.markdown(
    "अपने रिटन नोट्स दें और एआई की मदद से अपनी पसंद के प्रश्नों का क्लिकेबल मॉक"
    " टेस्ट दें!"
)

# Sidebar for API Key and Notes Input
with st.sidebar:
  st.header("Settings and Notes")
  api_key = st.text_input("Google Gemini API Key darj karein", type="password")
  st.markdown(
      "[Free API Key yahan se prapt"
      " karein](https://aistudio.google.com/app/apikey)"
  )

  st.markdown("---")
  st.subheader("Apne notes yahan dein:")
  upload_option = st.radio(
      "Notes dene ka tarika chunen:", ("Text paste karein", "PDF file upload karein")
  )

  notes_text = ""
  if upload_option == "Text paste karein":
    notes_text = st.text_area(
        "Yahan apne notes paste karein:",
        height=200,
        placeholder="Apne itihaas, vigyan ya anya vishayon ke notes yahan likhein...",
    )
  else:
    uploaded_file = st.file_uploader(
        "Apni notes PDF file upload karein", type=["pdf"]
    )
    if uploaded_file is not None:
      reader = pypdf.PdfReader(uploaded_file)
      for page in reader.pages:
        notes_text += page.extract_text() + "\n"

  num_questions = st.slider("Prashnon ki sankhya chunen:", 5, 40, 15)
  generate_btn = st.button("Mock Test Generate Karein")

# Session state initialization
if "quiz_data" not in st.session_state:
  st.session_state.quiz_data = None
if "submitted" not in st.session_state:
  st.session_state.submitted = False
if "user_answers" not in st.session_state:
  st.session_state.user_answers = {}

if generate_btn:
  if not api_key:
    st.error("Kripya apni Gemini API Key darj karein!")
  elif not notes_text.strip():
    st.error("Kripya notes darj karein ya PDF upload karein!")
  else:
    with st.spinner(
        "AI aapke notes se prashn taiyar kar raha hai, kripya pratiksha karein..."
    ):
      try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
                You are an expert exam creator. Based on the following study notes, generate exactly {num_questions} multiple-choice questions (MCQs) in strict JSON format. 
                Each question must have 4 options, the correct option string (exact match with one of the options), and a detailed explanation.
                
                Return ONLY a valid JSON array in this exact format, with no extra text or markdown wrapping outside JSON:
                [
                  {{
                    "question": "Question text here?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct": "Option A",
                    "explanation": "Detailed explanation here."
                  }}
                ]

                Notes:
                {notes_text[:15000]}
                """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
          text_resp = text_resp[7:]
        if text_resp.endswith("```"):
          text_resp = text_resp[:-3]

        quiz_data = json.loads(text_resp.strip())
        st.session_state.quiz_data = quiz_data
        st.session_state.submitted = False
        st.session_state.user_answers = {}
        st.success("Mock test safaltapoorvak taiyar ho gaya hai!")
      except Exception as e:
        st.error(f"Error: {e}")

# Display Quiz if available
if st.session_state.quiz_data:
  quiz = st.session_state.quiz_data
  st.markdown("---")
  st.subheader(f"Mock Test (Kul Prashn: {len(quiz)})")

  with st.form("quiz_form"):
    for i, q in enumerate(quiz):
      st.markdown(f"**Prashn {i+1}: {q['question']}**")
      user_ans = st.radio(
          f"Vikalp chunen (Q{i+1})",
          q["options"],
          key=f"q_{i}",
          index=None,
          disabled=st.session_state.submitted,
      )
      st.session_state.user_answers[i] = user_ans
      st.markdown("---")

    submit_test = st.form_submit_button("Test Submit Karein")

    if submit_test:
      st.session_state.submitted = True
      st.rerun()

# Show Results if submitted
if st.session_state.submitted and st.session_state.quiz_data:
  quiz = st.session_state.quiz_data
  score = 0
  total = len(quiz)

  st.markdown("---")
  st.header("Test Parinam aur Solution")

  for i, q in enumerate(quiz):
    user_ans = st.session_state.user_answers.get(i)
    correct_ans = q["correct"]

    if user_ans == correct_ans:
      score += 1
      st.success(
          f"**Prashn {i+1}: Sahi!**\n\nAapka uttar: {user_ans}\n\n"
          f"**Spashtikaran:** {q['explanation']}"
      )
    elif user_ans is None:
      st.warning(
          f"**Prashn {i+1}: Aapne uttar nahi diya.**\n\nSahi uttar:"
          f" `{correct_ans}`\n\n**Spashtikaran:** {q['explanation']}"
      )
    else:
      st.error(
          f"**Prashn {i+1}: Galat!**\n\nAapka uttar: {user_ans} | Sahi uttar:"
          f" `{correct_ans}`\n\n**Spashtikaran:** {q['explanation']}"
      )

  st.markdown("---")
  st.markdown("### Aapka Kul Score")
  st.metric(label="Ank", value=f"{score} / {total}")
