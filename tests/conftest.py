import json
import pytest
from pathlib import Path


@pytest.fixture
def invoice_from_test1():
    """Real invoice from test1.json (TAX INVOICE type, Australian)."""
    return {
        "id": "728205",
        "issueDate": "2025-05-01",
        "dueDate": None,
        "documentCurrencyCode": "AUD",
        "document_type": "TAX INVOICE",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": None,
            "partyName": "QUEST CARPETS",
            "postalAddress": {
                "streetName": "43-45 Mark Anthony Drive",
                "cityName": "Dandenong South",
                "postalZone": "3175",
                "countrySubentity": "VIC",
                "identificationCode": "AU",
            },
            "contact": {
                "telephone": "+613 8791 8200",
                "telefax": "+613 8791 8299",
                "electronicMail": None,
            },
            "partyTaxSchemes": [{"companyID": "61 606 397 273", "taxSchemeID": "GST"}],
            "partyLegalEntities": [
                {"registrationName": "Quest Flooring Pty Ltd", "companyID": "61 606 397 273"}
            ],
        },
        "accountingCustomerParty": {
            "id": "34201",
            "partyName": "FLOORWORLD PTY. LTD. (DOMESTIC)",
            "postalAddress": {
                "streetName": "TENANCY 4/LEVEL 2, 2/331-333 POLICE ROAD",
                "cityName": "MULGRAVE",
                "postalZone": "3170",
                "countrySubentity": "VIC",
                "identificationCode": "AU",
            },
            "contact": {"telephone": None, "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [{"companyID": "20051233964", "taxSchemeID": "ABN"}],
            "partyLegalEntities": [
                {"registrationName": "FLOORWORLD PTY. LTD. (DOMESTIC)", "companyID": "20051233964"}
            ],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": {
            "id": "RW10623",
            "salespersonID": "AT",
            "SalesOrderID": "742012",
            "customerReference": "34201",
            "issueDate": None,
        },
        "delivery": {
            "actualDeliveryDate": None,
            "deliveryLocation": {
                "id": None,
                "description": "SMITH'S FLOORWORLD",
                "address": {
                    "streetName": "92 PARKHURST DRIVE",
                    "buildingNumber": "92",
                    "cityName": "KNOXFIELD",
                    "postalZone": "3180",
                    "countrySubentity": "VIC",
                    "identificationCode": "AU",
                },
            },
        },
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": "11194380",
            "financialInstitutionBranch": {"id": "063 125", "name": None, "branchName": None},
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "STRICTLY NETT 30 DAYS TRADING",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [
            {
                "taxAmount": 194.43,
                "taxSubtotals": [
                    {
                        "taxableAmount": 1944.29,
                        "taxAmount": 194.43,
                        "taxPercent": 10.0,
                        "taxSchemeID": "GST",
                    }
                ],
            }
        ],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 1944.29,
            "taxExclusiveAmount": 1944.29,
            "taxInclusiveAmount": 2138.72,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 2138.72,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "CALIFORNIA DREAMS",
                    "description": "CALIFORNIA DREAMS CROMPTON",
                    "sellersItemIdentification_id": "10/2406A",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 21.2,
                "orderedQuantity": None,
                "unitCode": None,
                "priceAmount": 91.24,
                "lineExtensionAmount": 1934.29,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 1.0,
            },
            {
                "id": "2",
                "item": {
                    "name": "PACKING & HANDLING",
                    "description": "PACKING & HANDLING PER INVOICE",
                    "sellersItemIdentification_id": None,
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 1.0,
                "orderedQuantity": None,
                "unitCode": None,
                "priceAmount": 10.0,
                "lineExtensionAmount": 10.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 1.0,
            },
        ],
        "annotations": [],
        "fieldSourceMap": [
            {"field": "id", "page": 1},
            {"field": "issueDate", "page": 1},
            {"field": "legalMonetaryTotal.payableAmount", "page": 1},
        ],
    }


