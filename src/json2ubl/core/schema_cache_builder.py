"""
Schema Cache Builder - Parse UBL 2.1 XSD files and generate schema caches.

Builds schema caches by parsing XSD files and extracting element information.
Uses a simple, reliable approach: extract top-level elements and resolve their types.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Set

from lxml import etree

from ..config import get_logger

logger = get_logger(__name__)

# Namespace map for XSD parsing
NS = {
    "xs": "http://www.w3.org/2001/XMLSchema",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
}

# Document type mapping
NUMERIC_TYPE_TO_DOCUMENT_TYPE = {
    "1": "Catalogue",
    "10": "ContractNotice",
    "11": "PriorInformationNotice",
    "129": "CatalogueRequest",
    "140": "Forecast",
    "141": "ForecastRevision",
    "142": "InventoryReport",
    "143": "ProductActivity",
    "144": "RetailEvent",
    "145": "StockAvailabilityReport",
    "146": "TradeItemLocationProfile",
    "147": "TransportProgressStatus",
    "148": "TransportProgressStatusRequest",
    "149": "TransportServiceDescription",
    "15": "ContractAwardNotice",
    "150": "TransportServiceDescriptionRequest",
    "17": "CallForTenders",
    "170": "CataloguePricingUpdate",
    "171": "CatalogueItemSpecificationUpdate",
    "172": "CatalogueDeletion",
    "21": "ItemInformationRequest",
    "220": "Order",
    "221": "OrderResponseSimple",
    "227": "OrderChange",
    "230": "OrderCancellation",
    "231": "OrderResponse",
    "232": "FulfilmentCancellation",
    "24": "AwardedNotification",
    "25": "UnawardedNotification",
    "271": "PackingList",
    "310": "RequestForQuotation",
    "311": "ApplicationResponse",
    "312": "DocumentStatus",
    "313": "DocumentStatusRequest",
    "315": "Quotation",
    "325": "Statement",
    "326": "UtilityStatement",
    "380": "Invoice",
    "381": "CreditNote",
    "383": "DebitNote",
    "389": "SelfBilledInvoice",
    "396": "SelfBilledCreditNote",
    "42": "TransportationStatus",
    "43": "TransportationStatusRequest",
    "430": "RemittanceAdvice",
    "447": "GuaranteeCertificate",
    "45": "TenderReceipt",
    "50": "Tender",
    "54": "TendererQualification",
    "55": "TendererQualificationResponse",
    "6": "CertificateOfOrigin",
    "610": "ForwardingInstructions",
    "632": "DespatchAdvice",
    "633": "ReceiptAdvice",
    "635": "InstructionForReturns",
    "705": "BillOfLading",
    "71": "Reminder",
    "716": "Waybill",
    "744": "GoodsItemItinerary",
    "76": "TransportExecutionPlanRequest",
    "77": "TransportExecutionPlan",
    "780": "FreightInvoice",
    "916": "AttachedDocument",
    "92": "ExceptionCriteria",
    "93": "ExceptionNotification",
}


class SchemaCacheBuilder:
    """Build schema caches from UBL 2.1 XSD files."""

    def __init__(self, schema_root: Optional[str] = None):
        """Initialize cache builder."""
        if schema_root is None:
            schema_root = str(Path(__file__).parent.parent / "schemas" / "ubl-2.1")

        self.schema_root = Path(schema_root)
        self.maindoc_dir = self.schema_root / "maindoc"
        self.common_dir = self.schema_root / "common"
        self.cache_dir = Path(__file__).parent.parent / "schemas" / "cache"

        # Store loaded XSD roots for type resolution
        self._xsd_roots: Dict[str, etree._Element] = {}

    def build_all_caches(self) -> None:
        """Generate schema cache files for all UBL document types."""
        if not self.maindoc_dir.exists():
            raise FileNotFoundError(f"Schema directory not found: {self.maindoc_dir}")

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load common components first
        self._load_common_components()

        # Process each main document XSD
        xsd_files = sorted(self.maindoc_dir.glob("UBL-*.xsd"))
        logger.info(f"Found {len(xsd_files)} UBL document types")

        for xsd_path in xsd_files:
            try:
                doc_name = xsd_path.stem.replace("UBL-", "").replace("-2.1", "")
                logger.info(f"Building cache for {doc_name}...")

                # Parse XSD and extract schema
                tree = etree.parse(str(xsd_path))
                root = tree.getroot()
                self._xsd_roots["main"] = root

                # Build cache data
                cache_data = self._build_cache_for_document(root, doc_name)

                # Save to file
                cache_file = self.cache_dir / f"{doc_name}_schema_cache.json"
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)

                logger.info(f"Generated cache: {cache_file.name}")

            except Exception as e:
                logger.error(f"Error building cache for {xsd_path.name}: {e}")

        logger.info("Schema cache generation complete")

    def _load_common_components(self) -> None:
        """Load common component XSD files."""
        try:
            cbc_file = self.common_dir / "UBL-CommonBasicComponents-2.1.xsd"
            if cbc_file.exists():
                tree = etree.parse(str(cbc_file))
                self._xsd_roots["cbc"] = tree.getroot()

            cac_file = self.common_dir / "UBL-CommonAggregateComponents-2.1.xsd"
            if cac_file.exists():
                tree = etree.parse(str(cac_file))
                self._xsd_roots["cac"] = tree.getroot()

            ext_file = self.common_dir / "UBL-CommonExtensionComponents-2.1.xsd"
            if ext_file.exists():
                tree = etree.parse(str(ext_file))
                self._xsd_roots["ext"] = tree.getroot()

            logger.debug("Loaded common component XSD files")
        except Exception as e:
            logger.warning(f"Error loading common components: {e}")

    def _build_cache_for_document(self, root: etree._Element, doc_name: str) -> Dict[str, Any]:
        """Build cache for a single document type."""
        # Find the root element
        root_elem = self._find_element(root, doc_name)
        if not root_elem:
            raise ValueError(f"Root element {doc_name} not found")

        # Get type reference
        type_ref = root_elem.get("type")
        if not type_ref:
            raise ValueError(f"Root element {doc_name} has no type")

        # Extract all elements from this type
        elements = self._extract_elements_from_type(type_ref, root)

        cache_data = {
            "_document_type_mapping": NUMERIC_TYPE_TO_DOCUMENT_TYPE,
            "elements": elements,
        }
        return cache_data

    def _find_element(self, root: etree._Element, name: str) -> Optional[etree._Element]:
        """Find element definition by name."""
        for elem in root.findall("xs:element[@name]", NS):
            if elem.get("name") == name:
                return elem
        return None

    def _extract_elements_from_type(
        self,
        type_ref: str,
        main_root: etree._Element,
        visited: Optional[Set[str]] = None,
        depth: int = 0,
    ) -> Dict[str, Any]:
        """Extract all child elements from a type reference recursively."""
        if visited is None:
            visited = set()

        # Prevent infinite recursion (limit depth to 10 levels)
        if type_ref in visited or depth > 10:
            return {}
        visited.add(type_ref)

        elements = {}
        local_type = type_ref.split(":")[-1] if ":" in type_ref else type_ref

        # Find the type definition
        type_def = self._find_type(local_type, main_root)
        if not type_def:
            return elements

        # Extract sequence elements
        sequence = type_def.find("xs:sequence", NS)
        if sequence is None:
            return elements

        # Process each element in sequence
        for elem in sequence.findall("xs:element", NS):
            elem_name = self._get_element_name(elem)
            if not elem_name:
                continue

            # Normalize to lowercase
            elem_name_lower = elem_name.lower()

            # Get type from type= or ref= attribute
            elem_type = elem.get("type", "") or elem.get("ref", "")

            # Build element info
            elem_info = {
                "type": elem_type,
                "minOccurs": elem.get("minOccurs", "1"),
                "maxOccurs": elem.get("maxOccurs", "1"),
            }

            # Try to extract nested elements recursively
            if elem_type:
                nested_local = elem_type.split(":")[-1] if ":" in elem_type else elem_type

                # Check if this type hasn't been visited yet
                if nested_local not in visited:
                    nested_type_def = self._find_type(nested_local, main_root)

                    if nested_type_def:
                        nested_seq = nested_type_def.find("xs:sequence", NS)
                        if nested_seq is not None:
                            # Recursively extract nested elements
                            nested = self._extract_nested_from_sequence(
                                nested_seq, main_root, visited.copy(), depth + 1
                            )
                            if nested:
                                elem_info["nested_elements"] = nested

            elements[elem_name_lower] = elem_info

        return elements

    def _extract_nested_from_sequence(
        self, sequence: etree._Element, main_root: etree._Element, visited: Set[str], depth: int
    ) -> Dict[str, Any]:
        """Extract nested elements from a sequence element."""
        if depth > 10:
            return {}

        nested = {}

        for seq_elem in sequence.findall("xs:element", NS):
            elem_name = self._get_element_name(seq_elem)
            if not elem_name:
                continue

            elem_name_lower = elem_name.lower()
            elem_type = seq_elem.get("type", "")

            elem_info = {
                "type": elem_type,
                "minOccurs": seq_elem.get("minOccurs", "1"),
                "maxOccurs": seq_elem.get("maxOccurs", "1"),
            }

            # Recursively extract deeper nested elements
            if elem_type:
                nested_local = elem_type.split(":")[-1] if ":" in elem_type else elem_type

                if nested_local not in visited:
                    visited_copy = visited.copy()
                    visited_copy.add(nested_local)

                    type_def = self._find_type(nested_local, main_root)
                    if type_def:
                        inner_seq = type_def.find("xs:sequence", NS)
                        if inner_seq is not None:
                            inner_nested = self._extract_nested_from_sequence(
                                inner_seq, main_root, visited_copy, depth + 1
                            )
                            if inner_nested:
                                elem_info["nested_elements"] = inner_nested

            nested[elem_name_lower] = elem_info

        return nested

    def _find_type(self, type_name: str, main_root: etree._Element) -> Optional[etree._Element]:
        """Find type definition or element ref in any loaded XSD."""
        # Try main document first
        for ctype in main_root.findall("xs:complexType[@name]", NS):
            if ctype.get("name") == type_name:
                return ctype

        # Try common components
        for root in self._xsd_roots.values():
            if root is None:
                continue
            for ctype in root.findall(".//xs:complexType[@name]", NS):
                if ctype.get("name") == type_name:
                    return ctype

        # If not found as type, try as element ref (for complex types defined as elements)
        for root in [main_root] + list(self._xsd_roots.values()):
            if root is None:
                continue
            for elem in root.findall(".//xs:element[@name]", NS):
                if elem.get("name") == type_name:
                    elem_type = elem.get("type")
                    if elem_type:
                        local_type = elem_type.split(":")[-1] if ":" in elem_type else elem_type
                        return self._find_type(local_type, main_root)

        return None

    def _get_element_name(self, elem: etree._Element) -> Optional[str]:
        """Get element name from name= or ref= attribute."""
        name = elem.get("name")
        if name:
            return name

        ref = elem.get("ref")
        if ref:
            return ref.split(":")[-1] if ":" in ref else ref

        return None
