import fitz  # PyMuPDF
from PIL import Image
import io
import re

def parse_pdf_rules(pdf_file_bytes):
    """
    Parses a PDF using rule-based logic to extract structured questions.

    Args:
        pdf_file_bytes: The bytes of the PDF file.

    Returns:
        A list of dictionaries, where each dictionary represents a structured question.
    """
    doc = fitz.open(stream=pdf_file_bytes, filetype="pdf")
    questions = []
    current_question = None
    current_section = "General"

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Get blocks of text with coordinate information
        blocks = page.get_text("dict")["blocks"]
        
        # Also get images on the page
        images = page.get_images(full=True)
        image_y_coords = {int(img[2]): img for img in images} # Map y-coord to image

        for b in blocks:
            # Skip blocks without text lines
            if 'lines' not in b:
                continue

            block_text = ""
            for l in b['lines']:
                for s in l['spans']:
                    block_text += s['text']
            
            block_text = block_text.strip()
            y0 = b['bbox'][1] # Top y-coordinate of the block

            # Check for images just above this text block
            if current_question:
                for img_y in sorted(image_y_coords.keys()):
                    # If image is between the last question and this block
                    if (current_question.get('last_y', 0) < img_y < y0):
                        img_info = image_y_coords[img_y]
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image = Image.open(io.BytesIO(image_bytes))
                        current_question["images"].append(image)
                        current_question['last_y'] = img_y # Update last content position
            
            # Rule 1: Detect Section
            section_match = re.match(r"Section:?\s*(.*)", block_text, re.IGNORECASE)
            if section_match:
                if current_question:
                    questions.append(current_question)
                    current_question = None
                current_section = section_match.group(1).strip()
                continue

            # Rule 2: Detect Question Start
            question_match = re.match(r"Q\.\s*(\d+)", block_text)
            if question_match:
                if current_question:
                    questions.append(current_question)
                
                q_num = question_match.group(1)
                q_text = re.sub(r"Q\.\s*\d+\s*", "", block_text, 1)
                current_question = {
                    "number": q_num,
                    "text": q_text.strip(),
                    "options": {},
                    "correct": None,
                    "images": [],
                    "section": current_section,
                    "last_y": y0 # Track the vertical position
                }
                continue

            # Rule 3: Detect Options
            # Matches patterns like "A.", "B. ", "☑ C.", "XA."
            option_match = re.match(r"(X|☑)?\s*([A-D])\.", block_text, re.IGNORECASE)
            if option_match and current_question:
                is_correct = option_match.group(1) == "☑"
                option_letter = option_match.group(2).upper()
                option_text = re.sub(r"(X|☑)?\s*[A-D]\.", "", block_text, 1).strip()
                
                current_question["options"][option_letter] = option_text
                if is_correct:
                    current_question["correct"] = option_letter
                current_question['last_y'] = y0
                continue
            
            # Rule 4: Append to existing question text if no other rule matches
            if current_question and block_text:
                current_question["text"] += " " + block_text
                current_question['last_y'] = y0

    # Add the last question if it exists
    if current_question:
        questions.append(current_question)

    return questions
