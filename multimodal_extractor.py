import fitz  # PyMuPDF
from PIL import Image
import io

def extract_content_from_pdf(pdf_file_bytes):
    """
    Extracts all text and image content from a PDF for multimodal analysis.
    Filters out very small images that are likely logos or icons.
    """
    doc = fitz.open(stream=pdf_file_bytes, filetype="pdf")
    content_parts = []
    
    MIN_IMAGE_AREA = 2500 # Ignore images smaller than 50x50 pixels

    for page in doc:
        # Add page's text first
        content_parts.append(page.get_text())
        
        # Add images from the page, filtering out small ones
        for img_info in page.get_images(full=True):
            try:
                img_rect = page.get_image_bbox(img_info)
                if img_rect.width * img_rect.height < MIN_IMAGE_AREA:
                    continue # Skip small, irrelevant images

                base_image = doc.extract_image(img_info[0])
                image_bytes = base_image["image"]
                pil_image = Image.open(io.BytesIO(image_bytes))
                content_parts.append(pil_image)
            except Exception:
                continue # Skip if image processing fails
    
    return content_parts
