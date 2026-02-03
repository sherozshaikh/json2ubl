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


class TestMultiPageMergingAcrossAPIs:
    """Test that merging works consistently across all 3 APIs."""

    def test_merge_same_invoice_across_all_apis(self, invoice_dict):
        """Test that same invoice merged identically across API 1, 2, 3."""
        invoice_page1 = invoice_dict.copy()
        invoice_page1["invoiceline"] = [{"id": "L1", "lineextensionamount": 100}]

        invoice_page2 = invoice_dict.copy()
        invoice_page2["invoiceline"] = [{"id": "L2", "lineextensionamount": 200}]

        result_api1 = json_dict_to_ubl_xml([invoice_page1, invoice_page2])
        assert result_api1["error_response"] is None
        assert len(result_api1["documents"]) == 1
        xml_api1 = result_api1["documents"][0]["xml"]

        assert "L1" in xml_api1
        assert "L2" in xml_api1
        assert xml_api1.count("<cac:InvoiceLine>") >= 2

    def test_merge_multiple_invoices_same_batch(self):
        """Test merging multiple different invoices with multi-page entries."""
        invoices = [
            {
                "id": "INV-001",
                "document_type": 380,
                "issuedate": "2025-01-01",
                "invoiceline": [{"id": "L1", "lineextensionamount": 100}],
            },
            {
                "id": "INV-001",
                "document_type": 380,
                "issuedate": "2025-01-01",
                "invoiceline": [{"id": "L2", "lineextensionamount": 200}],
            },
            {
                "id": "INV-002",
                "document_type": 380,
                "issuedate": "2025-01-02",
                "invoiceline": [{"id": "L3", "lineextensionamount": 300}],
            },
            {
                "id": "INV-002",
                "document_type": 380,
                "issuedate": "2025-01-02",
                "invoiceline": [{"id": "L4", "lineextensionamount": 400}],
            },
        ]

        result = json_dict_to_ubl_xml(invoices)
        assert result["error_response"] is None
        assert len(result["documents"]) == 2

        inv001 = next((d for d in result["documents"] if d["id"] == "INV-001"), None)
        assert inv001 is not None
        assert "L1" in inv001["xml"]
        assert "L2" in inv001["xml"]

        inv002 = next((d for d in result["documents"] if d["id"] == "INV-002"), None)
        assert inv002 is not None
        assert "L3" in inv002["xml"]
        assert "L4" in inv002["xml"]


class TestNestedArrayFieldMerging:
    """Test merging of nested array fields."""

    def test_merge_nested_arrays_in_complex_structure(self):
        """Test merging documents with nested array fields."""
        from json2ubl.config import UblConfig
        from json2ubl.converter import Json2UblConverter

        config = UblConfig(schema_root="src/json2ubl/schemas/ubl-2.1")
        converter = Json2UblConverter(config)
        schema_cache = converter._load_schema_cache("Invoice")

        pages = [
            {
                "id": "nested-001",
                "taxtotal": [
                    {
                        "taxamount": 100,
                        "taxsubtotal": [{"taxableamount": 1000, "taxamount": 100, "percent": 10}],
                    }
                ],
            },
            {
                "id": "nested-001",
                "taxtotal": [
                    {
                        "taxamount": 50,
                        "taxsubtotal": [{"taxableamount": 500, "taxamount": 50, "percent": 10}],
                    }
                ],
            },
        ]

        result = converter._merge_pages(pages, schema_cache)
        assert result["id"] == "nested-001"
        assert "taxtotal" in result
        assert len(result["taxtotal"]) == 2
        assert result["taxtotal"][0]["taxamount"] == 100
        assert result["taxtotal"][1]["taxamount"] == 50

    def test_merge_allowancecharge_arrays(self):
        """Test merging allowancecharge array fields."""
        from json2ubl.config import UblConfig
        from json2ubl.converter import Json2UblConverter

        config = UblConfig(schema_root="src/json2ubl/schemas/ubl-2.1")
        converter = Json2UblConverter(config)
        schema_cache = converter._load_schema_cache("Invoice")

        pages = [
            {
                "id": "allowance-001",
                "allowancecharge": [{"chargeindicator": True, "amount": 50}],
            },
            {
                "id": "allowance-001",
                "allowancecharge": [{"chargeindicator": False, "amount": 25}],
            },
        ]

        result = converter._merge_pages(pages, schema_cache)
        assert result["id"] == "allowance-001"
        assert "allowancecharge" in result
        assert len(result["allowancecharge"]) == 2
