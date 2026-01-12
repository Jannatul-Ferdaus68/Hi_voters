import pdfplumber
import json
import re
import os

PDF_FOLDER = "pdfs"
OUTPUT_FILE = "voters.json"

voters = []

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_from_pdf(pdf_path):
    local_voters = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            record = {}

            for line in lines:
                line = clean(line)

                # Detect new voter entry (serial like 1., 2., 10.)
                if re.match(r"^\d+\.", line):
                    if record:
                        local_voters.append(record)
                    record = {
                        "source_pdf": os.path.basename(pdf_path)
                    }

                # Name
                if "নাম:" in line:
                    record["name"] = clean(line.split("নাম:")[-1])

                # Voter ID
                if "ভোটার নং:" in line:
                    record["voter_id"] = clean(line.split("ভোটার নং:")[-1])

                # Father
                if "পিতা:" in line:
                    record["father"] = clean(line.split("পিতা:")[-1])

                # Mother
                if "মাতা:" in line:
                    record["mother"] = clean(line.split("মাতা:")[-1])

                # Occupation (পেশা)
                if "পেশা:" in line:
                    record["occupation"] = clean(line.split("পেশা:")[-1])

                # Date of Birth
                if "জন্ম তারিখ:" in line or "জĥ তািরখ:" in line:
                    dob = re.findall(r"\d{2}/\d{2}/\d{4}", line)
                    if dob:
                        record["date_of_birth"] = dob[0]

                # Address (multi-line safe)
                if "ঠিকানা:" in line:
                    record["address"] = clean(line.split("ঠিকানা:")[-1])
                elif "address" in record and not any(
                    key in line for key in [
                        "নাম:", "ভোটার নং:", "পিতা:", "মাতা:",
                        "পেশা:", "জন্ম", "ঠিকানা:"
                    ]
                ):
                    record["address"] += " " + line

            if record:
                local_voters.append(record)

    return local_voters


# 🔁 Process all PDFs
for file in os.listdir(PDF_FOLDER):
    if file.lower().endswith(".pdf"):
        pdf_path = os.path.join(PDF_FOLDER, file)
        print(f"📄 Processing: {file}")
        voters.extend(extract_from_pdf(pdf_path))


# 💾 Save JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(voters, f, ensure_ascii=False, indent=2)

print(f"\ DONE: Extracted {len(voters)} voter records")
