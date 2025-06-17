import streamlit as st
from multimodal_extractor import extract_content_from_pdf
import google.generativeai as genai
import os

# --- Page Configuration ---
st.set_page_config(page_title="Intelligent Exam Formatter", page_icon="🧠", layout="wide")

# --- AI Prompt: The Core Logic ---
# This detailed prompt, using your example, is the key to getting the perfect output.
SYSTEM_PROMPT = """
You are a highly intelligent document processing expert. Your task is to analyze the provided content from an exam paper PDF (which includes text and images) and reformat it into a perfectly clean, structured text file.

**YOUR PRIMARY GOAL:** For each question, you must identify all its parts (question text, statements, conclusions, options) and structure the output exactly like this example:

--- START OF EXAMPLE ---
Q.1 Read the given statements and conclusions carefully. Assuming that the information given in the statements is true, even if it appears to be at variance with commonly known facts, decide which of the given conclusions logically follow(s) from the statements.

Statements:
All wires are chargers.
Some chargers are phones.
All chargers are equipment.

Conclusions:
I. Some equipment are phones.
II. All wires are phones.

Options:
1. Only conclusion II follows
2. Both the conclusions follow
3. Only conclusion I follows
4. Neither conclusion I nor II follows
--- END OF EXAMPLE ---

**DETAILED INSTRUCTIONS:**
1.  **Identify Each Question**: A new question starts with "Q." followed by a number.
2.  **Apply Exact Formatting**: For every question, apply the precise format shown in the example. Create "Statements:", "Conclusions:", and "Options:" headings only if they apply to that specific question.
3.  **Handle Math & Diagrams**: If you encounter an image of a mathematical equation, formula, circuit, or diagram, you MUST convert it to a clean LaTeX representation. Enclose LaTeX in `$$...$$` and place it where the image originally appeared.
4.  **Identify the Correct Answer**: The correct option is marked with a "☑" symbol. Note the number of this correct option (1, 2, 3, or 4) for the answer key.
5.  **Final Document Structure**:
    * **Part 1: Questions**: List all the questions, fully formatted as per the example, one after another. Use a `---` line to separate each question.
    * **Part 2: Answer Key**: After all questions are listed, create a final section titled `## 🔑 Answer Key`. In this section, list the correct answer number for every question. For example: `1. 3, 2. 1, 3. 4, ...`
6.  **Strict Filtering**: You MUST NOT include any of the following in your final output:
    * The words "testbook.com", "GET IT ON Google Play", or any other branding.
    * Any URLs or file paths.
    * Extraneous metadata like "Question ID:", "Status:", or "Chosen Option:".
    * Any of your own commentary. Only output the cleaned data.
"""

# --- Streamlit App UI ---
st.title("🧠 Intelligent Exam Paper Formatter")
st.markdown("This app uses an advanced AI model to understand and format your PDF exam papers perfectly, including all options and a final answer key.")

api_key = st.text_input(
    "Enter your Google Gemini API Key:",
    type="password",
    help="An AI model is required for this high-quality formatting. Get your key from Google AI Studio."
)

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if st.button("✨ Process My Paper", disabled=(not uploaded_file or not api_key)):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')

        with st.spinner("Step 1/3: Extracting text and images from PDF..."):
            content_parts = extract_content_from_pdf(uploaded_file.getvalue())

        with st.spinner("Step 2/3: AI is analyzing and formatting the document... (This can take a minute)"):
            # Combine the system prompt with the extracted content
            full_prompt = [SYSTEM_PROMPT] + content_parts
            response = model.generate_content(full_prompt)

        with st.spinner("Step 3/3: Preparing the final output..."):
            formatted_text = response.text
            st.balloons()

        st.divider()
        st.subheader("🎉 Formatted Exam Paper")

        # Display the formatted text in the app
        st.markdown(formatted_text, unsafe_allow_html=True)

        # Provide a download button for the clean text
        st.divider()
        st.download_button(
            label="⬇️ Download as Markdown File",
            data=formatted_text,
            file_name=f"{uploaded_file.name.replace('.pdf', '')}_formatted.md",
            mime="text/markdown"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error("Please ensure you have a valid Gemini API key and that the PDF is not corrupted.")
else:
    st.info("Please provide a Gemini API Key and upload a PDF to proceed.")
