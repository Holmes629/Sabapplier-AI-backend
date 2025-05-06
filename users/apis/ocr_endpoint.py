# Install requirements:
# pip install easyocr pdf2image opencv-python

import easyocr
from PIL import Image
import numpy as np
import cv2
from pdf2image import convert_from_bytes

# Initialize EasyOCR reader (load once globally)
reader = easyocr.Reader(['en'])  # You can add other languages like ['en', 'hi']

def get_ocr_data(uploaded_file):
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    text_output = ""

    if uploaded_file.name.lower().endswith(".pdf"):
        # 🧾 Handle PDF: Convert each page to image
        images = convert_from_bytes(file_bytes, dpi=300)
        for image in images:
            # Convert PIL image to numpy array
            img_np = np.array(image)
            results = reader.readtext(img_np, detail=0)
            text_output += " ".join(results) + " "
    else:
        # 🖼️ Handle image
        img_array = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("❌ Failed to decode image. Ensure it's a supported format.")

        results = reader.readtext(img, detail=0)
        text_output = " ".join(results)

    uploaded_file.seek(0)  # 🔁 Reset file pointer so Django can save it
    return text_output.strip()
