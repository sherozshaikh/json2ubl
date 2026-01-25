from typing import Any, Dict, List
from pydantic import ValidationError

from ..config import get_logger
from ..exceptions import MappingError, DocumentTypeError
from ..models import (
    UblDocument,
    Party,
    Address,
    Contact,
    PartyTaxScheme,
    PartyLegalEntity,
    Item,
    ItemInstance,
    InvoiceLine,
    TaxTotal,
    TaxSubtotal,
    LegalMonetaryTotal,
    AllowanceCharge,
    OrderReference,
    PaymentMeans,
    PaymentTerms,
    Delivery,
    DeliveryLocation,
    DocumentReference,
    Annotation,
    FieldSourceMap,
)

logger = get_logger(__name__)

# Map UBL numeric type codes to document type strings
# Per UBL 2.1 spec - UNCL 1001 Invoice Type Code
NUMERIC_TYPE_TO_DOCUMENT_TYPE = {
    "1" : "Catalogue",
    "10" : "ContractNotice",
    "11" : "PriorInformationNotice",
    "129" : "CatalogueRequest",
    "140" : "Forecast",
    "141" : "ForecastRevision",
    "142" : "InventoryReport",
    "143" : "ProductActivity",
    "144" : "RetailEvent",
    "145" : "StockAvailabilityReport",
    "146" : "TradeItemLocationProfile",
    "147" : "TransportProgressStatus",
    "148" : "TransportProgressStatusRequest",
    "149" : "TransportServiceDescription",
    "15" : "ContractAwardNotice",
    "150" : "TransportServiceDescriptionRequest",
    "17" : "CallForTenders",
    "170" : "CataloguePricingUpdate",
    "171" : "CatalogueItemSpecificationUpdate",
    "172" : "CatalogueDeletion",
    "21" : "ItemInformationRequest",
    "220" : "Order",
    "221" : "OrderResponseSimple",
    "227" : "OrderChange",
    "230" : "OrderCancellation",
    "231" : "OrderResponse",
    "232" : "FulfilmentCancellation",
    "24" : "AwardedNotification",
    "25" : "UnawardedNotification",
    "271" : "PackingList",
    "310" : "RequestForQuotation",
    "311" : "ApplicationResponse",
    "312" : "DocumentStatus",
    "313" : "DocumentStatusRequest",
    "315" : "Quotation",
    "325" : "Statement",
    "326" : "UtilityStatement",
    "380" : "Invoice",
    "381" : "CreditNote",
    "383" : "DebitNote",
    "389" : "SelfBilledInvoice",
    "396" : "SelfBilledCreditNote",
    "42" : "TransportationStatus",
    "43" : "TransportationStatusRequest",
    "430" : "RemittanceAdvice",
    "447" : "GuaranteeCertificate",
    "45" : "TenderReceipt",
    "50" : "Tender",
    "54" : "TendererQualification",
    "55" : "TendererQualificationResponse",
    "6" : "CertificateOfOrigin",
    "610" : "ForwardingInstructions",
    "632" : "DespatchAdvice",
    "633" : "ReceiptAdvice",
    "635" : "InstructionForReturns",
    "705" : "BillOfLading",
    "71" : "Reminder",
    "716" : "Waybill",
    "744" : "GoodsItemItinerary",
    "76" : "TransportExecutionPlanRequest",
    "77" : "TransportExecutionPlan",
    "780" : "FreightInvoice",
    "916" : "AttachedDocument",
    "92" : "ExceptionCriteria",
    "93" : "ExceptionNotification"
}

