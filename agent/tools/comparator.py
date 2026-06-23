"""
Gap-Based Insurance Comparison Engine.
Identifies weaknesses in current plan and checks if new plan fixes them.
"""

import json
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5vl:7b"


def compare_plans(current_plan: dict, new_plan: dict) -> dict:
    prompt = f"""You are a senior insurance advisor in India with 20 years of experience.

You are comparing two health insurance plans for a client.

CURRENT PLAN (what the person has NOW):
{json.dumps(current_plan, indent=2)}

NEW PLAN (what the person is CONSIDERING):
{json.dumps(new_plan, indent=2)}

Your task:
1. Identify the TOP weaknesses/gaps/demerits of the CURRENT plan
2. For each weakness, check if the NEW plan addresses or fixes it
3. Also note any areas where the current plan is BETTER than the new plan (be honest)
4. Calculate if the new plan is worth it (consider premium difference vs benefits gained)
5. Give an overall verdict and recommendation

Return ONLY a valid JSON object in this exact format:
{{
  "policyholder_name": "",
  "current_plan_name": "",
  "new_plan_name": "",
  "weaknesses_and_fixes": [
    {{
      "weakness": "Description of what is bad/missing in current plan",
      "current_value": "What current plan offers",
      "new_value": "What new plan offers",
      "is_fixed": true,
      "impact": "High/Medium/Low",
      "explanation": "Plain language explanation of why this matters"
    }}
  ],
  "areas_current_is_better": [
    {{
      "area": "Area name",
      "current_value": "",
      "new_value": "",
      "explanation": ""
    }}
  ],
  "premium_analysis": {{
    "current_premium": "",
    "new_premium": "",
    "difference": "",
    "is_worth_it": true,
    "reasoning": ""
  }},
  "overall_score": {{
    "current_plan_score": 0,
    "new_plan_score": 0,
    "max_score": 10
  }},
  "verdict": "SWITCH / STAY / CONSIDER",
  "verdict_reasoning": "Plain language explanation of the final recommendation",
  "key_highlights": []
}}

Be specific with Indian insurance context (IRDAI, room rent ratios, waiting periods, CSR).
Return ONLY JSON. No markdown, no explanation."""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=180
        )
        if response.status_code == 200:
            raw = response.json().get("response", "").strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        return {"error": "Comparison LLM call failed"}

    except requests.exceptions.ConnectionError:
        return {"error": "Ollama not running. Start with: ollama serve"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error in comparison: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def format_comparison_for_display(comparison: dict) -> str:
    if "error" in comparison:
        return f"❌ Comparison Error: {comparison['error']}"

    lines = []
    lines.append("=" * 70)
    lines.append(f"  INSURANCE COMPARISON REPORT")
    lines.append(f"  Policyholder: {comparison.get('policyholder_name', 'N/A')}")
    lines.append(f"  Current Plan: {comparison.get('current_plan_name', 'N/A')}")
    lines.append(f"  New Plan:     {comparison.get('new_plan_name', 'N/A')}")
    lines.append("=" * 70)

    lines.append("\n❌ WEAKNESSES IN YOUR CURRENT PLAN → ✅ HOW NEW PLAN FIXES IT")
    lines.append("-" * 70)
    for item in comparison.get("weaknesses_and_fixes", []):
        fixed = "✅" if item.get("is_fixed") else "⚠️ Not Fixed"
        impact = item.get("impact", "")
        lines.append(f"\n❌ [{impact} Impact] {item.get('weakness', '')}")
        lines.append(f"   Current: {item.get('current_value', 'N/A')}")
        lines.append(f"   New:     {item.get('new_value', 'N/A')}  {fixed}")
        lines.append(f"   Why it matters: {item.get('explanation', '')}")

    better = comparison.get("areas_current_is_better", [])
    if better:
        lines.append("\n\n⚠️  AREAS WHERE YOUR CURRENT PLAN IS BETTER")
        lines.append("-" * 70)
        for item in better:
            lines.append(f"\n• {item.get('area', '')}")
            lines.append(f"  Current: {item.get('current_value', '')}")
            lines.append(f"  New:     {item.get('new_value', '')}")

    premium = comparison.get("premium_analysis", {})
    lines.append("\n\n💰 PREMIUM ANALYSIS")
    lines.append("-" * 70)
    lines.append(f"  Current Premium: {premium.get('current_premium', 'N/A')}")
    lines.append(f"  New Premium:     {premium.get('new_premium', 'N/A')}")
    lines.append(f"  Difference:      {premium.get('difference', 'N/A')}")
    lines.append(f"  Worth it?:       {'✅ Yes' if premium.get('is_worth_it') else '❌ No'}")
    lines.append(f"  Reasoning:       {premium.get('reasoning', '')}")

    scores = comparison.get("overall_score", {})
    lines.append("\n\n⭐ OVERALL SCORES")
    lines.append("-" * 70)
    lines.append(f"  Current Plan: {scores.get('current_plan_score', 'N/A')} / {scores.get('max_score', 10)}")
    lines.append(f"  New Plan:     {scores.get('new_plan_score', 'N/A')} / {scores.get('max_score', 10)}")

    verdict = comparison.get("verdict", "N/A")
    verdict_icon = {"SWITCH": "🔄", "STAY": "✋", "CONSIDER": "🤔"}.get(verdict, "📋")
    lines.append("\n\n" + "=" * 70)
    lines.append(f"  {verdict_icon} FINAL VERDICT: {verdict}")
    lines.append(f"  {comparison.get('verdict_reasoning', '')}")
    lines.append("=" * 70)

    highlights = comparison.get("key_highlights", [])
    if highlights:
        lines.append("\n📌 KEY HIGHLIGHTS:")
        for h in highlights:
            lines.append(f"   • {h}")

    return "\n".join(lines)