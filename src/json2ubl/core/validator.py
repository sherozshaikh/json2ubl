import os
import sys
from io import StringIO
from pathlib import Path
from typing import Dict

from lxml import etree

from ..config import get_logger
from ..exceptions import ValidationError as Json2UblValidationError

logger = get_logger(__name__)


DOCUMENT_TYPE_TO_XSD = {
    "ApplicationResponse": "UBL-ApplicationResponse-2.1.xsd",
    "AttachedDocument": "UBL-AttachedDocument-2.1.xsd",
    "AwardedNotification": "UBL-AwardedNotification-2.1.xsd",
    "BillOfLading": "UBL-BillOfLading-2.1.xsd",
    "CallForTenders": "UBL-CallForTenders-2.1.xsd",
    "Catalogue": "UBL-Catalogue-2.1.xsd",
    "CatalogueDeletion": "UBL-CatalogueDeletion-2.1.xsd",
    "CatalogueItemSpecificationUpdate": "UBL-CatalogueItemSpecificationUpdate-2.1.xsd",
    "CataloguePricingUpdate": "UBL-CataloguePricingUpdate-2.1.xsd",
    "CatalogueRequest": "UBL-CatalogueRequest-2.1.xsd",
    "CertificateOfOrigin": "UBL-CertificateOfOrigin-2.1.xsd",
    "ContractAwardNotice": "UBL-ContractAwardNotice-2.1.xsd",
    "ContractNotice": "UBL-ContractNotice-2.1.xsd",
    "CreditNote": "UBL-CreditNote-2.1.xsd",
    "DebitNote": "UBL-DebitNote-2.1.xsd",
    "DespatchAdvice": "UBL-DespatchAdvice-2.1.xsd",
    "DocumentStatus": "UBL-DocumentStatus-2.1.xsd",
    "DocumentStatusRequest": "UBL-DocumentStatusRequest-2.1.xsd",
    "ExceptionCriteria": "UBL-ExceptionCriteria-2.1.xsd",
    "ExceptionNotification": "UBL-ExceptionNotification-2.1.xsd",
    "Forecast": "UBL-Forecast-2.1.xsd",
    "ForecastRevision": "UBL-ForecastRevision-2.1.xsd",
    "ForwardingInstructions": "UBL-ForwardingInstructions-2.1.xsd",
    "FreightInvoice": "UBL-FreightInvoice-2.1.xsd",
    "FulfilmentCancellation": "UBL-FulfilmentCancellation-2.1.xsd",
    "GoodsItemItinerary": "UBL-GoodsItemItinerary-2.1.xsd",
    "GuaranteeCertificate": "UBL-GuaranteeCertificate-2.1.xsd",
    "InstructionForReturns": "UBL-InstructionForReturns-2.1.xsd",
    "InventoryReport": "UBL-InventoryReport-2.1.xsd",
    "Invoice": "UBL-Invoice-2.1.xsd",
    "ItemInformationRequest": "UBL-ItemInformationRequest-2.1.xsd",
    "Order": "UBL-Order-2.1.xsd",
    "OrderCancellation": "UBL-OrderCancellation-2.1.xsd",
    "OrderChange": "UBL-OrderChange-2.1.xsd",
    "OrderResponse": "UBL-OrderResponse-2.1.xsd",
    "OrderResponseSimple": "UBL-OrderResponseSimple-2.1.xsd",
    "PackingList": "UBL-PackingList-2.1.xsd",
    "PriorInformationNotice": "UBL-PriorInformationNotice-2.1.xsd",
    "ProductActivity": "UBL-ProductActivity-2.1.xsd",
    "Quotation": "UBL-Quotation-2.1.xsd",
    "ReceiptAdvice": "UBL-ReceiptAdvice-2.1.xsd",
    "Reminder": "UBL-Reminder-2.1.xsd",
    "RemittanceAdvice": "UBL-RemittanceAdvice-2.1.xsd",
    "RequestForQuotation": "UBL-RequestForQuotation-2.1.xsd",
    "RetailEvent": "UBL-RetailEvent-2.1.xsd",
    "SelfBilledCreditNote": "UBL-SelfBilledCreditNote-2.1.xsd",
    "SelfBilledInvoice": "UBL-SelfBilledInvoice-2.1.xsd",
    "Statement": "UBL-Statement-2.1.xsd",
    "StockAvailabilityReport": "UBL-StockAvailabilityReport-2.1.xsd",
    "Tender": "UBL-Tender-2.1.xsd",
    "TendererQualification": "UBL-TendererQualification-2.1.xsd",
    "TendererQualificationResponse": "UBL-TendererQualificationResponse-2.1.xsd",
    "TenderReceipt": "UBL-TenderReceipt-2.1.xsd",
    "TradeItemLocationProfile": "UBL-TradeItemLocationProfile-2.1.xsd",
    "TransportationStatus": "UBL-TransportationStatus-2.1.xsd",
    "TransportationStatusRequest": "UBL-TransportationStatusRequest-2.1.xsd",
    "TransportExecutionPlan": "UBL-TransportExecutionPlan-2.1.xsd",
    "TransportExecutionPlanRequest": "UBL-TransportExecutionPlanRequest-2.1.xsd",
    "TransportProgressStatus": "UBL-TransportProgressStatus-2.1.xsd",
    "TransportProgressStatusRequest": "UBL-TransportProgressStatusRequest-2.1.xsd",
    "TransportServiceDescription": "UBL-TransportServiceDescription-2.1.xsd",
    "TransportServiceDescriptionRequest": "UBL-TransportServiceDescriptionRequest-2.1.xsd",
    "UnawardedNotification": "UBL-UnawardedNotification-2.1.xsd",
    "UtilityStatement": "UBL-UtilityStatement-2.1.xsd",
    "Waybill": "UBL-Waybill-2.1.xsd",
}


