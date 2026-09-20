import streamlit as st
import os

# Page Configuration
st.set_page_config(
    page_title="AI Smart Hindi Revision App",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Smart Hindi Revision App")
st.markdown("Your interactive AI tutor for handling large Hindi literature, grammar, and quick chapter reviews.")

# Sidebar Navigation
st.sidebar.header("Revision Mode")
option = st.sidebar.selectbox(
    "Choose a feature:",
    ["Chapter Summary & Notes", "AI Quiz Generator", "Grammar & Answer Checker"]
)

# Helper function to read uploaded files or text safely
def process_large_text(uploaded_file, text_input):
    if uploaded_file is not None:
        try:
            # Read text file content safely
            bytes_data = uploaded_file.read()
            text = bytes_data.decode("utf-8")
            return text
        except Exception as e:
            st.error(f"फ़ाइल पढ़ने में त्रुटि: {e}")
            return ""
    return text_input

# Feature 1: Chapter Summary & Notes (With File Upload for Large Data)
if option == "Chapter Summary & Notes":
    st.header("📖 Chapter Summary & Key Notes Generator")
    st.markdown("बड़े डेटा या पूरी किताब के अध्यायों को आसानी से प्रोसेस करने के लिए आप **फाइल अपलोड** कर सकते हैं या नीचे टेक्स्ट पेस्ट कर सकते हैं।")
    
    # File uploader for large data (.txt or documents)
    uploaded_file = st.file_uploader("बड़ा डेटा या अध्याय फ़ाइल अपलोड करें (.txt)", type=["txt"])
    
    # Text area as an alternative or supplementary input
    chapter_text_input = st.text_area("या यहाँ अपना हिंदी चैप्टर/डेटा पेस्ट करें:", height=150)
    
    # Get final text from either file or text area
    final_text = process_large_text(uploaded_file, chapter_text_input)
    
    if st.button("Generate Revision Notes"):
        if final_text.strip():
            # Display stats about data size handled
            words_count = len(final_text.split())
            st.success(f"डेटा सफलताપूर्वक फीड हो गया! कुल शब्द (Words): {words_count}")
            
            st.markdown("### **महत्वपूर्ण बिंदु (Key Points & Summary):**")
            # यहाँ आप अपने AI Model (जैसे Gemini API) को 'final_text' भेज सकते हैं
            st.markdown("- यह अध्याय आपके द्वारा दिए गए बड़े डेटा के आधार पर सारांशित किया गया है।")
            st.markdown("- मुख्य बिंदु 1: ...")
            st.markdown("- मुख्य बिंदु 2: ...")
        else:
            st.warning("कृपया कोई फ़ाइल अपलोड करें या टेक्स्ट बॉक्स में डेटा दर्ज करें।")

# Feature 2: AI Quiz Generator
elif option == "AI Quiz Generator":
    st.header("❓ Interactive Hindi Quiz")
    topic = st.text_input("Enter the topic or chapter name for the quiz:")
    
    if st.button("Create Quiz"):
        if topic.strip():
            st.info(f"Generating questions for: {topic}")
            st.markdown("**प्रश्न 1:** पाठ के अनुसार लेखक का मुख्य उद्देश्य क्या था?")
            st.radio("Select option:", ["विकल्प क", "विकल्प ख", "विकल्प ग", "विकल्प घ"])
        else:
            st.warning("Please enter a topic name.")

# Feature 3: Grammar & Answer Checker
elif option == "Grammar & Answer Checker":
    st.header("✍️ Hindi Grammar & Answer Evaluator")
    student_answer = st.text_area("Write your Hindi answer or paragraph here:")
    
    if st.button("Evaluate Answer"):
        if student_answer.strip():
            st.markdown("### **मूल्यांकन और सुधार (Evaluation & Feedback):**")
            st.info("आपके उत्तर की संरचना अच्छी है। कृपया वर्तनी (Spelling) और मात्राओं पर थोड़ा ध्यान दें।")
        else:
            st.warning("Please type your answer.")
