import json
from pathlib import Path

import pytest

from json2ubl import json_dict_to_ubl_xml, json_file_to_ubl_xml_dict


class TestIntegration:
    """Integration tests against test files."""

    @pytest.fixture
    def test_files_dir(self):
        return Path(__file__).parent.parent / "test_files"

    def load_test_file(self, test_files_dir: Path, filename: str):
        """Load test file as list of dicts."""
        file_path = test_files_dir / filename
        assert file_path.exists(), f"Test file not found: {filename}"

        with open(file_path, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]
        return data

    def test_invoice_conversion(self, test_files_dir: Path):
        """Test invoice conversion."""
        documents = self.load_test_file(test_files_dir, "invoice.json")
        response = json_dict_to_ubl_xml(documents)

        assert response["error_response"] is None
        assert len(response["documents"]) > 0
        assert "Invoice" in response["summary"]["document_types"]

    def test_credit_note_conversion(self, test_files_dir: Path):
        """Test credit note conversion."""
        documents = self.load_test_file(test_files_dir, "credit_note.json")
        response = json_dict_to_ubl_xml(documents)

        assert response["error_response"] is None
        assert len(response["documents"]) > 0

    def test_debit_note_conversion(self, test_files_dir: Path):
        """Test debit note conversion."""
        documents = self.load_test_file(test_files_dir, "debit_note.json")
        response = json_dict_to_ubl_xml(documents)

        assert response["error_response"] is None
        assert len(response["documents"]) > 0

    def test_batch_invoices(self, test_files_dir: Path):
        """Test batch invoice processing."""
        documents = self.load_test_file(test_files_dir, "batch_invoices.json")
        response = json_dict_to_ubl_xml(documents)

        assert response["error_response"] is None
        assert len(response["documents"]) == 2
        assert response["summary"]["document_types"]["Invoice"] == 2

    def test_invalid_doctype(self, test_files_dir: Path):
        """Test handling of invalid document type."""
        documents = self.load_test_file(test_files_dir, "invoice_invalid_doctype.json")
        response = json_dict_to_ubl_xml(documents)
        assert response is not None

    def test_missing_doctype(self, test_files_dir: Path):
        """Test handling of missing document type."""
        documents = self.load_test_file(test_files_dir, "invoice_missing_doctype.json")
        response = json_dict_to_ubl_xml(documents)
        assert response is not None

    def test_xml_output_valid(self, test_files_dir: Path):
        """Test that output XML is valid."""
        documents = self.load_test_file(test_files_dir, "invoice.json")
        response = json_dict_to_ubl_xml(documents)

        assert len(response["documents"]) > 0
        xml_string = response["documents"][0]["xml"]
        assert xml_string.startswith("<?xml") or xml_string.startswith("<")
        assert "Invoice" in xml_string or "invoice" in xml_string

    def test_unmapped_fields_tracking(self, test_files_dir: Path):
        """Test that unmapped fields are tracked."""
        documents = self.load_test_file(test_files_dir, "invoice.json")
        response = json_dict_to_ubl_xml(documents)

        assert len(response["documents"]) > 0
        doc = response["documents"][0]
        assert "unmapped_fields" in doc
        assert isinstance(doc["unmapped_fields"], list)

    def test_file_based_conversion(self, test_files_dir: Path):
        """Test file-based conversion method."""
        file_path = str(test_files_dir / "invoice.json")
        response = json_file_to_ubl_xml_dict(file_path)

        assert response["error_response"] is None
        assert len(response["documents"]) > 0
