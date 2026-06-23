"""
Vision LLM Pipeline using Ollama (LLaVA model).
Used for noisy scans, handwritten documents, or low-quality images.
"""

import base64
import requests
import json

OLLAMA_BASE_URL = "http://localhost:11434"
VISION_MODEL = "qwen2.5vl:7b"


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_structured_fields_from_image(image_path: str) -> dict:
    try:
        image_b64 = image_to_base64(image_path)
        prompt = """You are an expert insurance document analyzer.

Extract the following fields from this insurance document image.
Return ONLY a valid JSON object with these exact keys (use null if not found):

{
  "policyholder_name": "",
  "age": "",
  "gender": "",
  "policy_number": "",
  "insurer_name": "",
  "plan_name": "",
  "sum_insured": "",
  "premium_amount": "",
  "policy_start_date": "",
  "policy_end_date": "",
  "room_rent_limit": "",
  "pre_existing_disease_waiting_period": "",
  "specific_disease_waiting_period": "",
  "initial_waiting_period": "",
  "copayment": "",
  "no_claim_bonus": "",
  "pre_hospitalization_days": "",
  "post_hospitalization_days": "",
  "daycare_coverage": "",
  "ayush_coverage": "",
  "domiciliary_coverage": "",
  "exclusions": []
}

Return ONLY the JSON. No explanation, no markdown."""

        payload = {
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            raw = response.json().get("response", "").strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        return {"error": f"Vision API Error: {response.status_code}"}

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {str(e)}"}
    except Exception as e:
        return {"error": f"Vision extraction error: {str(e)}"}