"""
Universal Insurance Document Extractor.
Handles: PDF (structured/scanned), JPG/PNG, CSV, Excel, JSON.
"""

import os
import re
import json
import pandas as pd
import pdfplumber
import requests

from utils.file_detector import detect_format
from utils.ocr import extract_text_from_image, assess_image_quality
from utils.vision import extract_structured_fields_from_image

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5vl:7b"


def extract_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return f"PDF extraction error: {str(e)}"
    return text.strip()


def is_pdf_scanned(file_path: str) -> bool:
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    return False
        return True
    except:
        return True


def pdf_to_images(file_path: str) -> list:
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, dpi=300)
        image_paths = []
        for i, img in enumerate(images):
            img_path = f"C:/temp/pdf_page_{i}.png"
            os.makedirs("C:/temp", exist_ok=True)
            img.save(img_path, "PNG")
            image_paths.append(img_path)
        return image_paths
    except Exception as e:
        return []


def extract_from_image(file_path: str) -> str:
    quality = assess_image_quality(file_path)
    if quality == "good":
        return extract_text_from_image(file_path)
    else:
        result = extract_structured_fields_from_image(file_path)
        if "error" not in result:
            return json.dumps(result, indent=2)
        return extract_text_from_image(file_path)


def extract_from_csv(file_path: str, person_name: str = None) -> str:
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        if person_name:
            name_cols = [c for c in df.columns if "name" in c]
            for col in name_cols:
                mask = df[col].astype(str).str.lower().str.contains(
                    person_name.lower(), na=False)
                if mask.any():
                    return df[mask].to_string(index=False)
        return df.to_string(index=False)
    except Exception as e:
        return f"CSV extraction error: {str(e)}"


def extract_from_excel(file_path: str, person_name: str = None) -> str:
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        if person_name:
            name_cols = [c for c in df.columns if "name" in c]
            for col in name_cols:
                mask = df[col].astype(str).str.lower().str.contains(
                    person_name.lower(), na=False)
                if mask.any():
                    return df[mask].to_string(index=False)
        return df.to_string(index=False)
    except Exception as e:
        return f"Excel extraction error: {str(e)}"


def extract_from_json(file_path: str) -> str:
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"JSON extraction error: {str(e)}"


def extract_document(file_path: str, person_name: str = None) -> dict:
    fmt = detect_format(file_path)

    if fmt == "pdf":
        if is_pdf_scanned(file_path):
            images = pdf_to_images(file_path)
            if images:
                all_text = ""
                for img_path in images:
                    all_text += extract_from_image(img_path) + "\n\n"
                raw_text = all_text.strip()
            else:
                raw_text = "Could not convert scanned PDF to images."
        else:
            raw_text = extract_from_pdf(file_path)
    elif fmt == "image":
        raw_text = extract_from_image(file_path)
    elif fmt == "csv":
        raw_text = extract_from_csv(file_path, person_name)
    elif fmt == "excel":
        raw_text = extract_from_excel(file_path, person_name)
    elif fmt == "json":
        raw_text = extract_from_json(file_path)
    else:
        raw_text = f"Unsupported file format: {file_path}"

    return {
        "raw_text": raw_text,
        "format": fmt,
        "file": os.path.basename(file_path)
    }


def parse_insurance_fields(raw_text: str, label: str = "plan") -> dict:

    def find(patterns, text):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Return first non-None group
                for g in match.groups():
                    if g:
                        return g.strip()
                return match.group(1).strip()
        return None

    fields = {
        "policyholder_name": find([
            r"Name of (?:the )?Insured[:\s]+([A-Za-z\s]+)",
            r"Policyholder[:\s]+([A-Za-z\s]+)",
            r"Insured Name[:\s]+([A-Za-z\s]+)",
            r"Name\s*:\s*([A-Za-z\s]+)",
            r"(?:Mr\.|Ms\.|Mrs\.)\s+([A-Za-z\s]+)"
        ], raw_text),

        "age": find([
            r"Age[:\s]+(\d+)\s*(?:Years|Yrs|Y)?",
            r"(\d+)\s*(?:Years|Yrs)\s*(?:old)?",
        ], raw_text),

        "gender": find([
            r"Gender[:\s]+(Male|Female|Other)",
            r"\b(Male|Female)\b"
        ], raw_text),

        "policy_number": find([
            r"Policy\s*(?:No|Number)[:\s#]+([A-Z0-9/\-]+)",
            r"Policy\s*ID[:\s]+([A-Z0-9/\-]+)",
            r"Certificate\s*No[:\s]+([A-Z0-9/\-]+)"
        ], raw_text),

        "insurer_name": find([
            r"(?:Insurance Company|Insurer|Company Name)[:\s]+([A-Za-z\s]+)",
            r"([A-Za-z\s]+(?:Insurance|General|Health)[A-Za-z\s]*)\n"
        ], raw_text),

        "plan_name": find([
            r"Plan\s*(?:Name)?[:\s]+([A-Za-z0-9\s\-]+)",
            r"Product\s*(?:Name)?[:\s]+([A-Za-z0-9\s\-]+)",
            r"Policy\s*(?:Name|Type)[:\s]+([A-Za-z0-9\s\-]+)"
        ], raw_text),

        "sum_insured": find([
            r"Sum\s*Insured[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)",
            r"Coverage\s*Amount[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)",
            r"Basic\s*Sum\s*Insured[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)"
        ], raw_text),

        "premium_amount": find([
            r"(?:Total\s*)?Premium[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)",
            r"Annual\s*Premium[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)",
            r"(?:Rs\.?|INR|₹)\s*([\d,]+)\s*(?:per year|p\.a\.|annually)"
        ], raw_text),

        "policy_start_date": find([
            r"(?:Policy\s*)?(?:Start|Commencement|From)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(?:Start|From)\s*:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})\s*to"
        ], raw_text),

        "policy_end_date": find([
            r"(?:Policy\s*)?(?:End|Expiry|To)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(?:End|To|Expiry)\s*:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"to\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})"
        ], raw_text),

        "nominee": find([
            r"Nominee\s*(?:Name)?[:\s]+([A-Za-z\s]+)",
            r"Nomination[:\s]+([A-Za-z\s]+)"
        ], raw_text),

        "contact_number": find([
            r"(?:Mobile|Phone|Contact)[:\s]+(\+?[\d\s\-]{10,})",
            r"(\+91[\s\-]?\d{10})"
        ], raw_text),

        "email": find([
            r"(?:Email|E-mail)[:\s]+([\w\.\+]+@[\w\.]+\.\w+)",
            r"([\w\.\+]+@[\w\.]+\.\w+)"
        ], raw_text),

        "room_rent_limit": find([
            r"Room\s*Rent[:\s]+([^\n]+)",
            r"Room\s*Rent\s*(?:Limit|Cap)[:\s]+([^\n]+)"
        ], raw_text),

        "pre_existing_waiting_period": find([
            r"Pre[\s\-]?existing[:\s]+([^\n]+)",
            r"PED\s*Waiting[:\s]+([^\n]+)"
        ], raw_text),

        "copayment": find([
            r"Co[\s\-]?pay(?:ment)?[:\s]+([^\n]+)",
        ], raw_text),

        "no_claim_bonus": find([
            r"No\s*Claim\s*Bonus[:\s]+([^\n]+)",
            r"NCB[:\s]+([^\n]+)"
        ], raw_text),
    }

    # Remove None values and clean whitespace
    return {k: v.strip() if isinstance(v, str) else v
            for k, v in fields.items() if v}