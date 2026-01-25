import os
from pathlib import Path
from typing import Dict
from lxml import etree

from ..config import get_logger
from ..exceptions import ValidationError as Json2UblValidationError

logger = get_logger(__name__)

DOCUMENT_TYPE_TO_XSD = {
    "Invoice": "UBL-Invoice-2.1.xsd",
    "CreditNote": "UBL-CreditNote-2.1.xsd",
    "DebitNote": "UBL-DebitNote-2.1.xsd",
    "Order": "UBL-Order-2.1.xsd",
    "OrderResponse": "UBL-OrderResponse-2.1.xsd",
    "Quotation": "UBL-Quotation-2.1.xsd",
    "ReceiptAdvice": "UBL-ReceiptAdvice-2.1.xsd",
    "OrderCancellation": "UBL-OrderCancellation-2.1.xsd",
    "OrderChange": "UBL-OrderChange-2.1.xsd",
    "OrderResponseSimple": "UBL-OrderResponseSimple-2.1.xsd",
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

        if not schema.validate(root):
            error_log = "\n".join(str(e) for e in schema.error_log)
            logger.error(f"XML validation failed for {document_type}:\n{error_log}")
            raise Json2UblValidationError(f"XML validation failed: {error_log}")

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
            raise Json2UblValidationError(f"Failed to load schema: {e}")
