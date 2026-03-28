import cv2

try:
    import easyocr

    reader = easyocr.Reader(["en"])
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(blur)


def extract_text_from_image(img):
    if not EASYOCR_AVAILABLE:
        return "EasyOCR not available. Install with: pip install easyocr"

    try:
        processed = preprocess_image(img)
        results = reader.readtext(processed, detail=0)
        text = " ".join(results).strip()
        return text if text else "No text detected in image"
    except Exception as e:
        return f"OCR error: {str(e)}"
