import json
import sqlite3
import time
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Smart Hindi Revision App", page_icon="📚", layout="wide"
)

# Database setup with UNIQUE constraint to prevent duplicates
DB_FILE = "question_bank.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE,
            options TEXT,
            correct TEXT,
            explanation TEXT,
            asked INTEGER DEFAULT 0
        )
    """)
  conn.commit()
  conn.close()


init_db()

st.title("AI Smart Hindi Revision & Mock Test App (Advanced Manager)")
st.markdown(
    "Apne notes upload karein. Ab aap **Question Bank dekh sakte hain** aur"
    " kisi bhi sawal ko **ek-ek karke delete** bhi kar sakte hain!"
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
      "Notes ka tarika:", ("Text paste karein", "Files (PDF/Images) Upload karein")
  )

  notes_text = ""
  uploaded_files = None

  if upload_option == "Text paste karein":
    notes_text = st.text_area(
        "Apne notes yahan paste karein:",
        height=150,
        placeholder="Apne vishay ke notes yahan likhein...",
    )
  else:
    uploaded_files = st.file_uploader(
        "Apne notes ki Photos (JPG/PNG) ya PDF select karein",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

  st.info(
      "💡 Note: Duplicate questions automatically filter ho jayenge. Sirf naye"
      " unique sawal judenge!"
  )
  build_bank_btn = st.button("Smart Questions Jodein")


# Function with auto-retry for 503 errors
def call_gemini_with_retry(client, model, contents, config, max_retries=3):
  delay = 3
  for attempt in range(max_retries):
    try:
      return client.models.generate_content(
          model=model, contents=contents, config=config
      )
    except Exception as e:
      error_str = str(e)
      if (
          "503" in error_str
          or "UNAVAILABLE" in error_str
          or "high demand" in error_str
      ):
        if attempt < max_retries - 1:
          time.sleep(delay)
          delay *= 2
          continue
      raise e


# Handle Question Bank Generation safely
if build_bank_btn:
  if not api_key:
    st.error("Kripya apni Gemini API Key darj karein!")
  elif upload_option == "Text paste karein" and not notes_text.strip():
    st.error("Kripya notes darj karein!")
  elif upload_option == "Files (PDF/Images) Upload karein" and not uploaded_files:
    st.error("Kripya kam se kam ek PDF ya Image file upload karein!")
  else:
    with st.spinner(
        "AI aapke notes ko padh raha hai aur HINDI questions jod raha hai..."
    ):
      try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
                You are an expert exam creator and educator. Thoroughly analyze all the provided study notes, images, and documents. 
                CRITICAL INSTRUCTIONS:
                1. Generate a comprehensive batch of multiple-choice questions (MCQs) covering as many topics, dates, facts, and tables as possible. Ensure JSON output is well-formed.
                2. Language: Every single question, all 4 options, the correct answer string, and the detailed explanation must be written STRICTLY in the HINDI language (हिंदी भाषा में).
                
                Return ONLY a valid JSON array in this exact format, with no extra text or markdown wrapping outside JSON:
                [
                  {{
                    "question": "Question text in Hindi?",
                    "options": ["Option A in Hindi", "Option B in Hindi", "Option C in Hindi", "Option D in Hindi"],
                    "correct": "Option A in Hindi",
                    "explanation": "Detailed explanation in Hindi."
                  }}
                ]
                """

        generation_config = types.GenerateContentConfig(
            max_output_tokens=8192, temperature=0.3
        )

        if (
            upload_option == "Files (PDF/Images) Upload karein"
            and uploaded_files
        ):
          contents_list = []
          for file in uploaded_files:
            file_bytes = file.getvalue()
            mime_type = file.type
            contents_list.append(
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            )
          contents_list.append(prompt)

          response = call_gemini_with_retry(
              client,
              "gemini-3.6-flash",
              contents_list,
              config=generation_config,
          )
        else:
          full_prompt = f"{prompt}\n\nNotes:\n{notes_text[:50000]}"
          response = call_gemini_with_retry(
              client,
              "gemini-3.6-flash",
              full_prompt,
              config=generation_config,
          )

        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
          text_resp = text_resp[7:]
        if text_resp.endswith("```"):
          text_resp = text_resp[:-3]

        questions_list = json.loads(text_resp.strip())

        # Save to SQLite Database using INSERT OR IGNORE
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        added_count = 0

        for q in questions_list:
          cursor.execute(
              """
                        INSERT OR IGNORE INTO questions (question, options, correct, explanation, asked)
                        VALUES (?, ?, ?, ?, 0)
                    """,
              (
                  q["question"],
                  json.dumps(q["options"]),
                  q["correct"],
                  q["explanation"],
              ),
          )
          if cursor.rowcount > 0:
            added_count += 1

        conn.commit()
        conn.close()
        st.success(
            f"Safaltapoorvak {added_count} naye unique prashn HINDI mein jod"
            " diye gaye hain!"
        )
      except json.JSONDecodeError:
        st.error(
            "Error: AI response format cut gaya. Kripya 'Smart Questions Jodein'"
            " par dobara click karein!"
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

# --- QUESTION BANK MANAGEMENT SECTION (View & Individual Delete) ---
st.markdown("---")
with st.expander(
    "📋 Question Bank Management (Sawal Dekhein aur Delete Karein)",
    expanded=False,
):
  st.subheader("Saved Questions List")
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("SELECT id, question, correct, explanation FROM questions")
  all_questions = cursor.fetchall()
  conn.close()

  if not all_questions:
    st.info("Question Bank abhi khali hai.")
  else:
    st.write(f"Kul Saved Prashn: {len(all_questions)}")

    for idx, (q_id, q_text, q_correct, q_exp) in enumerate(all_questions, 1):
      cols = st.columns([0.85, 0.15])
      with cols[0]:
        st.markdown(
            f"**{idx}. {q_text}**\n\n*Sahi Uttar:* `{q_correct}`\n\n*Spashtikaran:"
            f"* {q_exp}"
        )
      with cols[1]:
        if st.button("Delete", key=f"del_q_{q_id}"):
          conn = sqlite3.connect(DB_FILE)
          cursor = conn.cursor()
          cursor.execute("DELETE FROM questions WHERE id = ?", (q_id,))
          conn.commit()
          conn.close()
          st.success(f"Prashn ID {q_id} delete kar diya gaya!")
          st.rerun()
      st.markdown("---")

    # Clear All Button
    if st.button(
        "⚠️ Sabhi Questions Ek Saath Delete Karein (Reset Bank)", type="primary"
    ):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute("DELETE FROM questions")
      conn.commit()
      conn.close()
      st.warning("Question Bank poori tarah clear kar diya gaya hai!")
      st.rerun()

# Daily Test Section
st.markdown("---")
st.subheader("Daily Mock Test (No-Repeat Mode)")
test_size = st.slider("Aaj ke test mein kitne prashn chahiye?", 10, 60, 40)
start_test_btn = st.button("Aaj ka Naya Test Shuru Karein")

if "current_test" not in st.session_state:
  st.session_state.current_test = None
if "test_submitted" not in st.session_state:
  st.session_state.test_submitted = False
if "test_answers" not in st.session_state:
  st.session_state.test_answers = {}

if start_test_btn:
  if total_q == 0:
    st.warning("Pehle sidebar se apni files dekar Question Bank banayein!")
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
