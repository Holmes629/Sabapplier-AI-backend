import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image
import io

def get_ocr_data(uploaded_file):
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    text_output = ""

    def image_to_text(img):
        return pytesseract.image_to_string(img, lang='eng')

    if uploaded_file.name.lower().endswith(".pdf"):
        try:
            # Convert PDF to a list of PIL Image objects
            images = convert_from_bytes(file_bytes, dpi=200)
            for img in images:
                text_output += image_to_text(img) + " "
        except Exception as e:
            print(f"Error processing PDF: {e}")
            text_output = ""
    else:
        # Handle image files
        try:
            img = Image.open(io.BytesIO(file_bytes))
            text_output = image_to_text(img)
        except Exception as e:
            print(f"Error processing image: {e}")
            text_output = ""

    uploaded_file.seek(0)  # Reset pointer for Django to save the file
    return text_output.strip()
