import fitz  # PyMuPDF
from PIL import Image
import io
import re
import collections

def parse_pdf_robustly(pdf_file_bytes):
    """
    Parses a PDF using advanced layout analysis and contextual rules.
    This version is specifically tuned to handle the complexities of the provided exam paper.

    Args:
        pdf_file_bytes: The bytes of the PDF file.

    Returns:
        A list of dictionaries, where each represents a structured question.
    """
    doc = fitz.open(stream=pdf_file_bytes, filetype="pdf")
    all_questions = []
    
    MIN_IMAGE_WIDTH = 50  # Ignore very small images (likely icons/logos)
    MIN_IMAGE_HEIGHT = 50

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # 1. Get all content blocks (text and images) and sort them by vertical position
        content_on_page = []
        
        # Add text blocks with their coordinates and text
        for block in page.get_text("blocks"):
            # Filter out metadata lines immediately
            block_text = block[4]
            if not re.search(r"Question ID|Status\s*:\s*Answered|Chosen Option|testbook\.com|GET IT ON Google Play", block_text, re.IGNORECASE):
                content_on_page.append({'type': 'text', 'bbox': block[:4], 'text': block_text.strip()})

        # Add image blocks with their coordinates and data
        for img_info in page.get_images(full=True):
            try:
                # Filter out small or banner-like images based on size
                img_rect = fitz.Rect(page.get_image_bbox(img_info))
                if img_rect.width < MIN_IMAGE_WIDTH or img_rect.height < MIN_IMAGE_HEIGHT:
                    continue # Skip small images

                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                pil_image = Image.open(io.BytesIO(image_bytes))
                content_on_page.append({'type': 'image', 'bbox': img_rect, 'img': pil_image})
            except Exception:
                continue

        # Sort all content by vertical position, then horizontal
        content_on_page.sort(key=lambda item: (item['bbox'][1], item['bbox'][0]))
        
        # 2. Process the sorted content
        for item in content_on_page:
            if item['type'] == 'text':
                text = item['text']
                
                # Detect a new section
                section_match = re.match(r"Section:?\s*(.*)", text, re.IGNORECASE)
                if section_match:
                    current_section = section_match.group(1).strip()
                    continue

                # Detect a new question
                question_match = re.match(r"Q\.\s*(\d+)\s*(.*)", text, re.DOTALL)
                if question_match:
                    # If a question is already being built, save it
                    if all_questions and "is_building" in all_questions[-1]:
                         del all_questions[-1]["is_building"]

                    q_num = question_match.group(1)
                    q_text = question_match.group(2)
                    all_questions.append({
                        "number": q_num,
                        "text": q_text,
                        "options": collections.OrderedDict(),
                        "correct": None,
                        "images": [],
                        "section": locals().get('current_section', 'General'),
                        "is_building": True # Flag that this question is active
                    })
                
                # Detect options
                elif all_questions and "is_building" in all_questions[-1]:
                    option_match = re.match(r"(X|☑)?\s*([A-D])\.\s*(.*)", text, re.IGNORECASE | re.DOTALL)
                    if option_match:
                        correct_symbol = option_match.group(1)
                        option_letter = option_match.group(2).upper()
                        option_text = option_match.group(3).strip()

                        all_questions[-1]["options"][option_letter] = option_text
                        if correct_symbol == "☑":
                            all_questions[-1]["correct"] = option_letter
                    # Append any other text to the last question's text
                    else:
                        all_questions[-1]["text"] += "\n" + text

            elif item['type'] == 'image':
                # Associate image with the last question being built
                if all_questions and "is_building" in all_questions[-1]:
                    all_questions[-1]["images"].append(item['img'])

    # Final cleanup of the flag
    if all_questions and "is_building" in all_questions[-1]:
        del all_questions[-1]["is_building"]

    return all_questions
