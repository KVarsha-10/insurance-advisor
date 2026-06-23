"""
OCR Pipeline using Tesseract + OpenCV preprocessing.
Used as fallback for clean, printed scanned documents.
For noisy/handwritten docs, vision.py (Ollama LLaVA) is used instead.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import os

# Path to Tesseract on Windows
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def preprocess_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return cleaned


def extract_text_from_image(image_path: str) -> str:
    try:
        processed = preprocess_image(image_path)
        pil_image = Image.fromarray(processed)
        text = pytesseract.image_to_string(pil_image, lang="eng")
        return text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"


def assess_image_quality(image_path: str) -> str:
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return "poor"
    height, width = img.shape
    if height < 300 or width < 300:
        return "poor"
    std_dev = np.std(img)
    if std_dev < 30:
        return "poor"
    return "good"