@pytest.fixture
def invoice_from_test2():
    """Real invoice from test2.json (Invoice type, US)."""
    return {
        "id": "S4925701.001",
        "issueDate": "2024-04-29",
        "dueDate": "2024-04-29",
        "documentCurrencyCode": "USD",
        "document_type": "Invoice",
        "page_count_text": "1 of 2",
        "accountingSupplierParty": {
            "id": "BR42",
            "partyName": "NATIONAL WHOLESALE SUPPLY BR42",
            "postalAddress": {
                "streetName": "VANDER WILT LANE",
                "buildingNumber": "1406",
                "cityName": "KATY",
                "postalZone": "77449",
                "countrySubentity": "TX",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "281-886-8353",
                "telefax": "281-786-3943",
                "electronicMail": None,
            },
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "45041",
            "partyName": "KAE EDWARD-CASH ACCT",
            "postalAddress": {
                "streetName": "SW FREEWAY",
                "buildingNumber": "14090",
                "additionalStreetName": "STE 300",
                "cityName": "SUGAR LAND",
                "postalZone": "77478",
                "countrySubentity": "TX",
                "identificationCode": "US",
            },
            "contact": {"telephone": None, "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [
                {"registrationName": "DBA KAE EDWARD PLBG LLC", "companyID": None}
            ],
        },
        "payeeParty": {
            "partyName": "NATIONAL WHOLESALE SUPPLY, Inc.",
            "postalAddress": {
                "streetName": "PO BOX 540007",
                "cityName": "DALLAS",
                "postalZone": "75354",
                "countrySubentity": "TX",
                "identificationCode": "US",
            },
            "contact": None,
        },
        "originatorParty": {"partyName": "EDWARD CASTRO", "postalAddress": None, "contact": None},
        "orderReference": {
            "id": "J4009",
            "salespersonID": "HOUSE",
            "SalesOrderID": None,
            "customerReference": "BRYLY",
            "issueDate": "2024-04-29",
        },
        "additionalDocumentReferences": [],
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
            "lineExtensionAmount": 1250.0,
            "taxExclusiveAmount": 1250.0,
            "taxInclusiveAmount": 1250.0,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 1250.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "ITEM 1",
                    "description": None,
                    "sellersItemIdentification_id": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 1.0,
                "orderedQuantity": None,
                "unitCode": None,
                "priceAmount": 1250.0,
                "lineExtensionAmount": 1250.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 1.0,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [],
    }


@pytest.fixture
def temp_json_file(tmp_path, invoice_from_test1):
    """Create temporary JSON file with test data."""
    file_path = tmp_path / "test.json"
    with open(file_path, "w") as f:
        json.dump([invoice_from_test1], f)
    return str(file_path)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


# ==================== New Document Type Fixtures ====================