class XmlValidator:
    """Validate XML documents against UBL 2.1 XSD schemas."""

    def __init__(self, schema_root: str):
        self.schema_root = Path(schema_root)
        self._schema_cache: Dict[str, etree.XMLSchema] = {}

    def validate(self, root: etree._Element, document_type: str) -> bool:
        """Validate XML element against appropriate XSD schema."""
        schema = self._get_schema(document_type)
        if schema is None:
            logger.warning(
                f"No schema found for document type {document_type}, skipping validation"
            )
            return True

        old_stderr = sys.stderr
        old_stderr_fd = os.dup(2)
        try:
            sys.stderr = StringIO()

            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, 2)
            os.close(devnull)

            is_valid = schema.validate(root)
        finally:
            os.dup2(old_stderr_fd, 2)
            os.close(old_stderr_fd)

            sys.stderr = old_stderr

        if not is_valid:
            error_log = "\n".join(str(e) for e in schema.error_log)
            num_errors = len(schema.error_log)

            raise Json2UblValidationError(
                f"XML validation failed for {document_type}: {num_errors} error(s)",
                details={"error_log": error_log},
            )

        logger.info(f"XML validation passed for {document_type}")
        return True

    def _get_schema(self, document_type: str) -> etree.XMLSchema | None:
        """Get or load XSD schema for document type."""
        if document_type in self._schema_cache:
            return self._schema_cache[document_type]

        xsd_filename = DOCUMENT_TYPE_TO_XSD.get(document_type)
        if not xsd_filename:
            logger.warning(f"No XSD filename mapping for {document_type}")
            return None

        xsd_path = self.schema_root / "maindoc" / xsd_filename
        if not xsd_path.exists():
            logger.error(f"XSD file not found: {xsd_path}")
            raise FileNotFoundError(f"XSD schema file missing: {xsd_path}")

        try:
            schema_doc = etree.parse(str(xsd_path))
            schema = etree.XMLSchema(schema_doc)
            self._schema_cache[document_type] = schema
            logger.debug(f"Loaded schema: {xsd_filename}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema {xsd_path}: {e}")
            raise Json2UblValidationError(f"Failed to load schema: {e}") from e
