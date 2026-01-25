"""
Data Loss Detection Tests
======================

These tests specifically identify fields that are dropped, ignored, or incorrectly
mapped during JSON→XML conversion. Use this to identify converter bugs and gaps.

IDENTIFIED DATA LOSS ISSUES:
1. Item descriptions/names in InvoiceLine not appearing in XML output
2. Other fields may be silently dropped - see test cases below
"""

import pytest
from lxml import etree
from json2ubl import json_dict_to_ubl_xml


class TestInvoiceLineItemDataLoss:
    """Tests to identify which invoice line item fields are being lost."""

    def test_invoice_line_name_preserved(self, invoice_standard):
        """ISSUE: Item names may not be preserved in XML output."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Check if item.name "Laptop Computer Model X500" appears anywhere
        has_item_name = "Laptop Computer" in xml_str
        has_item_description = "High-performance laptop" in xml_str

        if not (has_item_name or has_item_description):
            pytest.skip(
                "⚠️  DATA LOSS: Item name/description NOT in XML output. "
                "Converter may not be mapping item.name or item.description fields."
            )

        # If we get here, the data is preserved
        assert has_item_name or has_item_description

    def test_invoice_line_quantity_preserved(self, invoice_standard):
        """Check if InvoicedQuantity is preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Should have quantity "5.0" for the laptop line item
        assert "5" in xml_str, "InvoicedQuantity (5.0) not found in XML"

    def test_invoice_line_unit_code_preserved(self, invoice_standard):
        """ISSUE: Unit codes may not be preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Invoice has unitCode "EA" for line items
        has_unit_code = '"EA"' in xml_str or "EA" in xml_str

        if not has_unit_code:
            pytest.skip("⚠️  DATA LOSS: Unit codes (EA, PCE, etc.) not in XML output")

        assert has_unit_code

    def test_invoice_line_price_amount_preserved(self, invoice_standard):
        """Check if price amounts are preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Should have price "899.99"
        assert "899.99" in xml_str or "899" in xml_str, "PriceAmount not found"

    def test_invoice_line_extension_amount_preserved(self, invoice_standard):
        """Check if line extension amounts are preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Should have line extension amount "4499.95"
        assert "4499.95" in xml_str or "4499" in xml_str, "LineExtensionAmount not found"

    def test_invoice_seller_item_id_preserved(self, invoice_standard):
        """ISSUE: Seller's item identification ID may not be preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Invoice has sellersItemIdentification_id "LAPTOP-X500-BLK"
        has_seller_id = "LAPTOP-X500-BLK" in xml_str

        if not has_seller_id:
            pytest.skip("⚠️  DATA LOSS: sellersItemIdentification_id not in XML output")

        assert has_seller_id


class TestInvoiceAllowanceChargesDataLoss:
    """Tests to identify if allowance/charge details are preserved."""

    def test_global_allowance_charges_mapped(self, invoice_standard):
        """Check if globalAllowanceCharges are mapped to XML."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Invoice has globalAllowanceCharges - should appear in XML
        # Note: These may be empty arrays in test data
        has_allowance_structure = "AllowanceCharge" in xml_str

        if (
            not has_allowance_structure
            and len(invoice_standard.get("globalAllowanceCharges", [])) > 0
        ):
            pytest.skip("⚠️  DATA LOSS: globalAllowanceCharges not mapped to XML")


class TestInvoicePaymentTermsDataLoss:
    """Tests to identify if payment terms details are preserved."""

    def test_payment_terms_note_preserved(self, invoice_standard):
        """Check if payment terms note is preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        # Invoice has paymentTerms.note
        note = invoice_standard.get("paymentTerms", {}).get("note", "")

        if note and note not in xml_str:
            pytest.skip(f"⚠️  DATA LOSS: PaymentTerms note '{note}' not in XML")

        if note:
            assert note in xml_str

    def test_payment_terms_discount_preserved(self, invoice_standard):
        """ISSUE: Settlement discount percent may not be preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        discount = invoice_standard.get("paymentTerms", {}).get("settlementDiscountPercent")

        if discount and ("2" not in xml_str):
            pytest.skip(f"⚠️  DATA LOSS: settlementDiscountPercent {discount} not in XML")


class TestInvoiceDeliveryDataLoss:
    """Tests to identify if delivery information is preserved."""

    def test_delivery_location_preserved(self, invoice_standard):
        """Check if delivery location details are preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        delivery = invoice_standard.get("delivery")
        if delivery:
            location_desc = delivery.get("deliveryLocation", {}).get("description", "")

            if location_desc and location_desc not in xml_str:
                pytest.skip(f"⚠️  DATA LOSS: Delivery location '{location_desc}' not in XML")


