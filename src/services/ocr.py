import pytesseract
from PIL import Image

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        print("OCR error:", e)
        return ""