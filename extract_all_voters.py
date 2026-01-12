import os
import json
import re
from pdf2image import convert_from_path
import pytesseract

# -------------------------
# 1️⃣ Tesseract setup
# -------------------------
# Update this path if Tesseract is installed elsewhere
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -------------------------
# 2️⃣ Paths & folders
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER = os.path.join(BASE_DIR, "pdfs")  # Make sure your PDFs are in this folder
OUTPUT_FILE = os.path.join(BASE_DIR, "voters.json")

# -------------------------
# 3️⃣ Poppler path
# -------------------------
# Update this path to where you extracted Poppler
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin "

# -------------------------
# 4️⃣ Initialize
# -------------------------
voters = []

def clean(text):
    """Remove extra whitespace"""
    return re.sub(r"\s+", " ", text).strip()

def extract_from_text(text, source_pdf):
    """Extract voter records from OCR text"""
    records = []
    lines = text.split("\n")
    record = {}

    for line in lines:
        line = clean(line)

        # New voter block if line starts with a number
        if re.match(r"^\d+\.", line):
            if record:
                records.append(record)
            record = {"source_pdf": source_pdf}

        if "নাম:" in line:
            record["name"] = line.split("নাম:")[-1].strip()

        if "ভোটার নং:" in line:
            record["voter_id"] = line.split("ভোটার নং:")[-1].strip()

        if "পিতা:" in line:
            record["father"] = line.split("পিতা:")[-1].strip()

        if "মাতা:" in line:
            record["mother"] = line.split("মাতা:")[-1].strip()

        if "পেশা:" in line:
            record["occupation"] = line.split("পেশা:")[-1].strip()

        if "ঠিকানা:" in line:
            record["address"] = line.split("ঠিকানা:")[-1].strip()

        dob = re.findall(r"\d{2}/\d{2}/\d{4}", line)
        if dob:
            record["date_of_birth"] = dob[0]

    if record:
        records.append(record)

    return records

# -------------------------
# 5️⃣ OCR Processing loop
# -------------------------
for file in os.listdir(PDF_FOLDER):
    if file.lower().endswith(".pdf"):
        pdf_path = os.path.join(PDF_FOLDER, file)
        print(f"📄 OCR Processing: {file}")

        # Convert PDF pages to images using Poppler
        images = convert_from_path(
            pdf_path,
            dpi=300,
            poppler_path=POPPLER_PATH
        )

        full_text = ""
        for img in images:
            # OCR in Bangla
            text = pytesseract.image_to_string(img, lang="ben")
            full_text += "\n" + text

        # Extract voter records from OCR text
        voters.extend(extract_from_text(full_text, file))

# -------------------------
# 6️⃣ Save JSON
# -------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(voters, f, ensure_ascii=False, indent=2)

print(f"✅ DONE: Extracted {len(voters)} voter records into {OUTPUT_FILE}")
