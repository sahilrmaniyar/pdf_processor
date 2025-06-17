import streamlit as st
from pdf_processor import process_pdf
import google.generativeai as genai
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Exam Paper Processor",
    page_icon="🤖",
    layout="wide"
)

# --- Gemini API Configuration ---
# For local development, use os.getenv. For Streamlit Community Cloud, use st.secrets
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets["GOOGLE_API_KEY"]
# genai.configure(api_key=GOOGLE_API_KEY)

# --- Gemini Prompt ---
SYSTEM_PROMPT = """
You are an expert data extraction assistant. Your task is to analyze the provided content from a PDF, which includes text and images, and format it into a clean, readable markdown file.

Follow these instructions precisely:
1.  Structure the output with clear section headings (e.g., "General Knowledge").
2.  For each question, identify and extract the question number, the full question text, and all multiple-choice options.
3.  **Crucially, for any images of mathematical equations, diagrams, or circuits, convert them into appropriate LaTeX code.** Enclose inline LaTeX with `$` and block-level LaTeX with `$$`.
4.  Identify the correct answer. The correct answer is usually marked with a "☑" symbol or is the only non-crossed-out option.
5.  After listing all questions, create a final consolidated answer key. This section must start with the exact line "### Answers" and be immediately preceded by "<!-- START_ANSWERS_HERE -->" and immediately followed by "<!-- END_ANSWERS_HERE -->". For example:
<!-- START_ANSWERS_HERE -->
### Answers
Section 1
1. A
2. B
Section 2
1. C
<!-- END_ANSWERS_HERE -->
Group the answers by section.
6.  The final output must be pure markdown, ready to be displayed. Do not include any of your own commentary. Do not output the word "markdown".
"""

# --- App UI ---
st.title("📄 AI Exam Paper Processor")
st.markdown("Upload your PDF exam paper, and the AI will extract, format, and structure it, converting all math equations into LaTeX.")

# Get API Key from user
api_key = st.text_input("Enter your Google Gemini API Key:", type="password", help="Get your key from Google AI Studio.")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if st.button("✨ Process Paper", disabled=(not uploaded_file or not api_key)):
    if uploaded_file and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')

            with st.spinner("Step 1/3: Reading and processing the PDF..."):
                content_parts = process_pdf(uploaded_file)
                st.success("PDF processed successfully! Found text and image content.")

            with st.spinner("Step 2/3: Sending content to Gemini for analysis... (This can take a minute)"):
                # The model needs the prompt and the content parts
                full_prompt = [SYSTEM_PROMPT] + content_parts
                response = model.generate_content(full_prompt)

            with st.spinner("Step 3/3: Formatting the final output..."):
                formatted_text = response.text
                st.balloons()

            # --- Extract Answer Key ---
            start_marker = "<!-- START_ANSWERS_HERE -->"
            end_marker = "<!-- END_ANSWERS_HERE -->"
            answer_section_text = ""
            main_content_text = formatted_text

            start_pos = formatted_text.find(start_marker)
            end_pos = formatted_text.find(end_marker)

            if start_pos != -1 and end_pos != -1 and start_pos < end_pos:
                answer_section_text = formatted_text[start_pos + len(start_marker):end_pos].strip()
                main_content_text = formatted_text[:start_pos] + formatted_text[end_pos + len(end_marker):]

                # Remove "### Answers" heading if present
                if answer_section_text.startswith("### Answers"):
                    answer_section_text = answer_section_text[len("### Answers"):].lstrip()
            else:
                st.warning("Answer key markers not found in the processed output. The separate answer list cannot be displayed.")

            st.divider()
            st.subheader("🎉 Processed Output")
            with st.expander("🔍 View Full Processed Paper", expanded=True):
                st.markdown(main_content_text) # Display main content here

            # Display answer section if extracted
            if answer_section_text:
                st.subheader("🔑 Consolidated Answer Key")
                with st.expander("View Answer Key", expanded=False):
                    st.markdown(answer_section_text)

            # Add a download button for the formatted text (original full text)
            st.download_button(
                label="Download as Markdown",
                data=formatted_text, # This should be the original full text
                file_name=f"{uploaded_file.name.replace('.pdf', '')}_formatted.md",
                mime="text/markdown"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error("Please check your API key and ensure the PDF is not corrupted.")
else:
    st.info("Please upload a PDF and enter your API key to proceed.")
