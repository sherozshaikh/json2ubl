#!/usr/bin/env python3
"""
Generate UBL 2.1 schema templates and examples for LLM prompt engineering.

Usage:
    python generate_schema_examples.py Invoice CreditNote

Output: schema_templates/ folder with JSON files
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent / "src"))


def build_schema_template(
    schema_elements: Dict[str, Any],
    doc_type: str = None,
    max_depth: int = 3,
    current_depth: int = 0,
) -> Dict[str, Any]:
    """Build template from schema with example values."""
    if current_depth >= max_depth:
        return None

    template = {}

    # Add document_type at root level only
    if current_depth == 0 and doc_type:
        template["document_type"] = doc_type
        template["ublVersionID"] = "2.1"

    sample_values = {
        "id": "DOC-2026-001",
        "issuedate": "2026-01-20",
        "duedate": "2026-02-20",
        "name": "Sample Company",
        "description": "Sample Description",
        "amount": 1000.00,
        "percent": 10.0,
        "quantity": 5,
        "code": "SAMPLE",
        "telephone": "+1-555-0123",
        "electronicmail": "contact@example.com",
        "streetname": "123 Main Street",
        "cityname": "New York",
        "postalzone": "10001",
        "identificationcode": "US",
    }

    for field_name, field_schema in schema_elements.items():
        field_type = field_schema.get("type", "").lower()
        max_occurs = field_schema.get("maxOccurs", "1")

        # Determine if array
        is_array = max_occurs == "unbounded" or (max_occurs != "1" and max_occurs != "0")

        # Example value based on field name
        example_value = None
        field_lower = field_name.lower()

        if "nested_elements" in field_schema:
            nested_template = build_schema_template(
                field_schema["nested_elements"], None, max_depth, current_depth + 1
            )
            example_value = nested_template if nested_template else {}
        else:
            # Find matching sample value
            for key, val in sample_values.items():
                if key in field_lower:
                    example_value = val
                    break

            # Fallback by type
            if example_value is None:
                if field_type == "xsd:decimal":
                    example_value = 100.00
                elif field_type == "xsd:boolean":
                    example_value = True
                elif field_type == "xsd:date":
                    example_value = "2026-01-20"
                elif "id" in field_lower or "code" in field_lower:
                    example_value = "SAMPLE-001"
                elif "name" in field_lower:
                    example_value = "Sample Value"
                else:
                    example_value = None

        # Add to template
        if is_array and example_value is not None:
            template[field_name] = [example_value]
        elif example_value is not None:
            template[field_name] = example_value

    return template if template else {}


def generate_examples(doc_types: List[str]) -> None:
    """Generate schema templates and examples."""
    output_dir = Path(__file__).parent / "schema_templates"
    output_dir.mkdir(exist_ok=True)

    # Document type to code mapping
    doc_type_codes = {
        "Invoice": "380",
        "CreditNote": "381",
        "DebitNote": "383",
        "Order": "220",
    }

    for doc_type in doc_types:
        print(f"Generating schema for {doc_type}...")

        try:
            # Get cache file
            cache_file = (
                Path(__file__).parent
                / "src"
                / "json2ubl"
                / "schemas"
                / "cache"
                / f"{doc_type}_schema_cache.json"
            )

            if not cache_file.exists():
                print(f"  ❌ Schema cache not found: {doc_type}")
                continue

            with open(cache_file) as f:
                cache_data = json.load(f)

            schema_elements = cache_data.get("elements", {})

            # Get numeric code for document_type
            doc_code = doc_type_codes.get(doc_type, doc_type)

            # Generate template with numeric code
            template = build_schema_template(schema_elements, doc_code)

            # Save template
            template_file = output_dir / f"{doc_type}_schema_template.json"
            with open(template_file, "w") as f:
                json.dump(template, f, indent=2)
            print(f"  ✓ Template: {template_file}")

            # Save example with actual data
            example_file = output_dir / f"{doc_type}_example.json"
            with open(example_file, "w") as f:
                json.dump(template, f, indent=2)
            print(f"  ✓ Example: {example_file}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n✅ Output folder: {output_dir}")
    print(f"   Files generated for: {', '.join(doc_types)}")


if __name__ == "__main__":
    doc_types = sys.argv[1:] if len(sys.argv) > 1 else ["Invoice", "CreditNote"]
    generate_examples(doc_types)
