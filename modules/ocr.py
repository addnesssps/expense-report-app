import os
from PIL import Image

# Tesseract OCR (optional - graceful fallback if not installed)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# PDF text extraction
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


def extract_text_from_image(image_path: str) -> str:
    if not TESSERACT_AVAILABLE:
        return "[Tesseract OCRがインストールされていません。brew install tesseract tesseract-lang で導入してください]"
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="jpn+eng")
        return text.strip()
    except Exception as e:
        return f"[OCRエラー: {e}]"


def extract_text_from_pdf(pdf_path: str) -> str:
    if not PDFPLUMBER_AVAILABLE:
        return "[pdfplumberがインストールされていません]"
    try:
        texts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texts.append(page_text)
        return "\n".join(texts).strip()
    except Exception as e:
        return f"[PDF読み取りエラー: {e}]"


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
        return extract_text_from_image(file_path)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        return f"[未対応のファイル形式: {ext}]"


def save_uploaded_file(uploaded_file, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path
