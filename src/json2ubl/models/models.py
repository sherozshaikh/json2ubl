"""
Pydantic models for UBL documents - DEPRECATED/REFERENCE ONLY.

NOTE: These models are provided for reference and type hints only.
The converter uses schema-driven processing and does NOT validate against these models.
The schema-cache is the source of truth for document structure.

To use: Import from json2ubl.models if needed for type hints.
Don't use for validation - converter.map_json_to_document() is schema-driven.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Address(BaseModel):
    model_config = ConfigDict(extra="allow")

    street_name: Optional[str] = None
    additional_street_name: Optional[str] = None
    building_number: Optional[str] = None
    city_name: Optional[str] = None
    postal_zone: Optional[str] = None
    region: Optional[str] = None
    country_subentity: Optional[str] = None
    country_code: Optional[str] = None


class Contact(BaseModel):
    model_config = ConfigDict(extra="allow")

    telephone: Optional[str] = None
    telefax: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class PartyTaxScheme(BaseModel):
    model_config = ConfigDict(extra="allow")

    company_id: Optional[str] = None
    tax_scheme_id: Optional[str] = None
    tax_scheme_name: Optional[str] = None
    tax_scheme_type_code: Optional[str] = None


class PartyIdentification(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None


class PartyLegalEntity(BaseModel):
    model_config = ConfigDict(extra="allow")

    registration_name: Optional[str] = None
    company_id: Optional[str] = None


class Party(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    registration_name: Optional[str] = None
    party_name: Optional[str] = None
    supplier_assigned_account_id: Optional[str] = None
    company_id: Optional[str] = None
    abn: Optional[str] = None
    address: Optional[Address] = None
    contact: Optional[Contact] = None
    tax_schemes: List[PartyTaxScheme] = Field(default_factory=list)
    legal_entities: List[PartyLegalEntity] = Field(default_factory=list)


class TaxSubtotal(BaseModel):
    model_config = ConfigDict(extra="allow")

    taxable_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_percent: Optional[float] = None
    tax_category_id: Optional[str] = None
    tax_scheme_id: Optional[str] = None
    tax_scheme_name: Optional[str] = None
    tax_scheme_type_code: Optional[str] = None


class TaxTotal(BaseModel):
    model_config = ConfigDict(extra="allow")

    tax_amount: Optional[float] = None
    currency_id: Optional[str] = None
    subtotals: List[TaxSubtotal] = Field(default_factory=list)


class AllowanceCharge(BaseModel):
    model_config = ConfigDict(extra="allow")

    is_charge: bool = False
    reason_code: Optional[str] = None
    reason: Optional[str] = None
    amount: Optional[float] = None
    base_amount: Optional[float] = None
    percent: Optional[float] = None
    currency_id: Optional[str] = None


class LegalMonetaryTotal(BaseModel):
    model_config = ConfigDict(extra="allow")

    line_extension_amount: Optional[float] = None
    tax_exclusive_amount: Optional[float] = None
    tax_inclusive_amount: Optional[float] = None
    allowance_total_amount: Optional[float] = None
    charge_total_amount: Optional[float] = None
    prepaid_amount: Optional[float] = None
    payable_rounding_amount: Optional[float] = None
    payable_amount: Optional[float] = None
    currency_id: Optional[str] = None


class ItemInstance(BaseModel):
    model_config = ConfigDict(extra="allow")

    serial_number: Optional[str] = None
    batch_id: Optional[str] = None
    expiry_date: Optional[str] = None
    lot_number: Optional[str] = None


class Item(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    description: Optional[str] = None
    sellers_item_id: Optional[str] = None
    buyers_item_id: Optional[str] = None
    standard_item_id: Optional[str] = None
    pack: Optional[str] = None
    size: Optional[str] = None
    weight: Optional[float] = None
    instances: List[ItemInstance] = Field(default_factory=list)


class InvoiceLine(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    note: Optional[str] = None
    invoiced_quantity: Optional[float] = None
    invoiced_quantity_unit_code: Optional[str] = None
    ordered_quantity: Optional[float] = None
    ordered_quantity_unit_code: Optional[str] = None
    line_extension_amount: Optional[float] = None
    line_extension_currency_id: Optional[str] = None
    price_amount: Optional[float] = None
    price_currency_id: Optional[str] = None
    base_quantity: Optional[float] = None
    base_quantity_unit_code: Optional[str] = None
    item: Optional[Item] = None
    allowance_charges: List[AllowanceCharge] = Field(default_factory=list)
    order_reference_id: Optional[str] = None


class OrderReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    line_id: Optional[str] = None
    issue_date: Optional[str] = None
    salesperson_id: Optional[str] = None
    sales_order_id: Optional[str] = None
    customer_reference: Optional[str] = None


class PaymentMeans(BaseModel):
    model_config = ConfigDict(extra="allow")

    payment_means_code: Optional[str] = None
    payee_financial_account_id: Optional[str] = None
    payee_financial_account_currency_code: Optional[str] = None
    financial_institution_branch_id: Optional[str] = None
    financial_institution_branch_name: Optional[str] = None
    remit_to_email: Optional[str] = None


class PaymentTerms(BaseModel):
    model_config = ConfigDict(extra="allow")

    note: Optional[str] = None
    settlement_discount_percent: Optional[float] = None
    penalty_surcharge_percent: Optional[float] = None
    payment_due_date: Optional[str] = None


class DeliveryLocation(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    description: Optional[str] = None
    address: Optional[Address] = None


class Delivery(BaseModel):
    model_config = ConfigDict(extra="allow")

    actual_delivery_date: Optional[str] = None
    actual_delivery_time: Optional[str] = None
    delivery_location: Optional[DeliveryLocation] = None
    delivery_party: Optional[Party] = None


class DocumentReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    document_type_code: Optional[str] = None
    issue_date: Optional[str] = None
    document_description: Optional[str] = None


class Annotation(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Optional[str] = None
    content: Optional[str] = None
    location: Optional[str] = None
    confidence: Optional[float] = None


class FieldSourceMap(BaseModel):
    model_config = ConfigDict(extra="allow")

    field: Optional[str] = None
    page: Optional[int] = None


class UblDocument(BaseModel):
    """Base UBL document model."""

    model_config = ConfigDict(extra="allow")

    id: str
    issue_date: str
    due_date: Optional[str] = None
    document_currency_code: Optional[str] = None
    document_type: Optional[str] = None

    accounting_supplier_party: Optional[Party] = None
    accounting_customer_party: Optional[Party] = None
    payee_party: Optional[Party] = None
    originator_party: Optional[Party] = None

    order_reference: Optional[OrderReference] = None
    payment_means: Optional[PaymentMeans] = None
    payment_terms: Optional[PaymentTerms] = None
    delivery: Optional[Delivery] = None

    tax_total: Optional[TaxTotal] = None
    legal_monetary_total: Optional[LegalMonetaryTotal] = None

    invoice_lines: List[InvoiceLine] = Field(default_factory=list)
    allowance_charges: List[AllowanceCharge] = Field(default_factory=list)
    document_references: List[DocumentReference] = Field(default_factory=list)

    # Metadata (not serialized to UBL XML, logged only)
    annotations: List[Annotation] = Field(default_factory=list)
    field_source_map: List[FieldSourceMap] = Field(default_factory=list)
    page_count_text: Optional[str] = None
    ship_via: Optional[str] = None
    job_reference: Optional[str] = None


class CreditNoteLine(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    note: Optional[str] = None
    credited_quantity: Optional[float] = None
    credited_quantity_unit_code: Optional[str] = None
    line_extension_amount: Optional[float] = None
    line_extension_currency_id: Optional[str] = None
    price_amount: Optional[float] = None
    price_currency_id: Optional[str] = None
    item: Optional[Item] = None
    allowance_charges: List[AllowanceCharge] = Field(default_factory=list)


class DebitNoteLine(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    note: Optional[str] = None
    debited_quantity: Optional[float] = None
    debited_quantity_unit_code: Optional[str] = None
    line_extension_amount: Optional[float] = None
    line_extension_currency_id: Optional[str] = None
    price_amount: Optional[float] = None
    price_currency_id: Optional[str] = None
    item: Optional[Item] = None
    allowance_charges: List[AllowanceCharge] = Field(default_factory=list)


class OrderLine(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    note: Optional[str] = None
    ordered_quantity: Optional[float] = None
    ordered_quantity_unit_code: Optional[str] = None
    line_extension_amount: Optional[float] = None
    line_extension_currency_id: Optional[str] = None
    price_amount: Optional[float] = None
    price_currency_id: Optional[str] = None
    item: Optional[Item] = None
    allowance_charges: List[AllowanceCharge] = Field(default_factory=list)