@pytest.fixture
def invoice_standard():
    """Standard Invoice with full details."""
    return {
        "id": "INV-2025-001",
        "issueDate": "2025-01-20",
        "dueDate": "2025-02-20",
        "documentCurrencyCode": "USD",
        "document_type": "Invoice",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "SUP001",
            "partyName": "Global Electronics Inc",
            "postalAddress": {
                "streetName": "456 Industrial Blvd",
                "buildingNumber": "456",
                "cityName": "San Francisco",
                "postalZone": "94105",
                "countrySubentity": "CA",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-415-555-0123",
                "telefax": "+1-415-555-0124",
                "electronicMail": "sales@globalelectronics.com",
            },
            "partyTaxSchemes": [{"companyID": "98-7654321", "taxSchemeID": "FED"}],
            "partyLegalEntities": [
                {"registrationName": "Global Electronics Inc.", "companyID": "98-7654321"}
            ],
        },
        "accountingCustomerParty": {
            "id": "CUST001",
            "partyName": "Tech Retail Corp",
            "postalAddress": {
                "streetName": "789 Market Street",
                "buildingNumber": "789",
                "additionalStreetName": "Suite 500",
                "cityName": "New York",
                "postalZone": "10001",
                "countrySubentity": "NY",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-212-555-9876",
                "telefax": None,
                "electronicMail": "procurement@techretail.com",
            },
            "partyTaxSchemes": [{"companyID": "12-3456789", "taxSchemeID": "FED"}],
            "partyLegalEntities": [
                {"registrationName": "Tech Retail Corporation", "companyID": "12-3456789"}
            ],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": {
            "id": "PO-2025-1001",
            "salespersonID": "JOHN_DOE",
            "SalesOrderID": "SO-2025-1001",
            "customerReference": "CUST001",
            "issueDate": "2025-01-15",
        },
        "additionalDocumentReferences": [],
        "shipVia": "FedEx Ground",
        "jobReference": None,
        "delivery": {
            "actualDeliveryDate": None,
            "actualDeliveryTime": None,
            "deliveryLocation": {
                "id": "SHIP001",
                "description": "Main Distribution Center",
                "address": {
                    "streetName": "123 Logistics Way",
                    "buildingNumber": "123",
                    "cityName": "Newark",
                    "postalZone": "07102",
                    "countrySubentity": "NJ",
                    "identificationCode": "US",
                },
            },
            "deliveryParty": {
                "partyName": "Tech Retail Corp",
                "contact": {"name": "Jane Smith", "telephone": "+1-212-555-9876"},
            },
            "sourcePage": 1,
        },
        "paymentMeans": {
            "paymentMeansCode": "42",
            "payeeFinancialAccount_id": "4000123456789012",
            "financialInstitutionBranch": {
                "id": "BOFA0001",
                "name": "Bank of America",
                "branchName": "San Francisco Main",
            },
            "remit_to_email": "accounts@globalelectronics.com",
        },
        "paymentTerms": {
            "note": "Net 30 days from invoice date",
            "settlementDiscountPercent": 2.0,
            "penaltySurchargePercent": 1.5,
        },
        "taxTotal": [
            {
                "taxAmount": 125.50,
                "taxSubtotals": [
                    {
                        "taxableAmount": 1255.0,
                        "taxAmount": 125.50,
                        "taxPercent": 10.0,
                        "taxSchemeID": "VAT",
                    }
                ],
            }
        ],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 1255.0,
            "taxExclusiveAmount": 1255.0,
            "taxInclusiveAmount": 1380.50,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 1380.50,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "Laptop Computer Model X500",
                    "description": "High-performance laptop with 16GB RAM and 512GB SSD",
                    "sellersItemIdentification_id": "LAPTOP-X500-BLK",
                    "pack": "Unit",
                    "size": "15.6 inch",
                    "weight": "2.1 kg",
                    "itemInstances": [],
                },
                "invoicedQuantity": 5.0,
                "orderedQuantity": 5.0,
                "unitCode": "EA",
                "priceAmount": 899.99,
                "lineExtensionAmount": 4499.95,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.99,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [{"field": "id", "page": 1}],
    }


