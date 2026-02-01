from pathlib import Path

from json2ubl import json_dict_to_ubl_xml, json_file_to_ubl_xml_dict, json_file_to_ubl_xml_files


class TestInvoicePipeline:
    """Test Invoice (380) document type."""

    def test_invoice_dict_to_xml(self, invoice_dict):
        """Method 1: Convert Invoice dict to XML."""
        result = json_dict_to_ubl_xml([invoice_dict])
        assert result["error_response"] is None
        assert len(result["documents"]) == 1
        assert result["documents"][0]["id"] == "INV-2025-001"
        assert result["documents"][0]["xml"]
        assert "Invoice" in result["summary"]["document_types"]

    def test_invoice_file_to_dict(self, test_files_dir):
        """Method 2: Convert Invoice file to XML dicts."""
        result = json_file_to_ubl_xml_dict(str(test_files_dir / "invoice.json"))
        assert result["error_response"] is None
        assert len(result["documents"]) == 1
        assert result["documents"][0]["id"] == "INV-2025-001"

    def test_invoice_file_to_files(self, test_files_dir, tmp_path):
        """Method 3: Convert Invoice file and write to disk."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files(str(test_files_dir / "invoice.json"), output_dir)
        assert result["error_response"] is None
        assert result["summary"]["files_created"] == 1
        xml_files = list(Path(output_dir).glob("*.xml"))
        assert len(xml_files) == 1


class TestCreditNotePipeline:
    """Test CreditNote (381) document type."""

    def test_credit_note_dict_to_xml(self, credit_note_dict):
        """Method 1: Convert CreditNote dict to XML."""
        result = json_dict_to_ubl_xml([credit_note_dict])
        assert result["error_response"] is None
        assert len(result["documents"]) == 1
        assert result["documents"][0]["id"] == "CN-2025-001"
        assert "CreditNote" in result["summary"]["document_types"]

    def test_credit_note_file_to_dict(self, test_files_dir):
        """Method 2: Convert CreditNote file to XML dicts."""
        result = json_file_to_ubl_xml_dict(str(test_files_dir / "credit_note.json"))
        assert result["error_response"] is None
        assert len(result["documents"]) == 1

    def test_credit_note_file_to_files(self, test_files_dir, tmp_path):
        """Method 3: Convert CreditNote file and write to disk."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files(str(test_files_dir / "credit_note.json"), output_dir)
        assert result["error_response"] is None
        assert result["summary"]["files_created"] == 1


class TestDebitNotePipeline:
    """Test DebitNote (383) document type."""

    def test_debit_note_dict_to_xml(self, debit_note_dict):
        """Method 1: Convert DebitNote dict to XML."""
        result = json_dict_to_ubl_xml([debit_note_dict])
        assert result["error_response"] is None
        assert len(result["documents"]) == 1
        assert result["documents"][0]["id"] == "DN-2025-001"
        assert "DebitNote" in result["summary"]["document_types"]

    def test_debit_note_file_to_dict(self, test_files_dir):
        """Method 2: Convert DebitNote file to XML dicts."""
        result = json_file_to_ubl_xml_dict(str(test_files_dir / "debit_note.json"))
        assert result["error_response"] is None
        assert len(result["documents"]) == 1

    def test_debit_note_file_to_files(self, test_files_dir, tmp_path):
        """Method 3: Convert DebitNote file and write to disk."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files(str(test_files_dir / "debit_note.json"), output_dir)
        assert result["error_response"] is None
        assert result["summary"]["files_created"] == 1


class TestSelfBilledInvoicePipeline:
    """Test SelfBilledInvoice (389) document type."""

    def test_self_billed_invoice_dict_to_xml(self, self_billed_invoice_dict):
        """Method 1: Convert SelfBilledInvoice dict to XML."""
        result = json_dict_to_ubl_xml([self_billed_invoice_dict])
        assert result["error_response"] is None
        assert len(result["documents"]) == 1
        assert result["documents"][0]["id"] == "SBI-2025-001"
        assert "SelfBilledInvoice" in result["summary"]["document_types"]

    def test_self_billed_invoice_file_to_dict(self, test_files_dir):
        """Method 2: Convert SelfBilledInvoice file to XML dicts."""
        result = json_file_to_ubl_xml_dict(str(test_files_dir / "self_billed_invoice.json"))
        assert result["error_response"] is None
        assert len(result["documents"]) == 1

    def test_self_billed_invoice_file_to_files(self, test_files_dir, tmp_path):
        """Method 3: Convert SelfBilledInvoice file and write to disk."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files(
            str(test_files_dir / "self_billed_invoice.json"), output_dir
        )
        assert result["error_response"] is None
        assert result["summary"]["files_created"] == 1


class TestSelfBilledCreditNotePipeline:
    """Test SelfBilledCreditNote (396) document type."""

    def test_self_billed_credit_note_dict_to_xml(self, self_billed_credit_note_dict):
        """Method 1: Convert SelfBilledCreditNote dict to XML."""
        result = json_dict_to_ubl_xml([self_billed_credit_note_dict])
        assert result["error_response"] is None
        assert len(result["documents"]) == 1
        assert result["documents"][0]["id"] == "SBCN-2025-001"
        assert "SelfBilledCreditNote" in result["summary"]["document_types"]

    def test_self_billed_credit_note_file_to_dict(self, test_files_dir):
        """Method 2: Convert SelfBilledCreditNote file to XML dicts."""
        result = json_file_to_ubl_xml_dict(str(test_files_dir / "self_billed_credit_note.json"))
        assert result["error_response"] is None
        assert len(result["documents"]) == 1

    def test_self_billed_credit_note_file_to_files(self, test_files_dir, tmp_path):
        """Method 3: Convert SelfBilledCreditNote file and write to disk."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files(
            str(test_files_dir / "self_billed_credit_note.json"), output_dir
        )
        assert result["error_response"] is None
        assert result["summary"]["files_created"] == 1


class TestFreightInvoicePipeline:
    """Test FreightInvoice (780) document type."""

    def test_freight_invoice_dict_to_xml(self, freight_invoice_dict):
        """Method 1: Convert FreightInvoice dict to XML."""
        result = json_dict_to_ubl_xml([freight_invoice_dict])
        assert result["error_response"] is None
        assert len(result["documents"]) == 1
        assert result["documents"][0]["id"] == "FI-2025-001"
        assert "FreightInvoice" in result["summary"]["document_types"]

    def test_freight_invoice_file_to_dict(self, test_files_dir):
        """Method 2: Convert FreightInvoice file to XML dicts."""
        result = json_file_to_ubl_xml_dict(str(test_files_dir / "freight_invoice.json"))
        assert result["error_response"] is None
        assert len(result["documents"]) == 1

    def test_freight_invoice_file_to_files(self, test_files_dir, tmp_path):
        """Method 3: Convert FreightInvoice file and write to disk."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files(
            str(test_files_dir / "freight_invoice.json"), output_dir
        )
        assert result["error_response"] is None
        assert result["summary"]["files_created"] == 1
