import fitz  # PyMuPDF
from PIL import Image
import io
import re
import imagehash

# These are the perceptual hashes for the "Google Play" and "testbook.com" logos
# found in your sample PDF. This allows us to visually identify and remove them.
# In your own projects, you can generate hashes for any image you want to filter.
UNWANTED_IMAGE_HASHES = {
    imagehash.hex_to_hash('ffc3c3c3c3c3ffff'), # testbook.com logo hash
    imagehash.hex_to_hash('8f8181a1a5e5e4f4'), # GET IT ON Google Play banner hash
}
HASH_THRESHOLD = 5 # How similar images can be to be considered a match (lower is stricter)


def is_unwanted_image(img: Image.Image) -> bool:
    """Checks if an image is one of the known banners by comparing its hash."""
    try:
        img_hash = imagehash.phash(img)
        for unwanted_hash in UNWANTED_IMAGE_HASHES:
            if (img_hash - unwanted_hash) < HASH_THRESHOLD:
                return True
    except Exception:
        # Some very small or simple images might fail to hash
        return False
    return False


def parse_pdf_rules(pdf_file_bytes):
    """
    Parses a PDF using rule-based logic to extract structured questions,
    while filtering unwanted text and images.
    """
    doc = fitz.open(stream=pdf_file_bytes, filetype="pdf")
    questions = []
    current_question = None
    current_section = "General"

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Get text blocks with coordinate information to preserve reading order
        blocks = sorted(page.get_text("blocks"), key=lambda b: b[1])

        # Get images on the page and filter out unwanted ones
        page_images = []
        for img_info in page.get_images(full=True):
            try:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                pil_image = Image.open(io.BytesIO(image_bytes))

                if not is_unwanted_image(pil_image):
                    page_images.append({'y': img_info[2], 'img': pil_image})
            except Exception:
                continue # Skip if image extraction fails
        
        # Sort images by vertical position
        page_images.sort(key=lambda item: item['y'])
        
        last_y = 0
        for b in blocks:
            y0 = b[1]
            block_text = b[4].strip()

            # Rule 1: Filter out metadata text
            if re.search(r"Question ID|Status\s*:\s*Answered|Chosen Option", block_text, re.IGNORECASE):
                continue

            # Rule 2: Associate images that appear before this text block
            if current_question:
                images_for_this_q = [img['img'] for img in page_images if last_y < img['y'] < y0]
                if images_for_this_q:
                    current_question["images"].extend(images_for_this_q)
            
            # Rule 3: Detect Section
            section_match = re.match(r"Section:?\s*(.*)", block_text, re.IGNORECASE)
            if section_match:
                if current_question:
                    questions.append(current_question)
                    current_question = None
                current_section = section_match.group(1).strip()
                continue

            # Rule 4: Detect Question Start
            question_match = re.match(r"Q\.\s*(\d+)", block_text)
            if question_match:
                if current_question:
                    questions.append(current_question)
                
                q_num = question_match.group(1)
                q_text = re.sub(r"Q\.\s*\d+\s*", "", block_text, 1).strip()
                current_question = {
                    "number": q_num, "text": q_text, "options": {}, "correct": None,
                    "images": [], "section": current_section
                }
                continue

            # Rule 5: Detect Options
            option_match = re.match(r"(X|☑)?\s*([A-D])\.", block_text, re.IGNORECASE)
            if option_match and current_question:
                is_correct = option_match.group(1) == "☑"
                option_letter = option_match.group(2).upper()
                option_text = re.sub(r"(X|☑)?\s*[A-D]\.", "", block_text, 1).strip()
                
                current_question["options"][option_letter] = option_text
                if is_correct:
                    current_question["correct"] = option_letter
                continue
            
            # Rule 6: Append text to the current question
            if current_question and block_text:
                current_question["text"] += " " + block_text
            
            last_y = y0 # Update last vertical position

    if current_question:
        questions.append(current_question)

    return questions