@pytest.fixture
def credit_note_standard():
    """Standard CreditNote with negative amounts."""
    return {
        "id": "CN-2025-001",
        "issueDate": "2025-01-22",
        "dueDate": "2025-02-22",
        "documentCurrencyCode": "USD",
        "document_type": "CreditNote",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "SUP002",
            "partyName": "Tech Solutions Ltd",
            "postalAddress": {
                "streetName": "999 Innovation Drive",
                "buildingNumber": "999",
                "cityName": "Boston",
                "postalZone": "02101",
                "countrySubentity": "MA",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-617-555-1234",
                "telefax": None,
                "electronicMail": "support@techsolutions.com",
            },
            "partyTaxSchemes": [{"companyID": "12-3456789", "taxSchemeID": "FED"}],
            "partyLegalEntities": [
                {"registrationName": "Tech Solutions Ltd.", "companyID": "12-3456789"}
            ],
        },
        "accountingCustomerParty": {
            "id": "CUST002",
            "partyName": "Enterprise Systems Inc",
            "postalAddress": {
                "streetName": "200 Corporate Plaza",
                "buildingNumber": "200",
                "cityName": "Dallas",
                "postalZone": "75201",
                "countrySubentity": "TX",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-214-555-4321",
                "telefax": None,
                "electronicMail": "accounts@enterprisesys.com",
            },
            "partyTaxSchemes": [{"companyID": "45-6789012", "taxSchemeID": "FED"}],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": None,
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": None,
        "paymentMeans": {
            "paymentMeansCode": "42",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Credit to original invoice Net 30",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [
            {
                "taxAmount": -100.0,
                "taxSubtotals": [
                    {
                        "taxableAmount": -1000.0,
                        "taxAmount": -100.0,
                        "taxPercent": 10.0,
                        "taxSchemeID": "VAT",
                    }
                ],
            }
        ],
        "legalMonetaryTotal": {
            "lineExtensionAmount": -1000.0,
            "taxExclusiveAmount": -1000.0,
            "taxInclusiveAmount": -1100.0,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": -1100.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "Software License Refund",
                    "description": "Annual software license return",
                    "sellersItemIdentification_id": "LIC-SOFT-2024",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": -1.0,
                "orderedQuantity": None,
                "unitCode": "EA",
                "priceAmount": 1000.0,
                "lineExtensionAmount": -1000.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.99,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [{"field": "id", "page": 1}],
    }


@pytest.fixture
def debit_note_standard():
    """Standard DebitNote with charges."""
    return {
        "id": "DN-2025-001",
        "issueDate": "2025-01-23",
        "dueDate": "2025-02-23",
        "documentCurrencyCode": "GBP",
        "document_type": "DebitNote",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "SUP003",
            "partyName": "London Trading Co",
            "postalAddress": {
                "streetName": "Piccadilly Street",
                "buildingNumber": "123",
                "cityName": "London",
                "postalZone": "W1D 7AD",
                "countrySubentity": None,
                "identificationCode": "GB",
            },
            "contact": {
                "telephone": "+44-20-7946-0958",
                "telefax": None,
                "electronicMail": "sales@londontrading.co.uk",
            },
            "partyTaxSchemes": [{"companyID": "GB123456789", "taxSchemeID": "VAT"}],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "CUST003",
            "partyName": "Manchester Retail Ltd",
            "postalAddress": {
                "streetName": "Deansgate",
                "buildingNumber": "456",
                "cityName": "Manchester",
                "postalZone": "M1 7AB",
                "countrySubentity": None,
                "identificationCode": "GB",
            },
            "contact": {"telephone": "+44-161-228-1234", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [{"companyID": "GB987654321", "taxSchemeID": "VAT"}],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": None,
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": None,
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Additional charge due to late delivery",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": 2.5,
        },
        "taxTotal": [
            {
                "taxAmount": 75.0,
                "taxSubtotals": [
                    {
                        "taxableAmount": 500.0,
                        "taxAmount": 75.0,
                        "taxPercent": 15.0,
                        "taxSchemeID": "VAT",
                    }
                ],
            }
        ],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 500.0,
            "taxExclusiveAmount": 500.0,
            "taxInclusiveAmount": 575.0,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 500.0,
            "prepaidAmount": 0.0,
            "payableAmount": 575.0,
        },
        "globalAllowanceCharges": [
            {
                "chargeIndicator": True,
                "allowanceReasonCode": "LATE",
                "amount": 500.0,
                "description": "Late delivery penalty charge",
            }
        ],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "Late Delivery Charge",
                    "description": "Penalty for delivery beyond agreed date",
                    "sellersItemIdentification_id": "CHARGE-LATE",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 1.0,
                "orderedQuantity": None,
                "unitCode": "EA",
                "priceAmount": 500.0,
                "lineExtensionAmount": 500.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.95,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [{"field": "id", "page": 1}],
    }