DOCUMENT_TYPE_TO_CLASS = {
    "Catalogue": UblDocument,
    "ContractNotice": UblDocument,
    "PriorInformationNotice": UblDocument,
    "CatalogueRequest": UblDocument,
    "Forecast": UblDocument,
    "ForecastRevision": UblDocument,
    "InventoryReport": UblDocument,
    "ProductActivity": UblDocument,
    "RetailEvent": UblDocument,
    "StockAvailabilityReport": UblDocument,
    "TradeItemLocationProfile": UblDocument,
    "TransportProgressStatus": UblDocument,
    "TransportProgressStatusRequest": UblDocument,
    "TransportServiceDescription": UblDocument,
    "ContractAwardNotice": UblDocument,
    "TransportServiceDescriptionRequest": UblDocument,
    "CallForTenders": UblDocument,
    "CataloguePricingUpdate": UblDocument,
    "CatalogueItemSpecificationUpdate": UblDocument,
    "CatalogueDeletion": UblDocument,
    "ItemInformationRequest": UblDocument,
    "Order": UblDocument,
    "OrderResponseSimple": UblDocument,
    "OrderChange": UblDocument,
    "OrderCancellation": UblDocument,
    "OrderResponse": UblDocument,
    "FulfilmentCancellation": UblDocument,
    "AwardedNotification": UblDocument,
    "UnawardedNotification": UblDocument,
    "PackingList": UblDocument,
    "RequestForQuotation": UblDocument,
    "ApplicationResponse": UblDocument,
    "DocumentStatus": UblDocument,
    "DocumentStatusRequest": UblDocument,
    "Quotation": UblDocument,
    "Statement": UblDocument,
    "UtilityStatement": UblDocument,
    "Invoice": UblDocument,
    "CreditNote": UblDocument,
    "DebitNote": UblDocument,
    "SelfBilledInvoice": UblDocument,
    "SelfBilledCreditNote": UblDocument,
    "TransportationStatus": UblDocument,
    "TransportationStatusRequest": UblDocument,
    "RemittanceAdvice": UblDocument,
    "GuaranteeCertificate": UblDocument,
    "TenderReceipt": UblDocument,
    "Tender": UblDocument,
    "TendererQualification": UblDocument,
    "TendererQualificationResponse": UblDocument,
    "CertificateOfOrigin": UblDocument,
    "ForwardingInstructions": UblDocument,
    "DespatchAdvice": UblDocument,
    "ReceiptAdvice": UblDocument,
    "InstructionForReturns": UblDocument,
    "BillOfLading": UblDocument,
    "Reminder": UblDocument,
    "Waybill": UblDocument,
    "GoodsItemItinerary": UblDocument,
    "TransportExecutionPlanRequest": UblDocument,
    "TransportExecutionPlan": UblDocument,
    "FreightInvoice": UblDocument,
    "AttachedDocument": UblDocument,
    "ExceptionCriteria": UblDocument,
    "ExceptionNotification": UblDocument
}


