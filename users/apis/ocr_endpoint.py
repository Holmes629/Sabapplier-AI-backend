# Install requirements:
# pip install paddleocr paddlepaddle pillow

import numpy as np
import cv2
import fitz  # PyMuPDF
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,
    det_model_dir='./models/det/en_PP-OCRv3_det_infer',
    rec_model_dir='./models/rec/en_PP-OCRv4_rec_infer',
    lang='en'
)

def get_ocr_data(uploaded_file):
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()

    if uploaded_file.name.lower().endswith(".pdf"):
        # 🧾 Handle PDF: Convert each page to image
        text_output = ""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.tobytes(), dtype=np.uint8)
            img = cv2.imdecode(img, cv2.IMREAD_COLOR)
            if img is not None:
                result = ocr.ocr(img, cls=True)
                for line in result[0]:
                    text_output += line[1][0] + " "
    else:
        # 🖼️ Handle image
        img = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("❌ Failed to decode image. Ensure it's a supported format.")

        result = ocr.ocr(img, cls=True)
        text_output =  " ".join([line[1][0] for line in result[0]])
        
    uploaded_file.seek(0)  # 🔁 Reset file pointer so Django can save it
    return text_output


# def get_ocr_data(uploaded_file):
#     uploaded_file.seek(0)
    
    
#     ocr = PaddleOCR(use_angle_cls=True, lang='en')
#     print('1. starting the process....')
#     # For image OCR
#     # image_path = 'D:\\MYWORLD\\mywo\\my_working_projects_related\\Sabapplierai\\test_images\\image1.jpeg'
#     result = ocr.ocr(image_path, cls=True)

#     print('2. Finished recognizing.....')
#     doc_text = ""
#     for line in result:
#         for word_info in line:
#             text = word_info[1][0]
#             # confidence = word_info[1][1]
#             doc_text += text + " "
#     print("Recognized text:", doc_text)
#     print('3. terminating .....')
#     return doc_text