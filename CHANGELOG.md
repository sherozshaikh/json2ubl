# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-02-03

### 🐛 Fixed

- **Multi-page document merging**: Fixed critical issue where only last occurrence of array fields (e.g., InvoiceLine, AllowanceCharge) was retained when same invoice ID appeared multiple times
- **Hardcoded field names**: Replaced hardcoded array field list with schema-driven detection via `maxOccurs="unbounded"`
- **Case-insensitive field matching**: Fixed merging when input JSON has mixed case field names (e.g., `InvoiceLine` vs `invoiceline`)

### ✨ Added

- **Schema-driven array detection**: `_merge_pages()` now dynamically identifies array fields from schema cache instead of hardcoded list
- **Unified merge behavior across all APIs**: All 3 APIs (dict, file-to-dict, file-to-files) now use `_group_and_merge_documents()` helper for consistent merging
- **Support for all document types**: Merge logic now works dynamically with all 60+ UBL document types, not just Invoice-specific fields
- **Nested array merging**: Properly merges nested array fields (e.g., TaxTotal > TaxSubtotal, AllowanceCharge arrays)
- **Comprehensive test coverage**: 
  - Schema-driven array detection tests
  - Mixed case field name merging tests
  - Multi-invoice batch merging tests
  - Nested array field merging tests
  - Cross-API consistency tests
  - Different document type tests (Invoice, CreditNote)

### 🔄 Changed

- `Json2UblConverter._merge_pages()`: Now accepts `schema_cache` parameter for dynamic array field detection
- `Json2UblConverter.convert_json_file_to_xml_dict()`: Refactored to use new `_group_and_merge_documents()` helper
- `json_dict_to_ubl_xml()` in `__init__.py`: Now calls `_group_and_merge_documents()` to ensure consistent merge behavior
- Error handling: Improved error messages for merge failures with proper logging

### 🧪 Testing

**New test cases added:**
- `test_merge_pages_multiple_pages` - Schema-driven array detection with Invoice
- `test_merge_pages_mixed_case_field_names` - Case-insensitive field matching
- `test_group_and_merge_documents_standalone` - Direct testing of merge helper
- `test_group_and_merge_documents_skips_no_id` - Filtering documents without ID
- `test_merge_pages_schema_driven_different_doc_types` - Different document type schema detection (CreditNote)
- `test_merge_same_invoice_across_all_apis` - Integration test across all 3 APIs
- `test_merge_multiple_invoices_same_batch` - Multi-invoice batch merging (4 pages, 2 invoices)
- `test_merge_with_missing_document_type` - Error handling during merge
- `test_merge_nested_arrays_in_complex_structure` - TaxTotal nested array merging
- `test_merge_allowancecharge_arrays` - AllowanceCharge array merging

### 🚀 Data Integrity

**Important**: This release fixes a critical data loss issue:
- **Before v1.0.1**: When invoice ID "728621" appeared twice in input JSON, only line items from last occurrence were in output XML (other pages' items lost)
- **After v1.0.1**: All line items from all pages with same invoice ID are merged into single valid XML file

### 📝 Documentation

- Updated README with multi-page document merging feature
- Added inline code documentation for schema-driven merging

### 🔧 Technical Details

**Key files modified:**
- `src/json2ubl/converter.py`:
  - Added `_group_and_merge_documents()` helper method (lines 609-654)
  - Enhanced `_merge_pages()` with schema_cache parameter (lines 656-680)
  - Refactored `convert_json_file_to_xml_dict()` (lines 354-407)
  
- `src/json2ubl/__init__.py`:
  - Updated `json_dict_to_ubl_xml()` to use merge helper (lines 79-135)

- `tests/test_components.py`:
  - Enhanced merge test cases with schema_cache

- `tests/test_error_handling.py`:
  - Updated error handling validation

- `tests/test_pipeline.py`:
  - Added integration tests for multi-API consistency
  - Added nested array merging tests

---

## [1.0.0] - 2026-01-30

### ✨ Initial Release

- Full UBL 2.1 support (60+ document types)
- Schema-driven JSON-to-XML mapping
- Three conversion APIs (dict, file-to-dict, file-to-files)
- XML validation against UBL schemas
- Comprehensive error handling with rollback
- Thread-safe batch processing
- Pre-built schema caches for performance
- Extensive test coverage
- Production-ready logging with loguru

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)