@pytest.fixture
def freight_invoice_standard():
    """Standard FreightInvoice with logistics details."""
    return {
        "id": "FRI-2025-001",
        "issueDate": "2025-01-24",
        "dueDate": "2025-02-24",
        "documentCurrencyCode": "USD",
        "document_type": "FreightInvoice",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "LOGISTICS001",
            "partyName": "Global Freight Services",
            "postalAddress": {
                "streetName": "5000 Logistics Parkway",
                "buildingNumber": "5000",
                "cityName": "Atlanta",
                "postalZone": "30303",
                "countrySubentity": "GA",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-404-555-5555",
                "telefax": None,
                "electronicMail": "freight@globalfreight.com",
            },
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "SHIPPER001",
            "partyName": "Premium Manufacturing Co",
            "postalAddress": {
                "streetName": "7777 Industrial Complex",
                "buildingNumber": "7777",
                "cityName": "Chicago",
                "postalZone": "60601",
                "countrySubentity": "IL",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-312-555-6666",
                "telefax": None,
                "electronicMail": "shipping@premiummanuf.com",
            },
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": None,
        "additionalDocumentReferences": [],
        "shipVia": "Truck - Interstate",
        "jobReference": None,
        "delivery": {
            "actualDeliveryDate": "2025-01-23",
            "actualDeliveryTime": None,
            "deliveryLocation": {
                "id": "DC-HOUSTON",
                "description": "Houston Distribution Center",
                "address": {
                    "streetName": "2000 Port Authority Drive",
                    "buildingNumber": "2000",
                    "cityName": "Houston",
                    "postalZone": "77002",
                    "countrySubentity": "TX",
                    "identificationCode": "US",
                },
            },
            "deliveryParty": {
                "partyName": "Houston Receiving",
                "contact": {"name": "Robert Wilson", "telephone": "+1-713-555-7777"},
            },
            "sourcePage": 1,
        },
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Net 15 days from delivery",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 1875.0,
            "taxExclusiveAmount": 1875.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 1875.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "LTL Freight Service",
                    "description": "Less Than Truckload freight service",
                    "sellersItemIdentification_id": "LTL-2025",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 1.0,
                "orderedQuantity": 1.0,
                "unitCode": "SHIPMENT",
                "priceAmount": 1875.0,
                "lineExtensionAmount": 1875.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.99,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [{"field": "id", "page": 1}],
    }


