import fitz  # PyMuPDF
from PIL import Image
import io

def process_pdf(uploaded_file):
    """
    Extracts text and images from an uploaded PDF file.

    Args:
        uploaded_file: A file-like object from Streamlit's file_uploader.

    Returns:
        A list of content parts (alternating text and Image objects) for Gemini.
    """
    # Read the file content from the uploaded file object
    file_bytes = uploaded_file.read()
    
    # Open the PDF from bytes
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    
    content_parts = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        
        # Extract text
        content_parts.append(page.get_text())
        
        # Extract images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Convert to a PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            content_parts.append(image)
            
    return content_parts
