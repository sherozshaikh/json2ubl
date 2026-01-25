from lxml import etree
from typing import Any, Dict, List, Optional

from ..config import get_logger
from ..exceptions import ValidationError as Json2UblValidationError
from ..models import (
    UblDocument,
    Address,
    Contact,
    Party,
    PartyLegalEntity,
    PartyTaxScheme,
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
)

logger = get_logger(__name__)

NSMAP_BASE = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}

DOCUMENT_NAMESPACES = {
    "Invoice": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "CreditNote": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
    "DebitNote": "urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2",
    "Order": "urn:oasis:names:specification:ubl:schema:xsd:Order-2",
}

ROOT_ELEMENT_BY_TYPE = {
    "Invoice": "Invoice",
    "TAX INVOICE": "Invoice",
    "CreditNote": "CreditNote",
    "Credit Note": "CreditNote",
    "DebitNote": "DebitNote",
    "Debit Note": "DebitNote",
    "Order": "Order",
    "PurchaseOrder": "Order",
    "OrderResponse": "OrderResponse",
    "Quotation": "Quotation",
    "OrderCancellation": "OrderCancellation",
    "OrderChange": "OrderChange",
    "OrderResponseSimple": "OrderResponseSimple",
    "ReceiptAdvice": "ReceiptAdvice",
    "SelfBilledInvoice": "Invoice",
    "SelfBilledCreditNote": "CreditNote",
    "FreightInvoice": "Invoice",
}

TYPE_CODE_ELEMENT = {
    "Invoice": "InvoiceTypeCode",
    "CreditNote": "CreditNoteTypeCode",
    "DebitNote": "DebitNoteTypeCode",
    "Order": "OrderTypeCode",
}

LINE_ELEMENT_BY_ROOT = {
    "Invoice": "InvoiceLine",
    "CreditNote": "CreditNoteLine",
    "DebitNote": "DebitNoteLine",
    "Order": "OrderLine",
}

QUANTITY_ELEMENT_BY_ROOT = {
    "Invoice": "InvoicedQuantity",
    "CreditNote": "CreditedQuantity",
    "DebitNote": "DebitedQuantity",
    "Order": "OrderedQuantity",
}


