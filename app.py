import streamlit as st
from final_parser import parse_final
import collections

# --- Page Configuration ---
st.set_page_config(page_title="Final PDF Exam Processor", page_icon="✅", layout="wide")

# --- App UI ---
st.title("✅ Final PDF Exam Processor")
st.markdown("This version extracts **only the questions** and provides a consolidated answer key at the end, filtering out all other noise.")

# --- Helper Function to Build Markdown for Download ---
def format_for_download(structured_data):
    output_lines = []
    sections = collections.defaultdict(list)
    for q in structured_data:
        sections[q['section']].append(q)

    # Part 1: Questions
    for section_name, questions_in_section in sections.items():
        if not questions_in_section: continue
        output_lines.append(f"## Section: {section_name}\n")
        sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
        for q in sorted_questions:
            clean_text = ' '.join(q['text'].split())
            output_lines.append(f"**Q.{q['number']}:** {clean_text}\n")
        output_lines.append("---\n")
    
    # Part 2: Answer Key
    output_lines.append("## 🔑 Answer Key\n")
    for section_name, questions_in_section in sections.items():
        if not questions_in_section: continue
        output_lines.append(f"**{section_name}**")
        answer_line = []
        sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
        for q in sorted_questions:
            answer = q['answer'] if q['answer'] else 'N/A'
            answer_line.append(f"**{q['number']}**: {answer}")
        output_lines.append(" | ".join(answer_line) + "\n")
        
    return "\n".join(output_lines)

# --- Main App Logic ---
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file:
    if st.button("🚀 Process My Exam Paper"):
        try:
            file_bytes = uploaded_file.getvalue()
            with st.spinner("Performing high-precision parsing... Please wait."):
                structured_data = parse_final(file_bytes)
            
            if not structured_data:
                st.warning("Could not extract any questions. The PDF might be image-based or in an unsupported format.")
            else:
                st.success(f"Processing complete! Found {len(structured_data)} questions.")
                
                # Generate final string for display and download
                final_output_string = format_for_download(structured_data)

                # Add Download Button First
                st.download_button(
                    label="⬇️ Download Processed File",
                    data=final_output_string,
                    file_name=f"{uploaded_file.name.replace('.pdf', '')}_processed.md",
                    mime="text/markdown"
                )
                st.divider()

                # Display results on the page
                st.markdown(final_output_string)

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            st.error("This parser is highly tuned. If it fails, the PDF structure might be significantly different from the sample provided.")
else:
    st.info("Please upload your PDF file to begin.")
