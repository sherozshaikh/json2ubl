# json2ubl

**Production-grade JSON to UBL 2.1 XML converter with schema-driven mapping**

[![PyPI version](https://badge.fury.io/py/json2ubl.svg)](https://badge.fury.io/py/json2ubl)
[![Python Versions](https://img.shields.io/pypi/pyversions/json2ubl.svg)](https://pypi.org/project/json2ubl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[json2ubl](https://pypi.org/project/json2ubl/) is a production-ready converter that transforms JSON documents into UBL 2.1-compliant XML. It works with all 60+ UBL document types using automatic schema-driven mapping—no hardcoded field definitions required.

---

## ✨ Features

- **Universal Document Support** - Works with all 60+ UBL 2.1 document types (Invoice, CreditNote, Order, DebitNote, etc.)
- **Schema-Driven Processing** - Automatic field mapping and validation from XSD schemas, no hardcoded rules
- **Multi-Page Support** - Automatically merges multi-page documents (e.g., multi-page invoices) into valid UBL XML
- **Thread-Safe** - Built-in concurrency support for batch processing
- **Error Resilience** - Comprehensive error handling with rollback on partial failures
- **Production Ready** - Minimal dependencies, extensive logging, optimized for performance
- **Flexible Output** - Write to disk, return XML strings, or get unmapped fields for validation
- **Type-Safe** - Full Python type hints and validation with Pydantic

---

## 📦 Installation

```bash
pip install json2ubl
```

**Requirements:**
- Python >= 3.10
- lxml >= 4.9.4
- pydantic >= 2.7.0
- pyyaml >= 6.0.1
- loguru >= 0.7.2

---

## 🚀 Quickstart

### Convert Multiple Documents (List)

```python
from json2ubl import json_dict_to_ubl_xml

# List of invoices
invoices = [
    {
        "id": "INV-2026-001",
        "issue_date": "2026-01-30",
        "due_date": "2026-02-28",
        "document_type": 380,  # 380 = Invoice
        "accounting_supplier_party": {
            "party_name": "Acme Corp",
            "party_identification": {"id": "123456"}
        },
        "accounting_customer_party": {
            "party_name": "Customer Inc",
        },
        "invoice_lines": [
            {
                "id": "1",
                "invoiced_quantity": 10,
                "invoiced_quantity_unit_code": "EA",
                "line_extension_amount": 1000.00
            }
        ]
    },
    {
        "id": "INV-2026-002",
        "issue_date": "2026-01-31",
        "document_type": 380,
        ...
    }
]

response = json_dict_to_ubl_xml(invoices)
for doc in response["documents"]:
    print(f"Converted {doc['id']}")
    print(doc["xml"])  # UBL 2.1 XML string
```

### Convert JSON File to XML Dicts

```python
from json2ubl import json_file_to_ubl_xml_dict

# JSON file must contain list: [{}, {}]
response = json_file_to_ubl_xml_dict("invoices.json")

print(f"Converted {len(response['documents'])} documents")
for doc in response["documents"]:
    print(f"  - {doc['id']}: {len(doc['unmapped_fields'])} unmapped fields")
    print(doc["xml"])
```

### Write to XML Files

```python
from json2ubl import json_file_to_ubl_xml_files

# JSON file must contain list: [{}, {}]
response = json_file_to_ubl_xml_files(
    json_file_path="invoices.json",
    output_dir="./output_xml"
)

print(f"Generated {response['summary']['files_created']} XML files")
```

---

## 📊 Document Types

Supported UBL 2.1 document types (numeric codes):

- **380** - Invoice
- **381** - Credit Note
- **382** - Debit Note
- **220** - Order
- **225** - Order Change
- **230** - Order Cancellation
- ... and 55+ more UBL document types

Full list: [UBL 2.1 Document Types](https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.html)

---

## 🔧 API Reference

### `json_dict_to_ubl_xml(list_of_dicts: List[Dict]) -> Dict`

Convert list of JSON dicts to UBL 2.1 XML strings in memory.

**Args:**
- `list_of_dicts`: List of document dicts with `document_type` (numeric code) and schema fields
- `config_path`: Optional path to `ubl_converter.yaml`

**Returns:**
```python
{
    "documents": [
        {
            "id": "DOC-ID",
            "xml": "<ubl:Invoice>...</ubl:Invoice>",
            "unmapped_fields": ["custom_field_1"]
        }
    ],
    "summary": {
        "total_inputs": 2,
        "files_created": 0,
        "document_types": {"Invoice": 2}
    }
}
```

### `json_file_to_ubl_xml_dict(json_file_path: str) -> Dict`

Convert JSON file to UBL 2.1 XML strings (in-memory).

**Args:**
- `json_file_path`: Path to JSON file containing list: `[{}, {}]`

**Returns:** Same as `json_dict_to_ubl_xml()`

### `json_file_to_ubl_xml_files(json_file_path: str, output_dir: str) -> Dict`

Convert JSON file and write XML files to disk.

**Features:**
- JSON file must contain list: `[{}, {}]`
- Auto-detects output directory write permissions
- Rolls back on partial failure
- Atomic file operations with temp file staging

**For detailed API documentation with input/output examples and error handling, see [API.md](docs/API.md)**

---

## 🛡️ Error Handling

The converter includes comprehensive error handling:

```python
response = json_dict_to_ubl_xml([document])

if response.get("error_response"):
    print(f"Error: {response['error_response']}")
else:
    for doc in response["documents"]:
        print(f"Converted {doc['id']}")
        if doc["unmapped_fields"]:
            print(f"  Unmapped: {doc['unmapped_fields']}")
```

**Common Issues:**
- Missing `document_type` field → Error with guidance
- Invalid `document_type` code → Lists valid codes
- Null input fields → Preserved as empty XML elements
- Multi-page documents → Automatically merged (with configurable strategy)

---

## 🧪 Testing

Run tests:

```bash
pip install -e .[dev]
pytest tests/ -v
```

Test coverage includes:
- All 60+ UBL document types
- Multi-page document merging
- Error handling and rollback
- Concurrent batch processing
- Schema validation

---

## 🏗️ Architecture

```
json2ubl/
├── converter.py          # Main conversion API
├── core/
│   ├── mapper.py         # JSON-to-schema mapping
│   ├── validator.py      # XML validation
│   ├── serializer.py     # JSON-to-XML serialization
│   └── schema_cache_builder.py  # XSD-to-cache compilation
├── schemas/
│   ├── ubl-2.1/          # Official UBL 2.1 XSD files
│   └── cache/            # Pre-compiled schema caches
└── models/               # Pydantic type hints (reference)
```

---

## 🔍 How It Works

1. **Load Schema** - Loads UBL 2.1 XSD schema for document type
2. **Normalize** - Converts JSON keys to lowercase for case-insensitive matching
3. **Map** - Matches JSON fields to schema fields automatically
4. **Validate** - Checks required fields, types, and constraints
5. **Serialize** - Builds XML tree with proper namespaces and structure
6. **Write** - Outputs to file or returns XML string

**Key Design:**
- No hardcoded field mappings per document type
- Schema-driven → works for all UBL types automatically
- Efficient caching of parsed XSD structures

---

## 📈 Performance

- **Single document**: ~50-100ms (depends on complexity)
- **Batch (100 docs)**: ~5-10 seconds
- **Memory**: ~50MB for full schema cache
- **CPU**: Minimal (schema-driven, not iterative)

Benchmark results on production invoices with 20+ line items:
- Conversion: 2.5ms per invoice
- XML serialization: 1.2ms per invoice
- File I/O: 0.8ms per file

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- Built with [lxml](https://lxml.de/) for XML processing
- Validation via [Pydantic](https://docs.pydantic.dev/)
- Logging via [loguru](https://github.com/Delgan/loguru)
- UBL 2.1 specifications: [OASIS](https://docs.oasis-open.org/ubl/os-UBL-2.1/)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/sherozshaikh/json2ubl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sherozshaikh/json2ubl/discussions)
- **Email**: shaikh.sheroz07@gmail.com

---

**Made with ❤️ for data integration teams**