@pytest.fixture
def self_billed_invoice_standard():
    """Standard SelfBilledInvoice issued by buyer."""
    return {
        "id": "SBI-2025-001",
        "issueDate": "2025-01-25",
        "dueDate": "2025-02-25",
        "documentCurrencyCode": "EUR",
        "document_type": "SelfBilledInvoice",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "BUYER001",
            "partyName": "Large Retail Chain EU",
            "postalAddress": {
                "streetName": "Grand Avenue 999",
                "buildingNumber": "999",
                "cityName": "Amsterdam",
                "postalZone": "1012 KK",
                "countrySubentity": None,
                "identificationCode": "NL",
            },
            "contact": {
                "telephone": "+31-20-1234567",
                "telefax": None,
                "electronicMail": "billing@largechaineu.com",
            },
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "SUPPLIER-SBI",
            "partyName": "Fashion Supplier GmbH",
            "postalAddress": {
                "streetName": "Frankfurter Allee",
                "buildingNumber": "100",
                "cityName": "Berlin",
                "postalZone": "10369",
                "countrySubentity": None,
                "identificationCode": "DE",
            },
            "contact": {"telephone": "+49-30-555-1234", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": None,
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": None,
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Self-billed invoice terms",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 5000.0,
            "taxExclusiveAmount": 5000.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 5000.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "Fashion Collection",
                    "description": "Winter clothing collection",
                    "sellersItemIdentification_id": "COLL-WINTER",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 500.0,
                "orderedQuantity": 500.0,
                "unitCode": "PCE",
                "priceAmount": 10.0,
                "lineExtensionAmount": 5000.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.98,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [{"field": "id", "page": 1}],
    }


@pytest.fixture
def self_billed_credit_note_standard():
    """Standard SelfBilledCreditNote issued by buyer."""
    return {
        "id": "SBCN-2025-001",
        "issueDate": "2025-01-26",
        "dueDate": "2025-02-26",
        "documentCurrencyCode": "EUR",
        "document_type": "SelfBilledCreditNote",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "BUYER-CN",
            "partyName": "Industrial Buyer Corp",
            "postalAddress": {
                "streetName": "Industrial Zone",
                "buildingNumber": "200",
                "cityName": "Stuttgart",
                "postalZone": "70563",
                "countrySubentity": None,
                "identificationCode": "DE",
            },
            "contact": {
                "telephone": "+49-711-555-1234",
                "telefax": None,
                "electronicMail": "credit@industrialbuyer.de",
            },
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "SUPPLIER-SBCN",
            "partyName": "Components Manufacturing Ltd",
            "postalAddress": {
                "streetName": "Factory Road",
                "buildingNumber": "350",
                "cityName": "Prague",
                "postalZone": "13000",
                "countrySubentity": None,
                "identificationCode": "CZ",
            },
            "contact": {"telephone": "+420-2-555-1234", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": None,
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": None,
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Self-billed credit note",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": -1000.0,
            "taxExclusiveAmount": -1000.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": -1000.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "Defective Components Return",
                    "description": "Return of defective components",
                    "sellersItemIdentification_id": "DEFECT-001",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": -1000.0,
                "orderedQuantity": None,
                "unitCode": "PCE",
                "priceAmount": 1.0,
                "lineExtensionAmount": -1000.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.97,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [{"field": "id", "page": 1}],
    }


@pytest.fixture
def order_standard():
    """Standard Purchase Order."""
    return {
        "id": "ORDER-2025-001",
        "issueDate": "2025-01-27",
        "dueDate": "2025-02-27",
        "documentCurrencyCode": "USD",
        "document_type": "Order",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "VEND001",
            "partyName": "Wholesale Distributor Inc",
            "postalAddress": {
                "streetName": "Distribution Road",
                "buildingNumber": "1500",
                "cityName": "Los Angeles",
                "postalZone": "90001",
                "countrySubentity": "CA",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-213-555-1234",
                "telefax": None,
                "electronicMail": "sales@wholesaledistr.com",
            },
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "BUYER-ORDER",
            "partyName": "Office Supply Retailer",
            "postalAddress": {
                "streetName": "Retail Plaza",
                "buildingNumber": "600",
                "cityName": "Denver",
                "postalZone": "80202",
                "countrySubentity": "CO",
                "identificationCode": "US",
            },
            "contact": {
                "telephone": "+1-303-555-5678",
                "telefax": None,
                "electronicMail": "procurement@officesupply.com",
            },
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": None,
        "additionalDocumentReferences": [],
        "shipVia": "Standard Ground",
        "jobReference": None,
        "delivery": {
            "actualDeliveryDate": None,
            "actualDeliveryTime": None,
            "deliveryLocation": {
                "id": "DELIVERY-LOC-001",
                "description": "Denver Warehouse",
                "address": {
                    "streetName": "Warehouse Drive",
                    "buildingNumber": "100",
                    "cityName": "Denver",
                    "postalZone": "80202",
                    "countrySubentity": "CO",
                    "identificationCode": "US",
                },
            },
            "deliveryParty": {"partyName": "Office Supply Retailer", "contact": None},
            "sourcePage": 1,
        },
        "paymentMeans": {
            "paymentMeansCode": "31",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Prepayment required",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 3500.0,
            "taxExclusiveAmount": 3500.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 3500.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "Office Chairs",
                    "description": "Ergonomic office chairs",
                    "sellersItemIdentification_id": "CHAIR-ERGO",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 50.0,
                "orderedQuantity": 50.0,
                "unitCode": "EA",
                "priceAmount": 70.0,
                "lineExtensionAmount": 3500.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.99,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [{"field": "id", "page": 1}],
    }


@pytest.fixture
def order_cancellation_standard():
    """Standard Order Cancellation."""
    return {
        "id": "ORDERCANCEL-2025-001",
        "issueDate": "2025-01-28",
        "dueDate": None,
        "documentCurrencyCode": "USD",
        "document_type": "OrderCancellation",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "VEND001",
            "partyName": "Wholesale Distributor Inc",
            "postalAddress": {
                "streetName": "Distribution Road",
                "buildingNumber": "1500",
                "cityName": "Los Angeles",
                "postalZone": "90001",
                "countrySubentity": "CA",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-213-555-1234", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "BUYER-CANCEL",
            "partyName": "Office Supply Retailer",
            "postalAddress": {
                "streetName": "Retail Plaza",
                "buildingNumber": "600",
                "cityName": "Denver",
                "postalZone": "80202",
                "countrySubentity": "CO",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-303-555-5678", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": {
            "id": "ORDER-2025-001",
            "salespersonID": None,
            "SalesOrderID": None,
            "customerReference": "BUYER-CANCEL",
            "issueDate": "2025-01-27",
        },
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": None,
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Order cancellation",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 0.0,
            "taxExclusiveAmount": 0.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 0.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [],
        "annotations": [],
        "fieldSourceMap": [],
    }


@pytest.fixture
def order_change_standard():
    """Standard Order Change."""
    return {
        "id": "ORDERCHANGE-2025-001",
        "issueDate": "2025-01-29",
        "dueDate": None,
        "documentCurrencyCode": "USD",
        "document_type": "OrderChange",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "VEND001",
            "partyName": "Wholesale Distributor Inc",
            "postalAddress": {
                "streetName": "Distribution Road",
                "buildingNumber": "1500",
                "cityName": "Los Angeles",
                "postalZone": "90001",
                "countrySubentity": "CA",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-213-555-1234", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "BUYER-CHANGE",
            "partyName": "Office Supply Retailer",
            "postalAddress": {
                "streetName": "Retail Plaza",
                "buildingNumber": "600",
                "cityName": "Denver",
                "postalZone": "80202",
                "countrySubentity": "CO",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-303-555-5678", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": {
            "id": "ORDER-2025-001",
            "salespersonID": None,
            "SalesOrderID": None,
            "customerReference": "BUYER-CHANGE",
            "issueDate": "2025-01-27",
        },
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": None,
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Order change",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 1500.0,
            "taxExclusiveAmount": 1500.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 1500.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [
            {
                "id": "1",
                "item": {
                    "name": "Office Chairs - REDUCED",
                    "description": "Quantity reduced from 50 to 30",
                    "sellersItemIdentification_id": "CHAIR-ERGO",
                    "pack": None,
                    "size": None,
                    "weight": None,
                    "itemInstances": [],
                },
                "invoicedQuantity": 30.0,
                "orderedQuantity": 30.0,
                "unitCode": "EA",
                "priceAmount": 50.0,
                "lineExtensionAmount": 1500.0,
                "orderReference_id": None,
                "allowanceCharges": [],
                "sourcePage": 1,
                "confidence": 0.95,
            }
        ],
        "annotations": [],
        "fieldSourceMap": [],
    }


@pytest.fixture
def order_response_standard():
    """Standard Order Response."""
    return {
        "id": "ORDERRESP-2025-001",
        "issueDate": "2025-01-30",
        "dueDate": None,
        "documentCurrencyCode": "USD",
        "document_type": "OrderResponse",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "VEND-RESP",
            "partyName": "Wholesale Distributor Inc",
            "postalAddress": {
                "streetName": "Distribution Road",
                "buildingNumber": "1500",
                "cityName": "Los Angeles",
                "postalZone": "90001",
                "countrySubentity": "CA",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-213-555-1234", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "BUYER-RESP",
            "partyName": "Office Supply Retailer",
            "postalAddress": {
                "streetName": "Retail Plaza",
                "buildingNumber": "600",
                "cityName": "Denver",
                "postalZone": "80202",
                "countrySubentity": "CO",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-303-555-5678", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": {
            "id": "ORDER-2025-001",
            "salespersonID": None,
            "SalesOrderID": None,
            "customerReference": "BUYER-RESP",
            "issueDate": "2025-01-27",
        },
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": {
            "actualDeliveryDate": "2025-02-10",
            "actualDeliveryTime": None,
            "deliveryLocation": {
                "id": "DELIVERY-LOC",
                "description": "Denver Warehouse",
                "address": {
                    "streetName": "Warehouse Drive",
                    "buildingNumber": "100",
                    "cityName": "Denver",
                    "postalZone": "80202",
                    "countrySubentity": "CO",
                    "identificationCode": "US",
                },
            },
            "deliveryParty": {"partyName": "Office Supply Retailer", "contact": None},
            "sourcePage": 1,
        },
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Accepted",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 3500.0,
            "taxExclusiveAmount": 3500.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 3500.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [],
        "annotations": [],
        "fieldSourceMap": [],
    }


@pytest.fixture
def order_response_simple_standard():
    """Standard OrderResponseSimple."""
    return {
        "id": "ORDERSIMPLERESP-2025-001",
        "issueDate": "2025-01-31",
        "dueDate": None,
        "documentCurrencyCode": "USD",
        "document_type": "OrderResponseSimple",
        "page_count_text": "1",
        "accountingSupplierParty": {
            "id": "VEND-SIMPLE",
            "partyName": "Quick Distributor Ltd",
            "postalAddress": {
                "streetName": "Fast Lane",
                "buildingNumber": "999",
                "cityName": "Portland",
                "postalZone": "97201",
                "countrySubentity": "OR",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-503-555-1234", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "accountingCustomerParty": {
            "id": "BUYER-SIMPLE",
            "partyName": "Small Business Retailer",
            "postalAddress": {
                "streetName": "Main Street",
                "buildingNumber": "123",
                "cityName": "Portland",
                "postalZone": "97201",
                "countrySubentity": "OR",
                "identificationCode": "US",
            },
            "contact": {"telephone": "+1-503-555-5678", "telefax": None, "electronicMail": None},
            "partyTaxSchemes": [],
            "partyLegalEntities": [],
        },
        "payeeParty": None,
        "originatorParty": None,
        "orderReference": None,
        "additionalDocumentReferences": [],
        "shipVia": None,
        "jobReference": None,
        "delivery": None,
        "paymentMeans": {
            "paymentMeansCode": "30",
            "payeeFinancialAccount_id": None,
            "financialInstitutionBranch": None,
            "remit_to_email": None,
        },
        "paymentTerms": {
            "note": "Approved",
            "settlementDiscountPercent": None,
            "penaltySurchargePercent": None,
        },
        "taxTotal": [],
        "legalMonetaryTotal": {
            "lineExtensionAmount": 500.0,
            "taxExclusiveAmount": 500.0,
            "taxInclusiveAmount": None,
            "allowanceTotalAmount": 0.0,
            "chargeTotalAmount": 0.0,
            "prepaidAmount": 0.0,
            "payableAmount": 500.0,
        },
        "globalAllowanceCharges": [],
        "invoiceLines": [],
        "annotations": [],
        "fieldSourceMap": [],
    }
