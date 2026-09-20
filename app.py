import json
import streamlit as st
from google import genai
import pypdf
import io

st.set_page_config(
    page_title="AI Mock Test & Revision App", page_icon="📝", layout="wide"
)

st.title("📚 AI Mock Test & Revision App (Testbook Style)")
st.markdown(
    अपने रिटन नोट्स दें और एआई की मदद से अपनी पसंद के प्रश्नों का क्लिकेबल मॉक
     टेस्ट दें!
)

# Sidebar for API Key and Notes Input
with st.sidebar
  st.header(⚙️ सेटिंग्स और नोट्स)
  api_key = st.text_input(Google Gemini API Key दर्ज करें, type=password)
  st.markdown(
      [🔑 फ्री API Key यहाँ से प्राप्त
       करें](httpsaistudio.google.comappapikey)
  )

  st.markdown(---)
  st.subheader(अपने नोट्स यहाँ दें)
  upload_option = st.radio(
      नोट्स देने का तरीका चुनें, (टेक्स्ट पेस्ट करें, PDF फाइल अपलोड करें)
  )

  notes_text = 
  if upload_option == टेक्स्ट पेस्ट करें
    notes_text = st.text_area(
        यहाँ अपने नोट्स पेस्ट करें,
        height=200,
        placeholder=अपने इतिहास, विज्ञान या अन्य विषयों के नोट्स यहाँ लिखें...,
    )
  else
    uploaded_file = st.file_uploader(
        अपनी नोट्स PDF फाइल अपलोड करें, type=[pdf]
    )
    if uploaded_file is not None
      reader = pypdf.PdfReader(uploaded_file)
      for page in reader.pages
        notes_text += page.extract_text() + n

  num_questions = st.slider(प्रश्नों की संख्या चुनें, 5, 40, 15)
  generate_btn = st.button(🚀 मॉक टेस्ट जनरेट करें)

# Session state initialization
if quiz_data not in st.session_state
  st.session_state.quiz_data = None
if submitted not in st.session_state
  st.session_state.submitted = False
if user_answers not in st.session_state
  st.session_state.user_answers = {}

if generate_btn
  if not api_key
    st.error(कृपया अपनी Gemini API Key दर्ज करें!)
  elif not notes_text.strip()
    st.error(कृपया नोट्स दर्ज करें या PDF अपलोड करें!)
  else
    with st.spinner(
        एआई आपके नोट्स से प्रश्न तैयार कर रहा है, कृपया प्रतीक्षा करें...
    )
      try
        client = genai.Client(api_key=api_key)
        prompt = f
                You are an expert exam creator. Based on the following study notes, generate exactly {num_questions} multiple-choice questions (MCQs) in strict JSON format. 
                Each question must have 4 options, the correct option string (exact match with one of the options), and a detailed explanation.
                
                Return ONLY a valid JSON array in this exact format, with no extra text or markdown wrapping outside JSON
                [
                  {{
                    question Question text here,
                    options [Option A, Option B, Option C, Option D],
                    correct Option A,
                    explanation Detailed explanation here.
                  }}
                ]

                Notes
                {notes_text[15000]}
                

        response = client.models.generate_content(
            model=gemini-2.5-flash,
            contents=prompt,
        )

        text_resp = response.text.strip()
        if text_resp.startswith(```json)
          text_resp = text_resp[7]
        if text_resp.endswith(```)
          text_resp = text_resp[-3]

        quiz_data = json.loads(text_resp.strip())
        st.session_state.quiz_data = quiz_data
        st.session_state.submitted = False
        st.session_state.user_answers = {}
        st.success(मॉक टेस्ट सफलतापूर्वक तैयार हो गया है!)
      except Exception as e
        st.error(fत्रुटि (Error) {e})

# Display Quiz if available
if st.session_state.quiz_data
  quiz = st.session_state.quiz_data
  st.markdown(---)
  st.subheader(f📝 मॉक टेस्ट (कुल प्रश्न {len(quiz)}))

  with st.form(quiz_form)
    for i, q in enumerate(quiz)
      st.markdown(fप्रश्न {i+1} {q['question']})
      user_ans = st.radio(
          fविकल्प चुनें (Q{i+1}),
          q[options],
          key=fq_{i},
          index=None,
          disabled=st.session_state.submitted,
      )
      st.session_state.user_answers[i] = user_ans
      st.markdown(---)

    submit_test = st.form_submit_button(✅ टेस्ट सबमिट करें)

    if submit_test
      st.session_state.submitted = True
      st.rerun()

# Show Results if submitted
if st.session_state.submitted and st.session_state.quiz_data
  quiz = st.session_state.quiz_data
  score = 0
  total = len(quiz)

  st.markdown(---)
  st.header(📊 टेस्ट परिणाम और सॉल्यूशन (Test Results & Solutions))

  for i, q in enumerate(quiz)
    user_ans = st.session_state.user_answers.get(i)
    correct_ans = q[correct]

    if user_ans == correct_ans
      score += 1
      st.success(
          fप्रश्न {i+1} सही! ✅nnआपका उत्तर {user_ans}nn💡
          f स्पष्टीकरण {q['explanation']}
      )
    elif user_ans is None
      st.warning(
          fप्रश्न {i+1} आपने उत्तर नहीं दिया। ⚠️nnसही उत्तर
          f `{correct_ans}`nn💡 स्पष्टीकरण {q['explanation']}
      )
    else
      st.error(
          fप्रश्न {i+1} गलत! ❌nnआपका उत्तर {user_ans}  सही उत्तर
          f `{correct_ans}`nn💡 स्पष्टीकरण {q['explanation']}
      )

  st.markdown(---)
  st.markdown(### 🏆 आपका कुल स्कोर)
  st.metric(label=अंक, value=f{score}  {total})
