# JSON to UBL 2.1 XML Converter - API Documentation

**Package:** `json2ubl>=1.0.0`  
**Installation:** `pip install json2ubl>=1.0.0`

---

## Overview

The json2ubl package provides three APIs to convert JSON documents to UBL 2.1-compliant XML format. All APIs support all 60+ UBL document types using schema-driven automatic mapping.

---

## API 1: `json_dict_to_ubl_xml()`

Convert a list of JSON dictionaries to UBL XML strings in memory.

### Function Signature

```python
from json2ubl import json_dict_to_ubl_xml

response = json_dict_to_ubl_xml(
    list_of_dicts: List[Dict[str, Any]],
    config_path: str | None = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `list_of_dicts` | `List[Dict]` | Yes | List of document dictionaries to convert |
| `config_path` | `str` | No | Path to optional `ubl_converter.yaml` config file |

### Input Format

Each dictionary must contain:
- `id` - Document identifier (required)
- `document_type` - Numeric code (required). Examples: 380=Invoice, 381=CreditNote, 382=DebitNote
- Schema fields matching UBL 2.1 structure (case-insensitive)

**Example Input:**
```python
invoices = [
    {
        "id": "INV-2026-001",
        "document_type": 380,  # Invoice
        "issue_date": "2026-01-30",
        "accounting_supplier_party": {
            "party_name": "Supplier Inc",
            "party_identification": {"id": "12345"}
        },
        "accounting_customer_party": {
            "party_name": "Customer Ltd"
        },
        "invoice_lines": [
            {
                "id": "1",
                "invoiced_quantity": 10,
                "invoiced_quantity_unit_code": "EA",
                "line_extension_amount": 1000.00
            }
        ]
    }
]

