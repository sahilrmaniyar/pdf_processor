import pdfplumber
import re
import io
from collections import defaultdict

def parse_final(pdf_file_bytes):
    """
    A robust, final parser using pdfplumber for high-precision text extraction.
    It's designed to handle complex layouts by analyzing word positions.
    """
    all_questions = []
    current_question = {}
    current_section = "General Knowledge"  # Default starting section

    with pdfplumber.open(io.BytesIO(pdf_file_bytes)) as pdf:
        for page in pdf.pages:
            # Extract words with their precise bounding boxes
            words = page.extract_words(x_tolerance=2, y_tolerance=2)

            # Group words into lines based on vertical position
            lines = defaultdict(list)
            for word in words:
                # Group words that are on the same vertical level (with a tolerance)
                lines[round(word['top'])].append(word)

            # Process the reconstructed lines
            for top_val in sorted(lines.keys()):
                line_words = sorted(lines[top_val], key=lambda w: w['x0'])
                line_text = " ".join([w['text'] for w in line_words])

                # --- Filtering and Rule-Based Logic ---

                # 1. Skip all known junk and metadata lines
                if re.search(r"Question ID|Status :|Chosen Option|testbook\.com|GET IT ON Google Play", line_text, re.IGNORECASE):
                    continue

                # 2. Detect Section
                section_match = re.search(r"Section\s+([a-zA-Z\s]+)", line_text, re.IGNORECASE)
                if section_match:
                    if current_question:  # Save the last question before switching sections
                        all_questions.append(current_question)
                        current_question = {}
                    current_section = section_match.group(1).strip()
                    continue

                # 3. Detect Question Start
                question_match = re.match(r"Q\.\s*(\d+)", line_text)
                if question_match:
                    if current_question:  # Save the previous question
                        all_questions.append(current_question)
                    
                    q_num = question_match.group(1)
                    q_text = re.sub(r"^Q\.\s*\d+\s*", "", line_text).strip()
                    current_question = {
                        "number": q_num,
                        "text": q_text,
                        "answer": None,
                        "section": current_section
                    }
                    continue

                # 4. Detect Options to find the answer
                option_match = re.match(r"(☑)\s*([A-D])\.", line_text, re.IGNORECASE)
                if option_match and current_question:
                    option_letter = option_match.group(2).upper()
                    current_question["answer"] = option_letter
                    continue
                
                # Ignore lines that are just incorrect options (starting with 'X')
                if re.match(r"X[A-D]\.", line_text):
                    continue

                # 5. Append text to the current question
                if current_question and "text" in current_question:
                    # Append if it's not a stray option letter or junk
                    if not re.match(r"^[A-D]\.", line_text):
                       current_question["text"] += " " + line_text

    # Add the very last question if it exists
    if current_question:
        all_questions.append(current_question)

    return all_questions
