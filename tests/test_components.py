"""Component-level unit tests for mapper, serializer, validator."""

import pytest

from json2ubl.config import UblConfig
from json2ubl.converter import Json2UblConverter


@pytest.fixture
def converter():
    """Create converter instance."""
    config = UblConfig(schema_root="src/json2ubl/schemas/ubl-2.1")
    return Json2UblConverter(config)


class TestConverterNormalization:
    """Test key normalization."""

    def test_normalize_single_level_keys(self, converter):
        """Test lowercase normalization on single level."""
        data = {"ID": "123", "Name": "Test"}
        result = converter._normalize_keys_recursive(data)
        assert "id" in result
        assert "name" in result
        assert result["id"] == "123"

    def test_normalize_nested_keys(self, converter):
        """Test recursive key normalization."""
        data = {
            "ID": "123",
            "Party": {"CompanyID": "456", "PartyName": "Test"},
        }
        result = converter._normalize_keys_recursive(data)
        assert "id" in result
        assert "party" in result
        assert "companyid" in result["party"]
        assert "partyname" in result["party"]

    def test_normalize_list_items(self, converter):
        """Test normalization of keys in list items."""
        data = {
            "ID": "123",
            "Lines": [{"LineID": "L1", "Amount": "100"}],
        }
        result = converter._normalize_keys_recursive(data)
        assert "id" in result
        assert "lines" in result
        assert "lineid" in result["lines"][0]
        assert "amount" in result["lines"][0]

    def test_normalize_preserves_values(self, converter):
        """Test that normalization preserves non-dict/list values."""
        data = {"ID": 123, "Amount": 45.67, "Active": True, "Note": None}
        result = converter._normalize_keys_recursive(data)
        assert result["id"] == 123
        assert result["amount"] == 45.67
        assert result["active"] is True
        assert result["note"] is None


class TestDocumentTypeMapping:
    """Test document type mapping."""

    def test_valid_document_types(self, converter):
        """Test valid numeric document type codes."""
        valid_types = [
            (380, "Invoice"),
            (381, "CreditNote"),
            (383, "DebitNote"),
            (389, "SelfBilledInvoice"),
            (396, "SelfBilledCreditNote"),
            (780, "FreightInvoice"),
        ]
        from json2ubl.constants import NUMERIC_TYPE_TO_DOCUMENT_TYPE

        for code, expected_type in valid_types:
            actual_type = NUMERIC_TYPE_TO_DOCUMENT_TYPE.get(str(code))
            assert actual_type == expected_type

    def test_invalid_document_type_code(self):
        """Test invalid document type code."""
        from json2ubl.constants import NUMERIC_TYPE_TO_DOCUMENT_TYPE

        assert NUMERIC_TYPE_TO_DOCUMENT_TYPE.get("999") is None


class TestSchemaCacheLoading:
    """Test schema cache operations."""

    def test_load_schema_cache_invoice(self, converter):
        """Test loading Invoice schema cache."""
        cache = converter._load_schema_cache("Invoice")
        assert cache is not None
        assert isinstance(cache, dict)
        assert "elements" in cache or "mappings" in cache or len(cache) > 0

    def test_load_schema_cache_credit_note(self, converter):
        """Test loading CreditNote schema cache."""
        cache = converter._load_schema_cache("CreditNote")
        assert cache is not None

    def test_load_schema_cache_debit_note(self, converter):
        """Test loading DebitNote schema cache."""
        cache = converter._load_schema_cache("DebitNote")
        assert cache is not None

    def test_schema_cache_caching(self, converter):
        """Test that loaded schema caches are reused."""
        cache1 = converter._load_schema_cache("Invoice")
        cache2 = converter._load_schema_cache("Invoice")
        assert cache1 is cache2  # Same object reference


class TestConversionResponseStructure:
    """Test conversion response structure."""

    def test_success_response_structure(self, converter, invoice_dict):
        """Test successful conversion response."""
        result = converter.convert_json_dict_to_xml_dict(invoice_dict)
        assert isinstance(result, dict)
        assert "documents" in result
        assert "summary" in result
        assert "error_response" in result
        assert result["error_response"] is None
        assert len(result["documents"]) == 1

    def test_document_object_structure(self, converter, invoice_dict):
        """Test document object structure."""
        result = converter.convert_json_dict_to_xml_dict(invoice_dict)
        doc = result["documents"][0]
        assert "id" in doc
        assert "xml" in doc
        assert "unmapped_fields" in doc
        assert isinstance(doc["xml"], str)
        assert doc["xml"].startswith("<?xml")

    def test_summary_structure(self, converter, invoice_dict):
        """Test summary structure."""
        result = converter.convert_json_dict_to_xml_dict(invoice_dict)
        summary = result["summary"]
        assert "total_inputs" in summary
        assert "files_created" in summary
        assert "document_types" in summary
        assert isinstance(summary["total_inputs"], int)
        assert isinstance(summary["files_created"], int)
        assert isinstance(summary["document_types"], dict)

    def test_error_response_structure(self, converter, missing_doctype_dict):
        """Test error response structure."""
        result = converter.convert_json_dict_to_xml_dict(missing_doctype_dict)
        assert result["error_response"] is not None
        assert isinstance(result["error_response"], dict)
        assert "error_code" in result["error_response"]
        assert result["summary"]["total_inputs"] == 0
        assert len(result["documents"]) == 0


class TestBatchConversion:
    """Test batch conversion behavior."""

    def test_merge_pages_empty_list(self, converter):
        """Test merging empty page list."""
        result = converter._merge_pages([])
        assert result == {}

    def test_merge_pages_single_page(self, converter):
        """Test merging single page."""
        pages = [{"id": "123", "name": "Test"}]
        result = converter._merge_pages(pages)
        assert result["id"] == "123"
        assert result["name"] == "Test"

    def test_merge_pages_multiple_pages(self, converter):
        """Test merging multiple pages with list fields."""
        pages = [
            {"id": "123", "invoiceLines": [{"id": "L1", "amount": 100}]},
            {"id": "123", "invoiceLines": [{"id": "L2", "amount": 200}]},
        ]
        result = converter._merge_pages(pages)
        assert result["id"] == "123"
        assert len(result["invoiceLines"]) == 2
