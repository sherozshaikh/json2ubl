import json

from lxml import etree

from json2ubl import json_dict_to_ubl_xml, json_file_to_ubl_xml_dict, json_file_to_ubl_xml_files


class TestE2EConversion:
    """End-to-end tests using real LLM-generated JSON from test1.json and test2.json."""

    def test_convert_test1_invoice_tax_invoice(self, invoice_from_test1):
        """Test converting a TAX INVOICE (Australian format)."""
        result = json_dict_to_ubl_xml(invoice_from_test1)

        assert isinstance(result, dict)
        assert "728205" in result
        assert isinstance(result["728205"], str)
        assert "Invoice" in result["728205"]
        assert "<?xml" in result["728205"]

    def test_convert_test2_invoice_us(self, invoice_from_test2):
        """Test converting a US Invoice."""
        result = json_dict_to_ubl_xml(invoice_from_test2)

        assert isinstance(result, dict)
        assert "S4925701.001" in result
        assert isinstance(result["S4925701.001"], str)
        assert "Invoice" in result["S4925701.001"]

    def test_test1_invoice_xml_is_parseable(self, invoice_from_test1):
        """Test that converted XML is valid and parseable."""
        result = json_dict_to_ubl_xml(invoice_from_test1)
        xml_str = result["728205"]

        root = etree.fromstring(xml_str.encode("utf-8"))
        assert root is not None
        assert "Invoice" in root.tag

    def test_test2_invoice_xml_is_parseable(self, invoice_from_test2):
        """Test that converted US Invoice is valid and parseable."""
        result = json_dict_to_ubl_xml(invoice_from_test2)
        xml_str = result["S4925701.001"]

        root = etree.fromstring(xml_str.encode("utf-8"))
        assert root is not None
        assert "Invoice" in root.tag

    def test_file_to_dict_with_test1_structure(self, tmp_path):
        """Test converting JSON file with test1 structure to XML dict."""
        # Create a JSON file with test1-like structure
        invoices = [
            {
                "id": "INV-TEST-001",
                "issueDate": "2025-01-20",
                "documentCurrencyCode": "AUD",
                "document_type": "TAX INVOICE",
                "accountingSupplierParty": {
                    "partyName": "Test Supplier",
                    "postalAddress": {
                        "streetName": "123 Test St",
                        "cityName": "Test City",
                        "postalZone": "3000",
                        "identificationCode": "AU",
                    },
                    "contact": {
                        "telephone": "+61 1234 5678",
                        "telefax": None,
                        "electronicMail": None,
                    },
                    "partyTaxSchemes": [{"companyID": "12345678901", "taxSchemeID": "GST"}],
                    "partyLegalEntities": [],
                },
                "accountingCustomerParty": {
                    "partyName": "Test Customer",
                    "postalAddress": {
                        "streetName": "456 Customer Ave",
                        "cityName": "Another City",
                        "postalZone": "3100",
                        "identificationCode": "AU",
                    },
                    "contact": {"telephone": None, "telefax": None, "electronicMail": None},
                    "partyTaxSchemes": [],
                    "partyLegalEntities": [],
                },
                "payeeParty": None,
                "originatorParty": None,
                "orderReference": None,
                "delivery": None,
                "paymentMeans": {
                    "paymentMeansCode": "30",
                    "payeeFinancialAccount_id": None,
                    "financialInstitutionBranch": None,
                    "remit_to_email": None,
                },
                "paymentTerms": None,
                "taxTotal": [],
                "legalMonetaryTotal": {
                    "lineExtensionAmount": 100.0,
                    "taxExclusiveAmount": 100.0,
                    "taxInclusiveAmount": 110.0,
                    "allowanceTotalAmount": 0.0,
                    "chargeTotalAmount": 0.0,
                    "prepaidAmount": 0.0,
                    "payableAmount": 110.0,
                },
                "globalAllowanceCharges": [],
                "invoiceLines": [
                    {
                        "id": "1",
                        "item": {
                            "name": "Test Item",
                            "description": None,
                            "sellersItemIdentification_id": None,
                            "itemInstances": [],
                        },
                        "invoicedQuantity": 1.0,
                        "unitCode": None,
                        "priceAmount": 100.0,
                        "lineExtensionAmount": 100.0,
                        "allowanceCharges": [],
                    }
                ],
            }
        ]

        json_file = tmp_path / "test_invoices.json"
        with open(json_file, "w") as f:
            json.dump(invoices, f)

        result = json_file_to_ubl_xml_dict(str(json_file))

        assert isinstance(result, dict)
        assert "INV-TEST-001" in result
        assert isinstance(result["INV-TEST-001"], str)

    def test_file_to_files_creates_xml_files(self, tmp_path, invoice_from_test1):
        """Test Method 3 creates actual XML files on disk."""
        invoices = [invoice_from_test1]

        json_file = tmp_path / "invoices.json"
        with open(json_file, "w") as f:
            json.dump(invoices, f)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = json_file_to_ubl_xml_files(str(json_file), str(output_dir))

        assert result["total_invoices"] >= 1
        assert result["files_created"] >= 1
        assert result["json_file"] == str(json_file)
        assert result["output_dir"] == str(output_dir)

        # Check files were created
        output_files = list(output_dir.glob("*.xml"))
        assert len(output_files) == result["files_created"]

    def test_multiple_invoices_from_file(self, tmp_path, invoice_from_test1, invoice_from_test2):
        """Test converting multiple invoices from a single JSON file."""
        invoices = [invoice_from_test1, invoice_from_test2]

        json_file = tmp_path / "multi_invoices.json"
        with open(json_file, "w") as f:
            json.dump(invoices, f)

        result = json_file_to_ubl_xml_dict(str(json_file))

        assert len(result) == 2
        assert "728205" in result
        assert "S4925701.001" in result

    def test_xml_contains_supplier_party(self, invoice_from_test1):
        """Test that XML contains supplier party information."""
        result = json_dict_to_ubl_xml(invoice_from_test1)
        xml_str = result["728205"]

        root = etree.fromstring(xml_str.encode("utf-8"))
        ns = {"cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"}

        supplier = root.find(".//cac:AccountingSupplierParty", ns)
        assert supplier is not None

    def test_xml_contains_invoice_lines(self, invoice_from_test1):
        """Test that XML contains invoice line items."""
        result = json_dict_to_ubl_xml(invoice_from_test1)
        xml_str = result["728205"]

        root = etree.fromstring(xml_str.encode("utf-8"))
        ns = {"cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"}

        lines = root.findall(".//cac:InvoiceLine", ns)
        assert len(lines) == 2  # test1 has 2 invoice lines

    def test_xml_contains_monetary_totals(self, invoice_from_test1):
        """Test that XML contains legal monetary total."""
        result = json_dict_to_ubl_xml(invoice_from_test1)
        xml_str = result["728205"]

        root = etree.fromstring(xml_str.encode("utf-8"))
        ns = {"cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"}

        monetary_total = root.find(".//cac:LegalMonetaryTotal", ns)
        assert monetary_total is not None

    def test_handles_null_contact_fields(self, invoice_from_test2):
        """Test that conversion handles null contact fields gracefully."""
        result = json_dict_to_ubl_xml(invoice_from_test2)
        assert "S4925701.001" in result
        assert result["S4925701.001"] is not None

    def test_handles_null_payee_party(self, invoice_from_test1):
        """Test that conversion handles null payeeParty."""
        # invoice_from_test1 has null payeeParty
        result = json_dict_to_ubl_xml(invoice_from_test1)
        assert "728205" in result
        assert result["728205"] is not None

    def test_handles_null_originator_party(self, invoice_from_test1):
        """Test that conversion handles null originatorParty."""
        # invoice_from_test1 has null originatorParty
        result = json_dict_to_ubl_xml(invoice_from_test1)
        assert "728205" in result
        assert result["728205"] is not None
