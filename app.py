import json
import sqlite3
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Smart Mock Test App", page_icon="📝", layout="wide"
)

# Database setup for Question Bank
DB_FILE = "question_bank.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            options TEXT,
            correct TEXT,
            explanation TEXT,
            asked INTEGER DEFAULT 0
        )
    """)
  conn.commit()
  conn.close()


init_db()

st.title("AI Smart Mock Test & Revision App (Handwritten Notes Supported)")
st.markdown(
    "Apne haath se likhe notes ki photo wali PDF upload karein, AI use"
    " direct padh kar smart Question Bank bana dega!"
)

# Sidebar
with st.sidebar:
  st.header("Settings & Notes")
  api_key = st.text_input("Google Gemini API Key darj karein", type="password")
  st.markdown(
      "[Free API Key yahan se prapt"
      " karein](https://aistudio.google.com/app/apikey)"
  )

  st.markdown("---")
  st.subheader("Apne notes yahan dein:")
  upload_option = st.radio(
      "Notes ka tarika:", ("Text paste karein", "PDF upload karein")
  )

  notes_text = ""
  uploaded_file = None

  if upload_option == "Text paste karein":
    notes_text = st.text_area(
        "Apne notes yahan paste karein:",
        height=150,
        placeholder="Apne vishay ke notes yahan likhein...",
    )
  else:
    uploaded_file = st.file_uploader(
        "Haath se likhe notes ki PDF upload karein", type=["pdf"]
    )

  pool_size = st.slider(
      "Question Bank mein kul kitne prashn banayein?", 50, 200, 100, step=50
  )
  build_bank_btn = st.button("Smart Question Bank Banayein")

# Handle Question Bank Generation
if build_bank_btn:
  if not api_key:
    st.error("Kripya apni Gemini API Key darj karein!")
  elif upload_option == "Text paste karein" and not notes_text.strip():
    st.error("Kripya notes darj karein!")
  elif upload_option == "PDF upload karein" and uploaded_file is None:
    st.error("Kripya PDF file upload karein!")
  else:
    with st.spinner(
        "AI aapke haath se likhe notes ki PDF ko padh raha hai aur Question"
        " Bank taiyar kar raha hai..."
    ):
      try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
                You are an expert exam creator. Based on the provided study notes (which may contain handwritten text or images), analyze them thoroughly and generate exactly {pool_size} diverse multiple-choice questions (MCQs) covering all topics in strict JSON format. 
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
                """

        if upload_option == "PDF upload karein" and uploaded_file is not None:
          pdf_bytes = uploaded_file.getvalue()
          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=[
                  types.Part.from_bytes(
                      data=pdf_bytes, mime_type="application/pdf"
                  ),
                  prompt,
              ],
          )
        else:
          full_prompt = f"{prompt}\n\nNotes:\n{notes_text[:25000]}"
          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=full_prompt,
          )

        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
          text_resp = text_resp[7:]
        if text_resp.endswith("```"):
          text_resp = text_resp[:-3]

        questions_list = json.loads(text_resp.strip())

        # Save to SQLite Database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions")  # Purana bank clear karein
        for q in questions_list:
          cursor.execute(
              """
                        INSERT INTO questions (question, options, correct, explanation, asked)
                        VALUES (?, ?, ?, ?, 0)
                    """,
              (
                  q["question"],
                  json.dumps(q["options"]),
                  q["correct"],
                  q["explanation"],
              ),
          )
        conn.commit()
        conn.close()
        st.success(
            f"Safaltapoorvak {len(questions_list)} prashnon ka Smart Question"
            " Bank taiyar ho gaya hai!"
        )
      except Exception as e:
        st.error(f"Error: {e}")

# Check Database stats
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM questions")
total_q = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM questions WHERE asked = 0")
unasked_q = cursor.fetchone()[0]
conn.close()

st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("Bank mein Kul Prashn", total_q)
col2.metric("Bache hue Naye Prashn", unasked_q)
col3.metric("Puche ja chuke Prashn", total_q - unasked_q)

# Daily Test Section
st.markdown("---")
st.subheader("Daily Mock Test (No-Repeat Mode)")
test_size = st.slider("Aaj ke test mein kitne prashn chahiye?", 10, 50, 40)
start_test_btn = st.button("Aaj ka Naya Test Shuru Karein")

if "current_test" not in st.session_state:
  st.session_state.current_test = None
if "test_submitted" not in st.session_state:
  st.session_state.test_submitted = False
if "test_answers" not in st.session_state:
  st.session_state.test_answers = {}

if start_test_btn:
  if total_q == 0:
    st.warning("Pehle sidebar se apni PDF dekar 'Smart Question Bank' banayein!")
  else:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question, options, correct, explanation FROM questions WHERE"
        " asked = 0 ORDER BY RANDOM() LIMIT ?",
        (test_size,),
    )
    rows = cursor.fetchall()

    if len(rows) < test_size:
      cursor.execute("UPDATE questions SET asked = 0")
      conn.commit()
      cursor.execute(
          "SELECT id, question, options, correct, explanation FROM questions"
          " ORDER BY RANDOM() LIMIT ?",
          (test_size,),
      )
      rows = cursor.fetchall()

    conn.close()

    if not rows:
      st.error("Koi prashn uplabdh nahi hai!")
    else:
      test_data = []
      for r in rows:
        test_data.append({
            "id": r[0],
            "question": r[1],
            "options": json.loads(r[2]),
            "correct": r[3],
            "explanation": r[4],
        })
      st.session_state.current_test = test_data
      st.session_state.test_submitted = False
      st.session_state.test_answers = {}
      st.success(f"Aaj ka {len(test_data)} prashnon ka naya test taiyar hai!")

# Render Test
if st.session_state.current_test:
  test_q = st.session_state.current_test
  st.markdown(f"### Mock Test (Total: {len(test_q)} Questions)")

  with st.form("daily_test_form"):
    for i, q in enumerate(test_q):
      st.markdown(f"**Prashn {i+1}: {q['question']}**")
      ans = st.radio(
          f"Vikalp chunen Q{i+1}",
          q["options"],
          key=f"daily_q_{q['id']}",
          index=None,
          disabled=st.session_state.test_submitted,
      )
      st.session_state.test_answers[q["id"]] = ans
      st.markdown("---")

    submit_btn = st.form_submit_button("Test Submit Karein")

    if submit_btn:
      st.session_state.test_submitted = True
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      for q in test_q:
        cursor.execute("UPDATE questions SET asked = 1 WHERE id = ?", (q["id"],))
      conn.commit()
      conn.close()
      st.rerun()

# Show Results and Solutions
if st.session_state.test_submitted and st.session_state.current_test:
  test_q = st.session_state.current_test
  score = 0
  total = len(test_q)

  st.markdown("---")
  st.header("Test Parinam aur Solution (Results & Explanations)")

  for i, q in enumerate(test_q):
    user_ans = st.session_state.test_answers.get(q["id"])
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
  st.metric(label="Score", value=f"{score} / {total}")