response = json_dict_to_ubl_xml(invoices)
```

### Response Format

```python
{
    "documents": [
        {
            "id": "INV-2026-001",
            "xml": "<ubl:Invoice xmlns:ubl='urn:...'> ... </ubl:Invoice>",
            "unmapped_fields": ["custom_field_1", "custom_field_2"]
        }
    ],
    "summary": {
        "total_inputs": 1,
        "files_created": 0,
        "document_types": {"Invoice": 1}
    },
    "error_response": None
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `documents` | `List[Dict]` | List of converted documents |
| `documents[].id` | `str` | Document identifier from input |
| `documents[].xml` | `str` | Generated UBL 2.1 XML string |
| `documents[].unmapped_fields` | `List[str]` | JSON fields not found in UBL schema |
| `summary` | `Dict` | Conversion statistics |
| `summary.total_inputs` | `int` | Number of documents processed |
| `summary.files_created` | `int` | Always 0 for this API |
| `summary.document_types` | `Dict` | Count by document type (e.g., `{"Invoice": 1}`) |
| `error_response` | `Dict\|None` | Error details if conversion failed |

### Error Response

On failure, `error_response` contains:

```python
{
    "error_code": "MISSING_DOCUMENT_TYPE",  # or INVALID_DOCUMENT_TYPE, etc
    "message": "Missing required field: document_type",
    "details": {
        "doc_id": "INV-2026-001",
        "required_field": "document_type"
    }
}
```

### Usage Example

```python
from json2ubl import json_dict_to_ubl_xml

invoices = [
    {
        "id": "INV-001",
        "document_type": 380,
        "issue_date": "2026-01-31",
        "accounting_supplier_party": {"party_name": "ABC Corp"},
        "accounting_customer_party": {"party_name": "XYZ Ltd"},
        "invoice_lines": [{"id": "1", "line_extension_amount": 500.00}]
    }
]

response = json_dict_to_ubl_xml(invoices)

if response.get("error_response"):
    print(f"Error: {response['error_response']['message']}")
else:
    for doc in response["documents"]:
        print(f"✓ {doc['id']} converted")
        print(f"  Unmapped: {doc['unmapped_fields']}")
        # Save XML or process further
        with open(f"{doc['id']}.xml", "w") as f:
            f.write(doc["xml"])
```

### Common Errors

| Error Code | Cause | Solution |
|------------|-------|----------|
| `MISSING_DOCUMENT_TYPE` | Missing `document_type` field | Add numeric document type code |
| `INVALID_DOCUMENT_TYPE` | Wrong `document_type` value | Use valid code (380=Invoice, 381=CreditNote, etc) |
| `MappingError` | Invalid JSON structure | Verify field names match UBL schema |

---

## API 2: `json_file_to_ubl_xml_dict()`

Convert JSON file to UBL XML strings and return in memory (batch processing).

### Function Signature

```python
from json2ubl import json_file_to_ubl_xml_dict

response = json_file_to_ubl_xml_dict(
    json_file_path: str,
    config_path: str | None = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `json_file_path` | `str` | Yes | Path to JSON file containing list of documents |
| `config_path` | `str` | No | Path to optional config file |

### Input Format

JSON file must contain a list array:

**example.json:**
```json
[
  {
    "id": "INV-001",
    "document_type": 380,
    "issue_date": "2026-01-31",
    "accounting_supplier_party": {"party_name": "Supplier"},
    "accounting_customer_party": {"party_name": "Customer"},
    "invoice_lines": [{"id": "1", "line_extension_amount": 1000}]
  },
  {
    "id": "INV-002",
    "document_type": 380,
    "issue_date": "2026-02-01",
    ...
  }
]
```

### Response Format

Same as API 1:

```python
{
    "documents": [
        {"id": "INV-001", "xml": "...", "unmapped_fields": []},
        {"id": "INV-002", "xml": "...", "unmapped_fields": []}
    ],
    "summary": {
        "total_inputs": 2,
        "files_created": 0,
        "document_types": {"Invoice": 2}
    },
    "error_response": None
}
```

### Usage Example

```python
from json2ubl import json_file_to_ubl_xml_dict

response = json_file_to_ubl_xml_dict("invoices.json")

if response.get("error_response"):
    print(f"Error: {response['error_response']['message']}")
    print(f"Details: {response['error_response']['details']}")
else:
    print(f"✓ Converted {len(response['documents'])} documents")
    print(f"  Summary: {response['summary']}")
    
    for doc in response["documents"]:
        print(f"  - {doc['id']}: {len(doc['unmapped_fields'])} unmapped fields")
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError` | JSON file not found | Verify file path exists |
| `JSONDecodeError` | Invalid JSON format | Validate JSON syntax |
| `MISSING_DOCUMENT_TYPE` | Document missing `document_type` | Add type to all documents |

---

## API 3: `json_file_to_ubl_xml_files()`

Convert JSON file and write XML files directly to disk.

### Function Signature

```python
from json2ubl import json_file_to_ubl_xml_files

response = json_file_to_ubl_xml_files(
    json_file_path: str,
    output_dir: str,
    config_path: str | None = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `json_file_path` | `str` | Yes | Path to input JSON file |
| `output_dir` | `str` | Yes | Directory where XML files will be written |
| `config_path` | `str` | No | Path to optional config file |

### Response Format

Same structure as API 1 & 2, but **without** XML content:

```python
{
    "documents": [
        {
            "id": "INV-001",
            "unmapped_fields": []
        },
        {
            "id": "INV-002",
            "unmapped_fields": []
        }
    ],
    "summary": {
        "total_inputs": 2,
        "files_created": 2,
        "document_types": {"Invoice": 2}
    },
    "error_response": None
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `documents` | `List[Dict]` | List of processed documents (no XML) |
| `documents[].id` | `str` | Document identifier |
| `documents[].unmapped_fields` | `List[str]` | Fields not in UBL schema |
| `summary.files_created` | `int` | Number of XML files written to disk |
| `error_response` | `Dict\|None` | Error if conversion failed |

**Note:** `xml` field is omitted to reduce response payload when writing to disk.

### Output Files

Generated files are named: `{document_id}.xml`

```
output_dir/
├── INV-001.xml
├── INV-002.xml
└── CR-001.xml
```

### Usage Example

```python
from json2ubl import json_file_to_ubl_xml_files
import os

response = json_file_to_ubl_xml_files(
    json_file_path="batch_invoices.json",
    output_dir="./output_xml"
)

if response.get("error_response"):
    print(f"❌ Error: {response['error_response']['message']}")
else:
    files_created = response["summary"]["files_created"]
    print(f"✓ Successfully created {files_created} XML files")
    print(f"  Location: {os.path.abspath('./output_xml')}")
    
    for doc in response["documents"]:
        unmapped = len(doc["unmapped_fields"])
        print(f"  - {doc['id']}: {unmapped} unmapped fields")
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError` | Input file not found | Verify input JSON path |
| `PermissionError` | Cannot write to output_dir | Check directory permissions |
| `INVALID_DOCUMENT_TYPE` | Document type invalid | Fix document_type values |

---

## Supported Document Types

The converter supports all 60+ UBL 2.1 document types. Common ones:

| Code | Document Type |
|------|----------------|
| 380 | Invoice |
| 381 | Credit Note |
| 382 | Debit Note |
| 220 | Order |
| 225 | Order Change |
| 230 | Order Cancellation |

For full list, see [UBL 2.1 Specification](https://docs.oasis-open.org/ubl/os-UBL-2.1/)

---

## Field Mapping

- Input JSON keys are **case-insensitive** (automatically normalized to lowercase)
- Fields not in UBL schema are tracked in `unmapped_fields`
- Null values are preserved as empty XML elements
- Nested structures follow UBL hierarchy automatically

---

## Configuration (Optional)

Create `ubl_converter.yaml` for custom settings:

```yaml
schema_root: "./custom_schemas"
max_recursion_depth: 20
enable_logging: true
log_file: "converter.log"
```

Pass to any API:
```python
response = json_dict_to_ubl_xml(invoices, config_path="ubl_converter.yaml")
```

---

## Best Practices

1. **Validate input before conversion** - Ensure `id` and `document_type` are present
2. **Check `unmapped_fields`** - Review fields not in UBL schema
3. **Handle errors gracefully** - Always check `error_response` before processing
4. **Use API 3 for large batches** - Better for 1000+ documents (writes to disk directly)
5. **Log conversions** - Track which documents failed for auditing

---

## Error Handling Pattern

```python
from json2ubl import json_dict_to_ubl_xml

def convert_safely(documents):
    response = json_dict_to_ubl_xml(documents)
    
    # Check for errors
    if response.get("error_response"):
        error = response["error_response"]
        print(f"Error Code: {error['error_code']}")
        print(f"Message: {error['message']}")
        print(f"Details: {error['details']}")
        return None
    
    # Process successful conversions
    for doc in response["documents"]:
        if doc["unmapped_fields"]:
            print(f"Warning: {doc['id']} has unmapped fields: {doc['unmapped_fields']}")
        
        # Use XML or save to file
        print(f"✓ {doc['id']} converted successfully")
    
    return response

# Usage
result = convert_safely(invoices)
```

---

## Summary

| API | Use Case | Output | Best For |
|-----|----------|--------|----------|
| **API 1** | Single/few documents | XML in memory | Real-time API responses |
| **API 2** | Batch processing | XML in memory | Reports, archives |
| **API 3** | Bulk files | XML on disk | High-volume batch jobs |

All three APIs return consistent response structure with documents, summary, and error_response fields.
