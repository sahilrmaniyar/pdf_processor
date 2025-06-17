import streamlit as st
from robust_parser import parse_pdf_robustly
import collections

# --- Page Configuration ---
st.set_page_config(
    page_title="PDF Exam Paper Processor",
    page_icon="📄",
    layout="wide"
)

# --- App UI ---
st.title("📄 Robust PDF Exam Processor")
st.markdown("Upload your PDF exam paper. This improved tool uses layout analysis to correctly filter metadata, banners, and incorrect answers.")

# --- Helper Function to Build Markdown for Download ---
def format_data_for_download(structured_data):
    """Converts the structured data from the parser into a single markdown string for download."""
    output_lines = []
    
    sections = collections.defaultdict(list)
    for q in structured_data:
        sections[q['section']].append(q)

    for section_name, questions_in_section in sections.items():
        output_lines.append(f"## {section_name}\n")
        sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
        
        for q in sorted_questions:
            # Clean up newlines in question text
            q_text = ' '.join(q['text'].split())
            output_lines.append(f"**Q.{q['number']}:** {q_text}\n")
            
            for letter, text in sorted(q['options'].items()):
                output_lines.append(f"- **{letter}.** {text}")
            output_lines.append("\n---\n")
    
    # --- Add Consolidated Answer Key ---
    output_lines.append("## 🔑 Answer Key\n")
    for section_name, questions_in_section in sections.items():
        output_lines.append(f"**{section_name}**")
        answer_line = []
        sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
        for q in sorted_questions:
            answer = q['correct'] if q['correct'] else 'N/A'
            answer_line.append(f"**{q['number']}**: {answer}")
        output_lines.append(" | ".join(answer_line) + "\n")
        
    return "\n".join(output_lines)

# --- Main App Logic ---
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file:
    if st.button("✨ Process Paper"):
        try:
            file_bytes = uploaded_file.getvalue()
            
            with st.spinner("Analyzing PDF layout and content... This might take a moment."):
                structured_data = parse_pdf_robustly(file_bytes)
            
            if not structured_data:
                st.warning("Could not extract any questions. The PDF format might be unsupported or empty.")
            else:
                st.success(f"Processing complete! Found {len(structured_data)} questions.")
                st.divider()

                # --- Prepare and add Download Button ---
                download_string = format_data_for_download(structured_data)
                st.download_button(
                    label="⬇️ Download as Markdown File",
                    data=download_string,
                    file_name=f"{uploaded_file.name.replace('.pdf', '')}_formatted.md",
                    mime="text/markdown"
                )
                st.divider()

                # --- Display Formatted Output on the Page ---
                st.subheader("🎉 Processed Output")
                
                sections = collections.defaultdict(list)
                for q in structured_data:
                    sections[q['section']].append(q)

                for section_name, questions_in_section in sections.items():
                    st.header(section_name)
                    sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
                    for q in sorted_questions:
                        # Clean up text for display
                        q_text = ' '.join(q['text'].split())
                        st.markdown(f"**Q.{q['number']}:** {q_text}")
                        if q['images']:
                            for img in q['images']:
                                st.image(img, use_column_width=True)
                        for letter, text in sorted(q['options'].items()):
                            # Use a green checkmark for the correct answer in the UI
                            if letter == q['correct']:
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✅&nbsp;&nbsp;**{letter}.** {text}")
                            else:
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**{letter}.** {text}")
                        st.markdown("---")

        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
            st.error("Please ensure the PDF is valid and not corrupted. This parser is tuned for the provided AAI exam paper format.")
else:
    st.info("Please upload a PDF to begin.")