class JsonMapper:
    """Map JSON objects to Pydantic models with schema awareness."""

    def __init__(self, schema_metadata: Dict[str, Any] | None = None):
        self.schema_metadata = schema_metadata or {}

    def map_json_to_document(self, raw: Dict[str, Any]) -> UblDocument:
        """Convert raw JSON dict to UblDocument."""
        doc_type_raw = raw.get("document_type")
        if not doc_type_raw:
            raise DocumentTypeError("Missing 'document_type' field")

        try:
            # Convert numeric type codes (380, 381, etc.) to document type strings
            # If numeric code provided, map it; otherwise use as-is
            doc_type = NUMERIC_TYPE_TO_DOCUMENT_TYPE.get(str(doc_type_raw), str(doc_type_raw))
            logger.debug(f"Mapped document_type '{doc_type_raw}' -> '{doc_type}'")

            # Validate and extract required fields
            invoice_id = (raw.get("id", "") or "").strip()
            if not invoice_id:
                raise MappingError("Missing or empty 'id' field (invoice identifier required)")

            issue_date = (raw.get("issueDate", "") or "").strip()
            if not issue_date:
                raise MappingError("Missing or empty 'issueDate' field")

            # Map basic fields
            doc = UblDocument(
                id=invoice_id,
                issue_date=issue_date,
                due_date=raw.get("dueDate"),
                document_currency_code=raw.get("documentCurrencyCode"),
                document_type=doc_type,
                page_count_text=raw.get("page_count_text"),
                ship_via=raw.get("shipVia"),
                job_reference=raw.get("jobReference"),
            )

            # Map parties
            doc.accounting_supplier_party = self._map_party(raw.get("accountingSupplierParty"))
            doc.accounting_customer_party = self._map_party(raw.get("accountingCustomerParty"))
            doc.payee_party = self._map_party(raw.get("payeeParty"))
            doc.originator_party = self._map_party(raw.get("originatorParty"))

            # Map references and terms
            doc.order_reference = self._map_order_reference(raw.get("orderReference"))
            doc.payment_means = self._map_payment_means(raw.get("paymentMeans"))
            doc.payment_terms = self._map_payment_terms(raw.get("paymentTerms"))
            doc.delivery = self._map_delivery(raw.get("delivery"))

            # Map financial
            doc.tax_total = self._map_tax_total(raw.get("taxTotal"), doc.document_currency_code)
            doc.legal_monetary_total = self._map_legal_monetary_total(
                raw.get("legalMonetaryTotal"), doc.document_currency_code
            )

            # Map lines
            doc.invoice_lines = self._map_invoice_lines(
                raw.get("invoiceLines"), doc.document_currency_code
            )

            # Map allowances/charges
            doc.allowance_charges = self._map_allowance_charges(
                raw.get("globalAllowanceCharges"), doc.document_currency_code
            )

            # Map document references
            doc.document_references = self._map_document_references(
                raw.get("additionalDocumentReferences")
            )

            # Map metadata (not for UBL XML)
            doc.annotations = self._map_annotations(raw.get("annotations"))
            doc.field_source_map = self._map_field_source_map(raw.get("fieldSourceMap"))

            return doc
        except ValidationError as e:
            logger.error(f"Validation error mapping JSON: {e}")
            raise MappingError(f"Failed to map JSON to document: {e}")
        except MappingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in mapping: {e}")
            raise MappingError(f"Unexpected mapping error: {e}")

    def _map_party(self, raw: Dict[str, Any] | None) -> Party | None:
        """Map party object."""
        if not raw:
            return None

        try:
            return Party(
                id=raw.get("id"),
                registration_name=raw.get("registrationName"),
                party_name=raw.get("partyName"),
                supplier_assigned_account_id=raw.get("supplierAssignedAccountID"),
                company_id=raw.get("companyID"),
                abn=raw.get("abn"),
                address=self._map_address(raw.get("postalAddress")),
                contact=self._map_contact(raw.get("contact")),
                tax_schemes=self._map_tax_schemes(raw.get("partyTaxSchemes")),
                legal_entities=self._map_legal_entities(raw.get("partyLegalEntities")),
            )
        except Exception as e:
            logger.warning(f"Failed to map party: {e}")
            return None

    def _map_address(self, raw: Dict[str, Any] | None) -> Address | None:
        """Map address object."""
        if not raw:
            return None
        try:
            return Address(
                street_name=raw.get("streetName"),
                additional_street_name=raw.get("additionalStreetName"),
                building_number=raw.get("buildingNumber"),
                city_name=raw.get("cityName"),
                postal_zone=raw.get("postalZone"),
                region=raw.get("region"),
                country_subentity=raw.get("countrySubentity"),
                country_code=raw.get("identificationCode"),
            )
        except Exception as e:
            logger.warning(f"Failed to map address: {e}")
            return None

    def _map_contact(self, raw: Dict[str, Any] | None) -> Contact | None:
        """Map contact object."""
        if not raw or not any(raw.values()):
            return None
        try:
            return Contact(
                telephone=raw.get("telephone"),
                telefax=raw.get("telefax"),
                email=raw.get("email") or raw.get("electronicMail"),
                name=raw.get("name"),
            )
        except Exception as e:
            logger.warning(f"Failed to map contact: {e}")
            return None

    def _map_tax_schemes(self, raw_list: List[Dict[str, Any]] | None) -> List[PartyTaxScheme]:
        """Map tax schemes list."""
        if not raw_list:
            return []
        result = []
        for item in raw_list:
            try:
                result.append(
                    PartyTaxScheme(
                        company_id=item.get("companyID"),
                        tax_scheme_id=item.get("taxSchemeID"),
                        tax_scheme_name=item.get("taxSchemeName"),
                        tax_scheme_type_code=item.get("taxSchemeTypeCode"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to map tax scheme: {e}")
        return result

    def _map_legal_entities(self, raw_list: List[Dict[str, Any]] | None) -> List[PartyLegalEntity]:
        """Map all legal entities (not just first)."""
        if not raw_list:
            return []
        result = []
        for item in raw_list:
            try:
                result.append(
                    PartyLegalEntity(
                        registration_name=item.get("registrationName"),
                        company_id=item.get("companyID"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to map legal entity: {e}")
        return result

    def _map_order_reference(self, raw: Dict[str, Any] | None) -> OrderReference | None:
        """Map order reference."""
        if not raw:
            return None
        try:
            return OrderReference(
                id=raw.get("id"),
                line_id=raw.get("lineID"),
                issue_date=raw.get("issueDate"),
                salesperson_id=raw.get("salespersonID"),
                sales_order_id=raw.get("SalesOrderID"),
                customer_reference=raw.get("customerReference"),
            )
        except Exception as e:
            logger.warning(f"Failed to map order reference: {e}")
            return None

    def _map_payment_means(self, raw: Dict[str, Any] | None) -> PaymentMeans | None:
        """Map payment means (handles both flat and nested structure)."""
        if not raw:
            return None
        try:
            # Handle nested financialInstitutionBranch object (from OCR/real data)
            branch_obj = raw.get("financialInstitutionBranch") or {}
            branch_id = branch_obj.get("id") if branch_obj else None
            branch_name = (
                branch_obj.get("name") or branch_obj.get("branchName") if branch_obj else None
            )

            # Also check for flat structure (legacy/direct API)
            if not branch_id:
                branch_id = raw.get("financialInstitutionBranchID")
            if not branch_name:
                branch_name = raw.get("financialInstitutionBranchName")

            return PaymentMeans(
                payment_means_code=raw.get("paymentMeansCode"),
                payee_financial_account_id=raw.get("payeeFinancialAccountID")
                or raw.get("payeeFinancialAccount_id"),
                payee_financial_account_currency_code=raw.get("payeeFinancialAccountCurrencyCode"),
                financial_institution_branch_id=branch_id,
                financial_institution_branch_name=branch_name,
                remit_to_email=raw.get("remitToEmail") or raw.get("remit_to_email"),
            )
        except Exception as e:
            logger.warning(f"Failed to map payment means: {e}")
            return None

    def _map_payment_terms(self, raw: Dict[str, Any] | None) -> PaymentTerms | None:
        """Map payment terms."""
        if not raw:
            return None
        try:
            return PaymentTerms(
                note=raw.get("note"),
                settlement_discount_percent=raw.get("settlementDiscountPercent"),
                penalty_surcharge_percent=raw.get("penaltySurchargePercent"),
                payment_due_date=raw.get("paymentDueDate"),
            )
        except Exception as e:
            logger.warning(f"Failed to map payment terms: {e}")
            return None

    def _map_delivery(self, raw: Dict[str, Any] | None) -> Delivery | None:
        """Map delivery."""
        if not raw:
            return None
        try:
            loc_raw = raw.get("deliveryLocation") or {}
            return Delivery(
                actual_delivery_date=raw.get("actualDeliveryDate"),
                actual_delivery_time=raw.get("actualDeliveryTime"),
                delivery_location=DeliveryLocation(
                    id=loc_raw.get("id"),
                    description=loc_raw.get("description"),
                    address=self._map_address(loc_raw.get("address")),
                ),
                delivery_party=self._map_party(raw.get("deliveryParty")),
            )
        except Exception as e:
            logger.warning(f"Failed to map delivery: {e}")
            return None

    def _map_tax_total(
        self, raw_list: List[Dict[str, Any]] | None, currency: str | None
    ) -> TaxTotal | None:
        """Map tax total (aggregates all subtotals from all TaxTotal elements)."""
        if not raw_list or len(raw_list) == 0:
            return None
        try:
            # UBL allows multiple TaxTotal elements; aggregate all subtotals
            all_subtotals = []
            total_tax_amount = 0.0

            for tax_total_item in raw_list:
                if not tax_total_item:
                    continue

                # Accumulate tax amounts from all TaxTotal elements
                item_tax_amount = tax_total_item.get("taxAmount")
                if item_tax_amount is not None:
                    try:
                        total_tax_amount += float(item_tax_amount)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid taxAmount: {item_tax_amount}")

                # Collect all subtotals from all TaxTotal elements
                for st in tax_total_item.get("taxSubtotals", []):
                    try:
                        all_subtotals.append(
                            TaxSubtotal(
                                taxable_amount=st.get("taxableAmount"),
                                tax_amount=st.get("taxAmount"),
                                tax_percent=st.get("taxPercent"),
                                tax_category_id=st.get("taxCategoryID"),
                                tax_scheme_id=st.get("taxSchemeID"),
                                tax_scheme_name=st.get("taxSchemeName"),
                                tax_scheme_type_code=st.get("taxSchemeTypeCode"),
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Failed to map tax subtotal: {e}")

            if not all_subtotals and total_tax_amount == 0.0:
                logger.warning("No tax subtotals or tax amount found in tax total")
                return None

            return TaxTotal(
                tax_amount=total_tax_amount if total_tax_amount > 0 else None,
                currency_id=currency,
                subtotals=all_subtotals,
            )
        except Exception as e:
            logger.warning(f"Failed to map tax total: {e}")
            return None

    def _map_legal_monetary_total(
        self, raw: Dict[str, Any] | None, currency: str | None
    ) -> LegalMonetaryTotal | None:
        """Map legal monetary total."""
        if not raw:
            return None
        try:
            return LegalMonetaryTotal(
                line_extension_amount=raw.get("lineExtensionAmount"),
                tax_exclusive_amount=raw.get("taxExclusiveAmount"),
                tax_inclusive_amount=raw.get("taxInclusiveAmount"),
                allowance_total_amount=raw.get("allowanceTotalAmount"),
                charge_total_amount=raw.get("chargeTotalAmount"),
                prepaid_amount=raw.get("prepaidAmount"),
                payable_rounding_amount=raw.get("payableRoundingAmount"),
                payable_amount=raw.get("payableAmount"),
                currency_id=currency,
            )
        except Exception as e:
            logger.warning(f"Failed to map legal monetary total: {e}")
            return None

    def _map_invoice_lines(
        self, raw_list: List[Dict[str, Any]] | None, currency: str | None
    ) -> List[InvoiceLine]:
        """Map invoice lines."""
        if not raw_list:
            return []
        result = []
        for raw in raw_list:
            try:
                item_raw = raw.get("item") or {}
                result.append(
                    InvoiceLine(
                        id=raw.get("id"),
                        note=raw.get("note") or item_raw.get("note"),
                        invoiced_quantity=raw.get("invoicedQuantity"),
                        invoiced_quantity_unit_code=raw.get("invoicedQuantityUnitCode")
                        or raw.get("unitCode"),
                        ordered_quantity=raw.get("orderedQuantity"),
                        ordered_quantity_unit_code=raw.get("orderedQuantityUnitCode"),
                        base_quantity=raw.get("baseQuantity"),
                        base_quantity_unit_code=raw.get("baseQuantityUnitCode"),
                        line_extension_amount=raw.get("lineExtensionAmount"),
                        line_extension_currency_id=currency,
                        price_amount=raw.get("priceAmount"),
                        price_currency_id=currency,
                        item=self._map_item(item_raw, currency),
                        allowance_charges=self._map_allowance_charges(
                            raw.get("allowanceCharges"), currency
                        ),
                        order_reference_id=raw.get("orderReferenceID"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to map invoice line: {e}")
        return result

    def _map_item(self, raw: Dict[str, Any] | None, currency: str | None) -> Item | None:
        """Map item with instances."""
        if not raw:
            return None
        try:
            instances = []
            for inst_raw in raw.get("itemInstances", []):
                instances.append(
                    ItemInstance(
                        serial_number=inst_raw.get("serialNumber"),
                        batch_id=inst_raw.get("batchID"),
                        expiry_date=inst_raw.get("expiryDate"),
                        lot_number=inst_raw.get("lotNumber"),
                    )
                )
            return Item(
                name=raw.get("name"),
                description=raw.get("description"),
                sellers_item_id=raw.get("sellersItemIdentification_id"),
                buyers_item_id=raw.get("buyersItemIdentification_id"),
                standard_item_id=raw.get("standardItemIdentification_id"),
                pack=raw.get("pack"),
                size=raw.get("size"),
                weight=raw.get("weight"),
                instances=instances,
            )
        except Exception as e:
            logger.warning(f"Failed to map item: {e}")
            return None

    def _map_allowance_charges(
        self, raw_list: List[Dict[str, Any]] | None, currency: str | None
    ) -> List[AllowanceCharge]:
        """Map allowance/charge items."""
        if not raw_list:
            return []
        result = []
        for raw in raw_list:
            try:
                result.append(
                    AllowanceCharge(
                        is_charge=raw.get("chargeIndicator", False),
                        reason_code=raw.get("allowanceChargeReasonCode"),
                        reason=raw.get("allowanceChargeReason"),
                        amount=raw.get("amount"),
                        base_amount=raw.get("baseAmount"),
                        percent=raw.get("percent"),
                        currency_id=currency,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to map allowance/charge: {e}")
        return result

    def _map_document_references(
        self, raw_list: List[Dict[str, Any]] | None
    ) -> List[DocumentReference]:
        """Map additional document references."""
        if not raw_list:
            return []
        result = []
        for raw in raw_list:
            try:
                result.append(
                    DocumentReference(
                        id=raw.get("id"),
                        document_type_code=raw.get("documentTypeCode"),
                        issue_date=raw.get("issueDate"),
                        document_description=raw.get("documentDescription"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to map document reference: {e}")
        return result

    def _map_annotations(self, raw_list: List[Dict[str, Any]] | None) -> List[Annotation]:
        """Map annotations (metadata only)."""
        if not raw_list:
            return []
        result = []
        for raw in raw_list:
            try:
                result.append(
                    Annotation(
                        type=raw.get("type"),
                        content=raw.get("content"),
                        location=raw.get("location"),
                        confidence=raw.get("confidence"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to map annotation: {e}")
        return result

    def _map_field_source_map(self, raw_list: List[Dict[str, Any]] | None) -> List[FieldSourceMap]:
        """Map field source map (metadata only)."""
        if not raw_list:
            return []
        result = []
        for raw in raw_list:
            try:
                result.append(
                    FieldSourceMap(
                        field=raw.get("field"),
                        page=raw.get("page"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to map field source: {e}")
        return result
