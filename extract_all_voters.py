import os
import json
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import cv2
import numpy as np


# CONFIGURATION
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER = os.path.join(BASE_DIR, "pdfs")
OUTPUT_FILE = os.path.join(BASE_DIR, "voters.json")


# HELPERS
def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def preprocess_image(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(gray)

def capture_field(line, key):
    if key in line:
        return clean(line.split(key, 1)[1])
    return None

def is_valid_name(name):
    return name and len(name) > 2 and "cid:" not in name


# TEXT → RECORD EXTRACTION
def extract_from_text(text, source_pdf):
    records = []
    lines = text.split("\n")

    record = {}
    last_key = None

    for line in lines:
        line = clean(line)
        if not line:
            continue

        # Bengali + English serial detection
        if re.match(r"^(\d+|[০-৯]+)[\.\)]", line):
            if record and is_valid_name(record.get("name")):
                records.append(record)
            record = {"source_pdf": source_pdf}
            last_key = None
            continue

        # Name
        value = capture_field(line, "নাম:")
        if value:
            record["name"] = value
            last_key = "name"
            continue

        # Father
        value = capture_field(line, "পিতা:")
        if value:
            record["father"] = value
            last_key = "father"
            continue

        # Mother
        value = capture_field(line, "মাতা:")
        if value:
            record["mother"] = value
            last_key = "mother"
            continue

        # Occupation
        value = capture_field(line, "পেশা:")
        if value:
            record["occupation"] = value
            last_key = None
            continue

        # Address (multi-line)
        value = capture_field(line, "ঠিকানা:")
        if value:
            record["address"] = value
            last_key = "address"
            continue

        # Continue previous multi-line field
        if last_key in ["name", "father", "mother", "address"]:
            record[last_key] += " " + line

        # DOB
        dob = re.findall(r"\d{2}/\d{2}/\d{4}", line)
        if dob:
            record["date_of_birth"] = dob[0]

        # OCR quality flag
        if "cid:" in line:
            record["_ocr_quality"] = "low"
        else:
            record.setdefault("_ocr_quality", "ok")

    if record and is_valid_name(record.get("name")):
        records.append(record)

    return records


# MAIN OCR PIPELINE
voters = []

for file in os.listdir(PDF_FOLDER):
    if not file.lower().endswith(".pdf"):
        continue

    pdf_path = os.path.join(PDF_FOLDER, file)
    print(f"📄 OCR Processing: {file}")

    images = convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path=POPPLER_PATH
    )

    full_text = ""
    for img in images:
        img = preprocess_image(img)
        text = pytesseract.image_to_string(
            img,
            lang="ben",
            config="--psm 6"
        )
        full_text += "\n" + text

    voters.extend(extract_from_text(full_text, file))


# SAVE OUTPUT
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(voters, f, ensure_ascii=False, indent=2)

print(f"DONE: Extracted {len(voters)} voter records")
