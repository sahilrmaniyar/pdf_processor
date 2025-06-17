import streamlit as st
from rule_based_parser import parse_pdf_rules
import collections

# --- Page Configuration ---
st.set_page_config(
    page_title="PDF Exam Paper Processor",
    page_icon="📄",
    layout="wide"
)

# --- App UI ---
st.title("📄 Self-Contained PDF Exam Processor")
st.markdown("Upload your PDF exam paper. This tool will process it locally to extract questions, options, and images, while filtering out headers, footers, and metadata.")

# --- Helper Function to Build Markdown ---
def format_data_as_markdown(structured_data):
    """Converts the structured data from the parser into a single markdown string."""
    output_lines = []
    
    # Group questions by section
    sections = collections.defaultdict(list)
    for q in structured_data:
        sections[q['section']].append(q)

    for section_name, questions_in_section in sections.items():
        output_lines.append(f"## {section_name}\n")
        # Sort questions by number (as integer)
        sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
        
        for q in sorted_questions:
            output_lines.append(f"**Q.{q['number']}:** {q['text']}\n")
            # Note: Images won't appear in the downloaded markdown file, only in the UI.
            # A more advanced solution could save images and link them.
            
            for letter, text in sorted(q['options'].items()):
                output_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;**{letter}.** {text}")
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
            
            with st.spinner("Processing PDF with local parser... This is complex and may take a moment."):
                structured_data = parse_pdf_rules(file_bytes)
            
            if not structured_data:
                st.warning("Could not extract any questions. The PDF format might be unsupported.")
            else:
                st.success(f"Processing complete! Found {len(structured_data)} questions.")
                st.divider()

                # Format the data for both display and download
                final_output_string = format_data_as_markdown(structured_data)

                # --- Display Formatted Output ---
                st.subheader("🎉 Processed Output")
                
                # We need to display images separately as they are not in the markdown string
                st.info("Displaying questions and options below. Images like equations or diagrams are shown with their question.")
                
                sections = collections.defaultdict(list)
                for q in structured_data:
                    sections[q['section']].append(q)

                for section_name, questions_in_section in sections.items():
                    st.header(section_name)
                    sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
                    for q in sorted_questions:
                        st.markdown(f"**Q.{q['number']}:** {q['text']}")
                        if q['images']:
                            for img in q['images']:
                                st.image(img, use_column_width=True)
                        for letter, text in sorted(q['options'].items()):
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{letter}.** {text}")
                        st.markdown("---")

                # Display the answer key from the formatted string
                answer_key_part = final_output_string.split("## 🔑 Answer Key")[1]
                st.header("🔑 Answer Key")
                st.markdown(answer_key_part)

                # --- Add Download Button ---
                st.divider()
                st.download_button(
                    label="⬇️ Download as Markdown File",
                    data=final_output_string,
                    file_name=f"{uploaded_file.name.replace('.pdf', '')}_formatted.md",
                    mime="text/markdown"
                )

        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
            st.error("Please ensure the PDF is a valid, text-based document and not corrupted.")
else:
    st.info("Please upload a PDF to begin.")
