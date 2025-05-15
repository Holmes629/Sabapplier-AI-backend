import pytesseract
import cv2
import numpy as np
import fitz  # PyMuPDF

# 🪟 Only for Windows: specify path to tesseract.exe
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\tesseract-ocr-w64-setup-5.5.0.20241111.exe'

def get_ocr_data(uploaded_file):
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    text_output = ""

    def image_to_text(img):
        return pytesseract.image_to_string(img, lang='eng')

    if uploaded_file.name.lower().endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.tobytes(), dtype=np.uint8)
            img = cv2.imdecode(img, cv2.IMREAD_COLOR)
            if img is not None:
                text_output += image_to_text(img) + " "
    else:
        # 🖼️ Handle image
        img = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("❌ Failed to decode image.")
        text_output = image_to_text(img)

    uploaded_file.seek(0)  # Reset pointer for Django to save the file
    return text_output.strip()