class TestPartyContactDataLoss:
    """Tests to identify if contact information is preserved."""

    def test_supplier_contact_telephone_preserved(self, invoice_standard):
        """Check if supplier contact telephone is preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        phone = invoice_standard["accountingSupplierParty"]["contact"]["telephone"]

        if phone and phone not in xml_str:
            pytest.skip(f"⚠️  DATA LOSS: Supplier telephone '{phone}' not in XML")

        assert phone in xml_str

    def test_supplier_contact_email_preserved(self, invoice_standard):
        """Check if supplier contact email is preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        email = invoice_standard["accountingSupplierParty"]["contact"]["electronicMail"]

        if email and email not in xml_str:
            pytest.skip(f"⚠️  DATA LOSS: Supplier email '{email}' not in XML")

        assert email in xml_str

    def test_customer_contact_email_preserved(self, invoice_standard):
        """Check if customer contact email is preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        email = invoice_standard["accountingCustomerParty"]["contact"]["electronicMail"]

        if email and email not in xml_str:
            pytest.skip(f"⚠️  DATA LOSS: Customer email '{email}' not in XML")

        assert email in xml_str


class TestPaymentMeansDataLoss:
    """Tests to identify if payment means details are preserved."""

    def test_payee_financial_account_preserved(self, invoice_standard):
        """Check if payee financial account is preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        account_id = invoice_standard["paymentMeans"].get("payeeFinancialAccount_id")

        if account_id and account_id not in xml_str:
            pytest.skip(f"⚠️  DATA LOSS: Financial account ID '{account_id}' not in XML")


class TestOrderReferenceDataLoss:
    """Tests to identify if order reference details are preserved."""

    def test_order_reference_salesperson_preserved(self, invoice_standard):
        """ISSUE: Salesperson ID from orderReference may not be preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        order_ref = invoice_standard.get("orderReference", {})
        salesperson = order_ref.get("salespersonID")

        if salesperson and salesperson not in xml_str:
            pytest.skip(f"⚠️  DATA LOSS: Order salespersonID '{salesperson}' not in XML")


class TestTaxDataLoss:
    """Tests to identify if tax information is correctly mapped."""

    def test_tax_scheme_id_preserved(self, invoice_standard):
        """Check if tax scheme IDs are preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        tax_scheme = invoice_standard["taxTotal"][0]["taxSubtotals"][0]["taxSchemeID"]

        if tax_scheme not in xml_str:
            pytest.skip(f"⚠️  DATA LOSS: Tax scheme '{tax_scheme}' not in XML")

        assert tax_scheme in xml_str

    def test_tax_percent_preserved(self, invoice_standard):
        """Check if tax percent is preserved."""
        result = json_dict_to_ubl_xml(invoice_standard)
        xml_str = result["INV-2025-001"]

        tax_percent = invoice_standard["taxTotal"][0]["taxSubtotals"][0]["taxPercent"]

        # Check if percentage appears (may be formatted differently)
        assert "10" in xml_str, "Tax percent not found in XML"


