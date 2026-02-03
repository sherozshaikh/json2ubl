from json2ubl import json_dict_to_ubl_xml, json_file_to_ubl_xml_dict, json_file_to_ubl_xml_files


class TestDocumentTypeValidation:
    """Test document_type validation."""

    def test_missing_document_type(self, missing_doctype_dict):
        """Test missing document_type field with grouping/merge."""
        result = json_dict_to_ubl_xml([missing_doctype_dict])
        assert result["error_response"] is not None
        error_msg = (
            result["error_response"].get("message", "")
            if isinstance(result["error_response"], dict)
            else str(result["error_response"])
        )
        assert (
            "Missing required field: document_type" in error_msg
            or "document_type" in error_msg.lower()
        )
        assert len(result["documents"]) == 0

    def test_merge_with_missing_document_type(self):
        """Test merging documents when document_type is missing."""
        docs = [
            {"id": "MERGE-001", "name": "Page 1"},
            {"id": "MERGE-001", "name": "Page 2"},
        ]
        result = json_dict_to_ubl_xml(docs)
        assert result["error_response"] is not None
        error_msg = (
            result["error_response"].get("message", "")
            if isinstance(result["error_response"], dict)
            else str(result["error_response"])
        )
        assert "document_type" in error_msg.lower()
        assert len(result["documents"]) == 0

    def test_invalid_document_type_string(self, invalid_doctype_dict):
        """Test invalid document_type (string instead of numeric)."""
        result = json_dict_to_ubl_xml([invalid_doctype_dict])
        assert result["error_response"] is not None
        error_msg = (
            result["error_response"].get("message", "")
            if isinstance(result["error_response"], dict)
            else str(result["error_response"])
        )
        assert "Invalid document_type" in error_msg
        assert "Must be numeric code" in error_msg

    def test_invalid_document_type_numeric(self):
        """Test invalid numeric code."""
        doc = {
            "id": "TEST-001",
            "document_type": 999,
            "accountingCustomerParty": {"id": "C1", "name": "Customer"},
            "accountingSupplierParty": {"id": "S1", "name": "Supplier"},
        }
        result = json_dict_to_ubl_xml([doc])
        assert result["error_response"] is not None
        error_msg = (
            result["error_response"].get("message", "")
            if isinstance(result["error_response"], dict)
            else str(result["error_response"])
        )
        assert "Invalid document_type" in error_msg

    def test_null_document_type(self):
        """Test null document_type."""
        doc = {
            "id": "TEST-001",
            "document_type": None,
            "accountingCustomerParty": {"id": "C1", "name": "Customer"},
            "accountingSupplierParty": {"id": "S1", "name": "Supplier"},
        }
        result = json_dict_to_ubl_xml([doc])
        assert result["error_response"] is not None


class TestFileNotFound:
    """Test file handling."""

    def test_json_file_not_found(self):
        """Test file not found error."""
        result = json_file_to_ubl_xml_dict("/nonexistent/path/file.json")
        assert result["error_response"] is not None
        assert (
            "not found" in result["error_response"].lower()
            or "no such file" in result["error_response"].lower()
        )

    def test_json_file_to_files_not_found(self, tmp_path):
        """Test file not found for Method 3."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files("/nonexistent/path/file.json", output_dir)
        assert result["error_response"] is not None


class TestBatchProcessing:
    """Test batch processing scenarios."""

    def test_batch_multiple_invoices(self, test_files_dir):
        """Test processing batch file with multiple invoices."""
        result = json_file_to_ubl_xml_dict(str(test_files_dir / "batch_invoices.json"))
        assert result["error_response"] is None
        assert len(result["documents"]) == 2
        assert result["summary"]["total_inputs"] == 2
        ids = {doc["id"] for doc in result["documents"]}
        assert "BATCH-INV-001" in ids
        assert "BATCH-INV-002" in ids

    def test_batch_file_write_to_disk(self, test_files_dir, tmp_path):
        """Test batch file writing to disk."""
        output_dir = str(tmp_path / "batch_output")
        result = json_file_to_ubl_xml_files(str(test_files_dir / "batch_invoices.json"), output_dir)
        assert result["error_response"] is None
        assert result["summary"]["files_created"] == 2


class TestResponseStructure:
    """Test response structure compliance."""

    def test_success_response_has_error_response_field(self, invoice_dict):
        """Verify success response includes error_response=None."""
        result = json_dict_to_ubl_xml([invoice_dict])
        assert "error_response" in result
        assert result["error_response"] is None

    def test_error_response_has_error_response_field(self, missing_doctype_dict):
        """Verify error response includes populated error_response."""
        result = json_dict_to_ubl_xml([missing_doctype_dict])
        assert "error_response" in result
        assert result["error_response"] is not None
        assert isinstance(result["error_response"], dict)
        assert "error_code" in result["error_response"]
        assert "message" in result["error_response"]

    def test_response_has_documents_key(self, invoice_dict):
        """Verify response has documents key."""
        result = json_dict_to_ubl_xml([invoice_dict])
        assert "documents" in result
        assert isinstance(result["documents"], list)

    def test_response_has_summary_key(self, invoice_dict):
        """Verify response has summary key."""
        result = json_dict_to_ubl_xml([invoice_dict])
        assert "summary" in result
        assert "total_inputs" in result["summary"]
        assert "files_created" in result["summary"]
        assert "document_types" in result["summary"]

    def test_successful_document_has_required_fields(self, invoice_dict):
        """Verify successful document object has required fields."""
        result = json_dict_to_ubl_xml([invoice_dict])
        doc = result["documents"][0]
        assert "id" in doc
        assert "xml" in doc
        assert "unmapped_fields" in doc
        assert isinstance(doc["unmapped_fields"], list)

    def test_file_method_response_excludes_xml(self, test_files_dir, tmp_path):
        """Verify Method 3 response excludes xml field."""
        output_dir = str(tmp_path / "output")
        result = json_file_to_ubl_xml_files(str(test_files_dir / "invoice.json"), output_dir)
        doc = result["documents"][0]
        assert "id" in doc
        assert "xml" not in doc
        assert "unmapped_fields" in doc
