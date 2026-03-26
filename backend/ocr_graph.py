import cv2
import numpy as np
try:
    import easyocr
    reader = easyocr.Reader(['en'])  # Initialize once for performance
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


def preprocess_image(img):
    """Preprocess image for better OCR results."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply slight blur to reduce noise
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(blur)
    return enhanced


def extract_text_from_image(img):
    """Use EasyOCR to extract text, including equations and graph instructions."""
    if not EASYOCR_AVAILABLE:
        return "EasyOCR not available. Install with: pip install easyocr"

    try:
        # Preprocess the image
        processed = preprocess_image(img)

        # Run OCR
        results = reader.readtext(processed, detail=0)  # detail=0 returns just text

        # Join all detected text
        text = ' '.join(results).strip()

        return text if text else "No text detected in image"

    except Exception as e:
        return f"OCR error: {str(e)}"


def detect_line_equation(img):
    """Detect a dominant line using Hough and estimate a linear equation in image coords."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=80, minLineLength=60, maxLineGap=10)

    if lines is None or len(lines) == 0:
        return None

    slopes = []
    intercepts = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 == x1:
            continue
        m = (y2 - y1) / float(x2 - x1)
        c = y1 - m * x1
        slopes.append(m)
        intercepts.append(c)

    if not slopes:
        return None

    # Use median to resist outliers
    m_med = float(np.median(slopes))
    c_med = float(np.median(intercepts))

    # Convert image coord slope to Cartesian (y up) by sign
    m_cartesian = -m_med

    return (m_cartesian, c_med)


def extract_numeric_points_from_image(img):
    """Optional: parse explicit (x,y) point labels from OCR text."""
    text = extract_text_from_image(img)
    point_pairs = []
    import re
    for match in re.finditer(r"\(([-+]?\d*\.?\d+),\s*([-+]?\d*\.?\d+)\)", text):
        x_val = float(match.group(1))
        y_val = float(match.group(2))
        point_pairs.append((x_val, y_val))

    return point_pairs
