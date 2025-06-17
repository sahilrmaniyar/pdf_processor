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
st.markdown("Upload your PDF exam paper. This tool will process it locally to extract questions, options, and images without using any external APIs.")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if st.button("✨ Process Paper", disabled=(not uploaded_file)):
    if uploaded_file:
        try:
            # Get bytes from uploaded file
            file_bytes = uploaded_file.getvalue()
            
            with st.spinner("Processing PDF with local parser... This might take a moment."):
                structured_data = parse_pdf_rules(file_bytes)
            
            st.success(f"Processing complete! Found {len(structured_data)} questions.")
            st.divider()

            # --- Display Formatted Output ---
            st.subheader("🎉 Processed Output")
            
            # Group questions by section
            sections = collections.defaultdict(list)
            for q in structured_data:
                sections[q['section']].append(q)

            for section_name, questions_in_section in sections.items():
                st.header(section_name)
                # Sort questions by number (as integer)
                sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
                
                for q in sorted_questions:
                    st.markdown(f"**Q.{q['number']}:** {q['text']}")
                    
                    # Display any associated images (e.g., equations, diagrams)
                    if q['images']:
                        for img in q['images']:
                            st.image(img, use_column_width=True)
                            
                    # Display options
                    for letter, text in sorted(q['options'].items()):
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{letter}.** {text}")
                    st.markdown("---")
            
            # --- Display Consolidated Answer Key ---
            st.divider()
            st.subheader("🔑 Answer Key")
            for section_name, questions_in_section in sections.items():
                st.markdown(f"**{section_name}**")
                answer_line = []
                # Sort questions by number for the answer key
                sorted_questions = sorted(questions_in_section, key=lambda x: int(x['number']))
                for q in sorted_questions:
                    answer = q['correct'] if q['correct'] else 'N/A'
                    answer_line.append(f"{q['number']}. {answer}")
                st.text(" | ".join(answer_line))


        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
            st.error("Please ensure the PDF is a valid, text-based document and not corrupted.")
else:
    st.info("Please upload a PDF to begin.")