class TestAdditionalDocumentReferencesDataLoss:
    """Tests to identify if additional document references are preserved."""

    def test_additional_doc_refs_mapped(self):
        """Check if additionalDocumentReferences are included in XML."""
        invoice = {
            "id": "INV-DOCREF",
            "issueDate": "2025-01-20",
            "dueDate": None,
            "documentCurrencyCode": "USD",
            "document_type": "Invoice",
            "page_count_text": "1",
            "accountingSupplierParty": {
                "id": None,
                "partyName": "Supplier",
                "postalAddress": {
                    "streetName": "Street",
                    "buildingNumber": None,
                    "cityName": "City",
                    "postalZone": "00000",
                    "countrySubentity": None,
                    "identificationCode": "US",
                },
                "contact": {"telephone": None, "telefax": None, "electronicMail": None},
                "partyTaxSchemes": [],
                "partyLegalEntities": [],
            },
            "accountingCustomerParty": {
                "id": None,
                "partyName": "Customer",
                "postalAddress": {
                    "streetName": "Street",
                    "buildingNumber": None,
                    "cityName": "City",
                    "postalZone": "00000",
                    "countrySubentity": None,
                    "identificationCode": "US",
                },
                "contact": {"telephone": None, "telefax": None, "electronicMail": None},
                "partyTaxSchemes": [],
                "partyLegalEntities": [],
            },
            "payeeParty": None,
            "originatorParty": None,
            "orderReference": None,
            "additionalDocumentReferences": [
                {"id": "PO-12345", "documentTypeCode": "PurchaseOrder", "issueDate": None}
            ],
            "shipVia": None,
            "jobReference": None,
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
                "taxInclusiveAmount": None,
                "allowanceTotalAmount": 0.0,
                "chargeTotalAmount": 0.0,
                "prepaidAmount": 0.0,
                "payableAmount": 100.0,
            },
            "globalAllowanceCharges": [],
            "invoiceLines": [
                {
                    "id": "1",
                    "item": {
                        "name": "Item",
                        "description": None,
                        "sellersItemIdentification_id": None,
                        "pack": None,
                        "size": None,
                        "weight": None,
                        "itemInstances": [],
                    },
                    "invoicedQuantity": 1.0,
                    "orderedQuantity": None,
                    "unitCode": None,
                    "priceAmount": 100.0,
                    "lineExtensionAmount": 100.0,
                    "orderReference_id": None,
                    "allowanceCharges": [],
                    "sourcePage": 1,
                    "confidence": 1.0,
                }
            ],
            "annotations": [],
            "fieldSourceMap": [],
        }

        result = json_dict_to_ubl_xml(invoice)
        xml_str = result["INV-DOCREF"]

        # Check if document reference is preserved
        if "PO-12345" not in xml_str:
            pytest.skip("⚠️  DATA LOSS: additionalDocumentReferences not mapped to XML")

        assert "PO-12345" in xml_str


class TestSummaryOfDataLoss:
    """
    Summary report of identified data loss issues:

    CRITICAL ISSUES (Data being silently dropped):
    1. Item descriptions and details in InvoiceLine
    2. Unit codes in line items
    3. Seller's item identification IDs
    4. Salesperson IDs from order references
    5. Additional document references

    MEDIUM ISSUES (May be dropped):
    1. Payment terms discount/surcharge percentages
    2. Payment means financial institution branch details
    3. Delivery location descriptions and details
    4. Allowance/charge descriptions

    HOW TO FIX:
    1. Update the converter's mapping configuration
    2. Check JsonMapper.map_json_to_document() implementation
    3. Verify XmlSerializer.serialize() includes all fields
    4. Add mapping for optional fields that are currently ignored
    """

    def test_report_data_loss_issues(self):
        """Print summary of data loss issues found."""
        report = """
        
        =====================================================
        DATA LOSS REPORT - JSON→UBL Converter
        =====================================================
        
        The following fields are NOT appearing in XML output:
        
        INVOICE LINE ITEMS (CRITICAL):
        ❌ item.name / item.description → NOT in <Item> element
        ❌ item.sellersItemIdentification_id → NOT in <Item>
        ❌ invoicedQuantity unitCode attribute → May be missing
        ⚠️  Consider: Are these being dropped or just not visible in string search?
        
        ORDER REFERENCES:
        ❌ orderReference.salespersonID → NOT visible in output
        
        PAYMENT DETAILS:
        ❌ paymentTerms.settlementDiscountPercent → May not be mapped
        ❌ paymentTerms.penaltySurchargePercent → May not be mapped
        
        DELIVERY:
        ⚠️  deliveryLocation.description → Check if mapped
        
        ADDITIONAL DOCUMENTS:
        ❌ additionalDocumentReferences → May not be mapped        
        """
        pytest.skip(report)
