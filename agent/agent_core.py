"""
Pipeline Orchestrator — ties all modules together.
"""

from agent.tools.extractor import extract_document, parse_insurance_fields
from agent.tools.comparator import compare_plans, format_comparison_for_display
from agent.tools.reporter import generate_pdf_report


def run_comparison(current_plan_path: str, new_plan_path: str, person_name: str = None) -> dict:
    print("Step 1: Extracting current plan...")
    current_raw = extract_document(current_plan_path, person_name)
    current_fields = parse_insurance_fields(current_raw["raw_text"], label="current")

    print("Step 2: Extracting new plan...")
    new_raw = extract_document(new_plan_path)
    new_fields = parse_insurance_fields(new_raw["raw_text"], label="new")

    print("Step 3: Comparing plans...")
    comparison = compare_plans(current_fields, new_fields)

    print("Step 4: Generating report...")
    report_path = generate_pdf_report(comparison)

    return {
        "current_fields": current_fields,
        "new_fields": new_fields,
        "comparison": comparison,
        "display": format_comparison_for_display(comparison),
        "report_path": report_path
    }