class XmlSerializer:
    """Convert Pydantic UBL models to lxml XML."""

    def __init__(self):
        self._nsmap_cache: Dict[str, dict] = {}

    def serialize(self, doc: UblDocument) -> etree._Element:
        """Convert UblDocument to XML element tree."""
        root_element = ROOT_ELEMENT_BY_TYPE.get(doc.document_type, "Invoice")
        namespace = DOCUMENT_NAMESPACES.get(root_element, DOCUMENT_NAMESPACES["Invoice"])
        nsmap = self._get_nsmap(root_element, namespace)

        root = etree.Element(f"{{{namespace}}}{root_element}", nsmap=nsmap)

        # UBL header elements
        self._cbc(root, "UBLVersionID", "2.1")
        self._cbc(root, "ID", doc.id)
        self._cbc(root, "IssueDate", doc.issue_date)

        if doc.due_date:
            self._cbc(root, "DueDate", doc.due_date)

        # Type code
        type_code_elem = TYPE_CODE_ELEMENT.get(root_element, "InvoiceTypeCode")
        self._cbc(root, type_code_elem, doc.document_type or "380")

        # Currency
        if doc.document_currency_code:
            self._cbc(root, "DocumentCurrencyCode", doc.document_currency_code)

        # Parties
        if doc.accounting_supplier_party:
            self._serialize_party(root, doc.accounting_supplier_party, "AccountingSupplierParty")
        if doc.accounting_customer_party:
            self._serialize_party(root, doc.accounting_customer_party, "AccountingCustomerParty")
        if doc.payee_party:
            self._serialize_party(root, doc.payee_party, "PayeeParty")
        if doc.originator_party:
            self._serialize_party(root, doc.originator_party, "OriginatorParty")

        # Order reference
        if doc.order_reference:
            self._serialize_order_reference(root, doc.order_reference)

        # Payment
        if doc.payment_means:
            self._serialize_payment_means(root, doc.payment_means)
        if doc.payment_terms:
            self._serialize_payment_terms(root, doc.payment_terms)

        # Delivery
        if doc.delivery:
            self._serialize_delivery(root, doc.delivery)

        # Document references
        for doc_ref in doc.document_references:
            self._serialize_document_reference(root, doc_ref)

        # Allowances/charges
        for ac in doc.allowance_charges:
            self._serialize_allowance_charge(root, ac)

        # Tax and monetary
        if doc.tax_total:
            self._serialize_tax_total(root, doc.tax_total)
        if doc.legal_monetary_total:
            self._serialize_legal_monetary_total(root, doc.legal_monetary_total)

        # Invoice lines - FIXED: pass quantity_element properly
        line_element = LINE_ELEMENT_BY_ROOT.get(root_element, "InvoiceLine")
        quantity_element = QUANTITY_ELEMENT_BY_ROOT.get(root_element, "InvoicedQuantity")
        for line in doc.invoice_lines:
            self._serialize_invoice_line(
                root, line, line_element, quantity_element, doc.document_currency_code
            )

        return root

    def _get_nsmap(self, root_element: str, namespace: str) -> dict:
        """Get namespace map for document type."""
        if root_element in self._nsmap_cache:
            return self._nsmap_cache[root_element]
        nsmap = dict(NSMAP_BASE)
        nsmap[None] = namespace
        self._nsmap_cache[root_element] = nsmap
        return nsmap

    def _cbc(self, parent: etree._Element, tag: str, text: Any = None, **attrib) -> etree._Element:
        """Create CommonBasicComponent element."""
        el = etree.SubElement(parent, f"{{{NSMAP_BASE['cbc']}}}{tag}", **attrib)
        if text is not None:
            el.text = str(text)
        return el

    def _cac(self, parent: etree._Element, tag: str, **attrib) -> etree._Element:
        """Create CommonAggregateComponent element."""
        return etree.SubElement(parent, f"{{{NSMAP_BASE['cac']}}}{tag}", **attrib)

    def _serialize_address(self, parent: etree._Element, address: Address) -> None:
        """Serialize Address to PostalAddress element."""
        addr_el = self._cac(parent, "PostalAddress")
        if address.street_name:
            self._cbc(addr_el, "StreetName", address.street_name)
        if address.additional_street_name:
            self._cbc(addr_el, "AdditionalStreetName", address.additional_street_name)
        if address.building_number:
            self._cbc(addr_el, "BuildingNumber", address.building_number)
        if address.city_name:
            self._cbc(addr_el, "CityName", address.city_name)
        if address.postal_zone:
            self._cbc(addr_el, "PostalZone", address.postal_zone)
        if address.region:
            self._cbc(addr_el, "Region", address.region)
        if address.country_subentity:
            self._cbc(addr_el, "CountrySubentityCode", address.country_subentity)
        if address.country_code:
            country = self._cac(addr_el, "Country")
            self._cbc(country, "IdentificationCode", address.country_code)

    def _serialize_contact(self, parent: etree._Element, contact: Contact) -> None:
        """Serialize Contact element."""
        c = self._cac(parent, "Contact")
        if contact.telephone:
            self._cbc(c, "Telephone", contact.telephone)
        if contact.telefax:
            self._cbc(c, "Telefax", contact.telefax)
        if contact.email:
            self._cbc(c, "ElectronicMail", contact.email)
        if contact.name:
            self._cbc(c, "Name", contact.name)

    def _serialize_party(self, parent: etree._Element, party: Party, role: str) -> None:
        """Serialize Party element with role."""
        role_el = self._cac(parent, role)
        party_el = self._cac(role_el, "Party")

        # PartyIdentification
        if party.id:
            pi = self._cac(party_el, "PartyIdentification")
            self._cbc(pi, "ID", party.id)

        # PartyName
        if party.party_name:
            pn = self._cac(party_el, "PartyName")
            self._cbc(pn, "Name", party.party_name)

        # PostalAddress
        if party.address:
            self._serialize_address(party_el, party.address)

        # PartyTaxScheme
        for ts in party.tax_schemes:
            pts = self._cac(party_el, "PartyTaxScheme")
            if ts.company_id:
                self._cbc(pts, "CompanyID", ts.company_id)
            tax_scheme = self._cac(pts, "TaxScheme")
            if ts.tax_scheme_id:
                self._cbc(tax_scheme, "ID", ts.tax_scheme_id)
            if ts.tax_scheme_name:
                self._cbc(tax_scheme, "Name", ts.tax_scheme_name)
            if ts.tax_scheme_type_code:
                self._cbc(tax_scheme, "TaxTypeCode", ts.tax_scheme_type_code)

        # PartyLegalEntity
        for le in party.legal_entities:
            ple = self._cac(party_el, "PartyLegalEntity")
            if le.registration_name:
                self._cbc(ple, "RegistrationName", le.registration_name)
            if le.company_id:
                self._cbc(ple, "CompanyID", le.company_id)

        # Contact
        if party.contact:
            self._serialize_contact(party_el, party.contact)

    def _serialize_order_reference(self, parent: etree._Element, ref: OrderReference) -> None:
        """Serialize OrderReference element."""
        or_el = self._cac(parent, "OrderReference")
        if ref.id:
            self._cbc(or_el, "ID", ref.id)
        if ref.issue_date:
            self._cbc(or_el, "IssueDate", ref.issue_date)
        if ref.sales_order_id:
            self._cbc(or_el, "SalesOrderID", ref.sales_order_id)
        if ref.customer_reference:
            self._cbc(or_el, "CustomerReference", ref.customer_reference)

    def _serialize_payment_means(self, parent: etree._Element, pm: PaymentMeans) -> None:
        """Serialize PaymentMeans element."""
        pm_el = self._cac(parent, "PaymentMeans")
        if pm.payment_means_code:
            self._cbc(pm_el, "PaymentMeansCode", pm.payment_means_code)
        if pm.payee_financial_account_id:
            pfa = self._cac(pm_el, "PayeeFinancialAccount")
            self._cbc(pfa, "ID", pm.payee_financial_account_id)

    def _serialize_payment_terms(self, parent: etree._Element, pt: PaymentTerms) -> None:
        """Serialize PaymentTerms element."""
        pt_el = self._cac(parent, "PaymentTerms")
        if pt.note:
            self._cbc(pt_el, "Note", pt.note)
        if pt.settlement_discount_percent:
            self._cbc(pt_el, "SettlementDiscountPercent", pt.settlement_discount_percent)
        if pt.penalty_surcharge_percent:
            self._cbc(pt_el, "PenaltySurchargePercent", pt.penalty_surcharge_percent)
        if pt.payment_due_date:
            self._cbc(pt_el, "PaymentDueDate", pt.payment_due_date)

    def _serialize_delivery(self, parent: etree._Element, delivery: Delivery) -> None:
        """Serialize Delivery element."""
        del_el = self._cac(parent, "Delivery")
        if delivery.actual_delivery_date:
            self._cbc(del_el, "ActualDeliveryDate", delivery.actual_delivery_date)
        if delivery.delivery_location:
            loc_el = self._cac(del_el, "DeliveryLocation")
            if delivery.delivery_location.id:
                self._cbc(loc_el, "ID", delivery.delivery_location.id)
            if delivery.delivery_location.description:
                self._cbc(loc_el, "Description", delivery.delivery_location.description)
            if delivery.delivery_location.address:
                self._serialize_address(loc_el, delivery.delivery_location.address)

    def _serialize_document_reference(self, parent: etree._Element, ref: DocumentReference) -> None:
        """Serialize AdditionalDocumentReference element."""
        doc_ref = self._cac(parent, "AdditionalDocumentReference")
        if ref.id:
            self._cbc(doc_ref, "ID", ref.id)
        if ref.document_type_code:
            self._cbc(doc_ref, "DocumentTypeCode", ref.document_type_code)
        if ref.issue_date:
            self._cbc(doc_ref, "IssueDate", ref.issue_date)
        if ref.document_description:
            self._cbc(doc_ref, "DocumentDescription", ref.document_description)

    def _serialize_allowance_charge(self, parent: etree._Element, ac: AllowanceCharge) -> None:
        """Serialize AllowanceCharge element."""
        ac_el = self._cac(parent, "AllowanceCharge")
        self._cbc(ac_el, "ChargeIndicator", "true" if ac.is_charge else "false")
        if ac.reason_code:
            self._cbc(ac_el, "AllowanceChargeReasonCode", ac.reason_code)
        if ac.reason:
            self._cbc(ac_el, "AllowanceChargeReason", ac.reason)
        if ac.base_amount:
            currency = ac.currency_id or ""
            self._cbc(ac_el, "BaseAmount", ac.base_amount, currencyID=currency)
        if ac.amount:
            currency = ac.currency_id or ""
            self._cbc(ac_el, "Amount", ac.amount, currencyID=currency)
        if ac.percent:
            self._cbc(ac_el, "Percent", ac.percent)

    def _serialize_tax_total(self, parent: etree._Element, tt: TaxTotal) -> None:
        """Serialize TaxTotal element."""
        tt_el = self._cac(parent, "TaxTotal")
        if tt.tax_amount:
            currency = tt.currency_id or ""
            self._cbc(tt_el, "TaxAmount", tt.tax_amount, currencyID=currency)
        for st in tt.subtotals:
            self._serialize_tax_subtotal(tt_el, st, tt.currency_id)

    def _serialize_tax_subtotal(
        self, parent: etree._Element, st: TaxSubtotal, currency: str | None
    ) -> None:
        """Serialize TaxSubtotal element."""
        st_el = self._cac(parent, "TaxSubtotal")
        if st.taxable_amount:
            c = currency or ""
            self._cbc(st_el, "TaxableAmount", st.taxable_amount, currencyID=c)
        if st.tax_amount:
            c = currency or ""
            self._cbc(st_el, "TaxAmount", st.tax_amount, currencyID=c)

        tc = self._cac(st_el, "TaxCategory")
        if st.tax_category_id:
            self._cbc(tc, "ID", st.tax_category_id)
        if st.tax_percent:
            self._cbc(tc, "Percent", st.tax_percent)

        ts = self._cac(tc, "TaxScheme")
        if st.tax_scheme_id:
            self._cbc(ts, "ID", st.tax_scheme_id)
        if st.tax_scheme_name:
            self._cbc(ts, "Name", st.tax_scheme_name)

    def _serialize_legal_monetary_total(
        self, parent: etree._Element, lmt: LegalMonetaryTotal
    ) -> None:
        """Serialize LegalMonetaryTotal element."""
        lmt_el = self._cac(parent, "LegalMonetaryTotal")
        c = lmt.currency_id or ""

        if lmt.line_extension_amount is not None:
            self._cbc(lmt_el, "LineExtensionAmount", lmt.line_extension_amount, currencyID=c)
        if lmt.tax_exclusive_amount is not None:
            self._cbc(lmt_el, "TaxExclusiveAmount", lmt.tax_exclusive_amount, currencyID=c)
        if lmt.tax_inclusive_amount is not None:
            self._cbc(lmt_el, "TaxInclusiveAmount", lmt.tax_inclusive_amount, currencyID=c)
        if lmt.allowance_total_amount is not None:
            self._cbc(lmt_el, "AllowanceTotalAmount", lmt.allowance_total_amount, currencyID=c)
        if lmt.charge_total_amount is not None:
            self._cbc(lmt_el, "ChargeTotalAmount", lmt.charge_total_amount, currencyID=c)
        if lmt.prepaid_amount is not None:
            self._cbc(lmt_el, "PrepaidAmount", lmt.prepaid_amount, currencyID=c)
        if lmt.payable_amount is not None:
            self._cbc(lmt_el, "PayableAmount", lmt.payable_amount, currencyID=c)

    def _serialize_invoice_line(
        self,
        parent: etree._Element,
        line: InvoiceLine,
        line_tag: str,
        quantity_element: str,
        currency: str | None,
    ) -> None:
        """Serialize invoice/credit/debit line."""
        il = self._cac(parent, line_tag)

        if line.id:
            self._cbc(il, "ID", line.id)
        if line.note:
            self._cbc(il, "Note", line.note)

        # Quantity - use the provided quantity element name
        if line.invoiced_quantity is not None:
            unit = line.invoiced_quantity_unit_code or ""
            self._cbc(il, quantity_element, line.invoiced_quantity, unitCode=unit)

        if line.line_extension_amount is not None:
            c = line.line_extension_currency_id or currency or ""
            self._cbc(il, "LineExtensionAmount", line.line_extension_amount, currencyID=c)

        # Item
        if line.item:
            self._serialize_item(il, line.item)

        # Price
        if line.price_amount is not None:
            price_el = self._cac(il, "Price")
            c = line.price_currency_id or currency or ""
            self._cbc(price_el, "PriceAmount", line.price_amount, currencyID=c)

        # AllowanceCharges
        for ac in line.allowance_charges:
            self._serialize_allowance_charge(il, ac)

    def _serialize_item(self, parent: etree._Element, item: Item) -> None:
        """Serialize Item with serial numbers."""
        item_el = self._cac(parent, "Item")

        if item.name:
            self._cbc(item_el, "Name", item.name)
        if item.description:
            self._cbc(item_el, "Description", item.description)

        # Serial numbers
        for inst in item.instances:
            if inst.serial_number:
                self._cbc(item_el, "SerialNumber", inst.serial_number)
            if inst.batch_id:
                self._cbc(item_el, "BatchID", inst.batch_id)
            if inst.lot_number:
                self._cbc(item_el, "LotNumberID", inst.lot_number)

        # Item identifications
        if item.sellers_item_id:
            sid = self._cac(item_el, "SellersItemIdentification")
            self._cbc(sid, "ID", item.sellers_item_id)
        if item.buyers_item_id:
            bid = self._cac(item_el, "BuyersItemIdentification")
            self._cbc(bid, "ID", item.buyers_item_id)
        if item.standard_item_id:
            stid = self._cac(item_el, "StandardItemIdentification")
            self._cbc(stid, "ID", item.standard_item_id)
