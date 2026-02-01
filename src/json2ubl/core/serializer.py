"""
Generic, schema-driven UBL document serializer.

Converts UBL document dicts to XML recursively following schema structure.
No hardcoded element mappings, no document-type-specific logic.
Works with any UBL 2.1 document type (60+ types).
"""

from collections import OrderedDict
from typing import Any, Dict

from lxml import etree

from ..config import get_logger

logger = get_logger(__name__)

# Standard UBL namespace constants
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"


# Element name normalization mapping (case-insensitive to proper XML names)
ELEMENT_NAME_MAPPING = {
    "streetname": "StreetName",
    "additionalstreetname": "AdditionalStreetName",
    "blockname": "BlockName",
    "registrationname": "RegistrationName",
    "companyid": "CompanyID",
    "taxlevelcode": "TaxLevelCode",
    "exemptionreasoncode": "ExemptionReasonCode",
    "exemptionreason": "ExemptionReason",
    "lineextensionamount": "LineExtensionAmount",
    "postaladdress": "PostalAddress",
}

NSMAP_BASE = {
    "cac": NS_CAC,
    "cbc": NS_CBC,
}


class XmlSerializer:
    """
    Schema-driven generic XML serializer for UBL documents.

    Generates XML recursively following schema structure.
    Uses element ordering from schema sequence.
    Derives namespaces from schema metadata.
    No hardcoded mappings for any document type.
    """

    def __init__(self, schema_cache: Dict[str, Any] | None = None):
        """
        Initialize serializer with schema cache.

        Args:
            schema_cache: Schema cache from schema_cache_builder containing:
                - root_element_name: Root element name from schema
                - root_namespace: Target namespace from schema
                - elements: Element definitions with cardinality/nesting
        """
        self.schema_cache = schema_cache or {}
        self._nsmap_cache: OrderedDict = OrderedDict()
        self._namespace_cache: Dict[str, str] = {}
        self._max_cache_size = 100
        self._element_name_lookup: Dict[str, str] = self._build_element_name_lookup()

    def serialize(self, doc: Dict[str, Any]) -> etree._Element:
        """
        Convert UBL document dict to XML element tree using SCHEMA-DRIVEN approach.

        Recursively serializes following schema structure.
        Element ordering follows schema sequence.
        Namespaces derived from schema metadata.

        Args:
            doc: Document dict with document_type key

        Returns:
            lxml Element representing the UBL XML document
        """
        try:
            doc_type = doc.get("document_type")
            root_element = self.schema_cache.get("root_element_name")
            root_namespace = self.schema_cache.get("root_namespace")

            if not root_element or not root_namespace:
                raise ValueError(
                    f"Schema cache missing root_element_name or root_namespace for {doc_type}. "
                    f"Ensure schema cache was built correctly."
                )

            logger.debug(
                f"Serializing {doc_type}: root element={root_element}, ns={root_namespace}"
            )

            nsmap = self._get_nsmap(root_namespace)
            root = etree.Element(f"{{{root_namespace}}}{root_element}", nsmap=nsmap)

            # Extract document-level currency code for attribute population
            document_currency = doc.get("documentcurrencycode") or doc.get("documentCurrencyCode")

            schema_elements = self.schema_cache.get("elements", {})
            self._serialize_recursive(
                root,
                doc,
                schema_elements,
                root_namespace,
                depth=0,
                document_currency=document_currency,
            )

            return root

        except Exception as e:
            logger.error(f"Error serializing document: {e}")
            raise

    def _serialize_recursive(
        self,
        parent: etree._Element,
        data_dict: Dict[str, Any],
        schema_spec: Dict[str, Any],
        parent_ns: str,
        depth: int = 0,
        document_currency: str | None = None,
    ) -> None:
        """
        Recursively serialize document dict to XML following schema structure.

        Processes each element defined in schema:
        - Creates child elements in schema order
        - Handles cardinality (arrays vs single elements)
        - Recursively processes nested structures
        - Applies proper namespace context
        - Extracts scalar values from dict structures when schema expects simple types

        Args:
            parent: Parent XML element to add children to
            data_dict: Data dict for this level
            schema_spec: Schema specification for this level (element definitions)
            parent_ns: Parent namespace context
            depth: Current recursion depth
            document_currency: Document-level currency code for attribute population
        """
        if depth > 50:
            logger.warning(f"Max recursion depth exceeded at depth {depth}")
            return

        if not isinstance(data_dict, dict):
            return

        # Normalize data dict keys to lowercase for lookup
        data_keys_lower = {k.lower(): k for k in data_dict.keys()}

        if not schema_spec:
            # If schema spec is empty at depth > 1, it means we've gone deeper than
            # the cached schema. This is OK - just skip this level and don't recurse.
            # The data will still be there but won't be nested in the XML.
            if depth > 1:
                logger.warning(
                    f"Schema spec is empty at depth={depth} - may have incomplete nesting"
                )
                return
            else:
                raise ValueError("Schema spec is empty at root level - schema cache is broken")

        # Process schema elements in order (schema defines the sequence)
        for schema_key_lower, schema_info in schema_spec.items():
            # Skip metadata fields
            if schema_key_lower.startswith("_"):
                continue

            try:
                # Look for matching data key (case-insensitive)
                data_key = data_keys_lower.get(schema_key_lower)
                if data_key is None:
                    continue

                if data_key not in data_dict:
                    logger.warning(f"Key '{data_key}' missing from data_dict, expected from schema")
                    continue

                data_value = data_dict[data_key]

                # Get element info from schema EARLY so we can determine namespace
                element_type = schema_info.get("type", "")
                element_attributes = schema_info.get("_attributes", {})

                # Determine correct namespace for this element based on its type
                elem_ns = self._get_element_namespace(element_type, parent_ns)

                # Get proper XML element name from schema cache (has correct UBL casing)
                element_name = schema_info.get("name") or self._capitalize_element_name(
                    schema_key_lower
                )

                if data_value is None:
                    # Preserve null fields as empty elements per A5 requirement
                    min_occurs = schema_info.get("minOccurs", "0")
                    if min_occurs == "1" or min_occurs == "true":
                        self._create_element(parent, element_name, elem_ns, text="")
                    continue

                # Get remaining element info from schema
                max_occurs = schema_info.get("maxOccurs", "1")
                is_array = max_occurs == "unbounded"
                nested_elements = schema_info.get("nested_elements", {})

                if is_array:
                    # Array: create multiple elements
                    if isinstance(data_value, list):
                        for item in data_value:
                            if element_attributes and isinstance(item, dict):
                                # Simple type with attributes
                                attribs = self._extract_attributes_from_data(
                                    item, element_attributes, document_currency
                                )
                                text_value = item.get("_value") or item.get("value", "")
                                self._create_element(
                                    parent,
                                    element_name,
                                    elem_ns,
                                    text=str(text_value),
                                    attrib=attribs,
                                )
                            elif isinstance(item, dict):
                                # Complex nested element - recurse even if nested_elements empty
                                child_elem = self._create_element(parent, element_name, elem_ns)
                                self._serialize_recursive(
                                    child_elem,
                                    item,
                                    nested_elements,
                                    elem_ns,
                                    depth + 1,
                                    document_currency=document_currency,
                                )
                            else:
                                # Simple element with text
                                text_value = self._extract_value_for_field(item, element_type)
                                self._create_element(parent, element_name, elem_ns, text=text_value)
                    else:
                        # Single item, create one element
                        if element_attributes and isinstance(data_value, dict):
                            # Simple type with attributes
                            attribs = self._extract_attributes_from_data(
                                data_value, element_attributes, document_currency
                            )
                            text_value = data_value.get("_value") or data_value.get("value", "")
                            self._create_element(
                                parent,
                                element_name,
                                elem_ns,
                                text=str(text_value),
                                attrib=attribs,
                            )
                        elif isinstance(data_value, dict):
                            child_elem = self._create_element(parent, element_name, elem_ns)
                            self._serialize_recursive(
                                child_elem,
                                data_value,
                                nested_elements,
                                elem_ns,
                                depth + 1,
                                document_currency=document_currency,
                            )
                        else:
                            text_value = self._extract_value_for_field(data_value, element_type)
                            self._create_element(parent, element_name, elem_ns, text=text_value)
                else:
                    # Single element
                    if element_attributes and isinstance(data_value, dict):
                        # Simple type with attributes
                        attribs = self._extract_attributes_from_data(
                            data_value, element_attributes, document_currency
                        )
                        text_value = data_value.get("_value") or data_value.get("value", "")
                        self._create_element(
                            parent,
                            element_name,
                            elem_ns,
                            text=str(text_value),
                            attrib=attribs,
                        )
                    elif isinstance(data_value, dict):
                        # Complex nested element - recurse even if nested_elements empty
                        child_elem = self._create_element(parent, element_name, elem_ns)
                        self._serialize_recursive(
                            child_elem,
                            data_value,
                            nested_elements,
                            elem_ns,
                            depth + 1,
                            document_currency=document_currency,
                        )
                    elif isinstance(data_value, list) and data_value:
                        # Take first if list provided for non-array field
                        first = data_value[0]
                        if element_attributes and isinstance(first, dict):
                            # Simple type with attributes
                            attribs = self._extract_attributes_from_data(
                                first, element_attributes, document_currency
                            )
                            text_value = first.get("_value") or first.get("value", "")
                            self._create_element(
                                parent,
                                element_name,
                                elem_ns,
                                text=str(text_value),
                                attrib=attribs,
                            )
                        elif isinstance(first, dict):
                            child_elem = self._create_element(parent, element_name, elem_ns)
                            self._serialize_recursive(
                                child_elem,
                                first,
                                nested_elements,
                                elem_ns,
                                depth + 1,
                                document_currency=document_currency,
                            )
                        else:
                            text_value = self._extract_value_for_field(first, element_type)
                            self._create_element(parent, element_name, elem_ns, text=text_value)
                    else:
                        # Simple scalar element
                        # If the schema defines attributes, apply them even for scalar values
                        if element_attributes:
                            # Create empty dict for attribute extraction (will use schema defaults)
                            attribs = self._extract_attributes_from_data(
                                {}, element_attributes, document_currency
                            )
                            text_value = self._extract_value_for_field(data_value, element_type)
                            self._create_element(
                                parent,
                                element_name,
                                elem_ns,
                                text=str(text_value),
                                attrib=attribs,
                            )
                        else:
                            text_value = self._extract_value_for_field(data_value, element_type)
                            self._create_element(parent, element_name, elem_ns, text=text_value)

            except Exception as e:
                # Type mismatch or serialization error - log warning and skip field
                element_name = schema_info.get("name") or self._capitalize_element_name(
                    schema_key_lower
                )
                logger.warning(
                    f"Failed to serialize field '{element_name}': {e}. "
                    f"Skipping field to continue processing."
                )

    def _extract_attributes_from_data(
        self,
        data_dict: Dict[str, Any],
        schema_attributes: Dict[str, Dict[str, str]],
        document_currency: str | None = None,
    ) -> Dict[str, str]:
        """
        Extract attribute values from data dict based on schema attributes.

        For missing attributes, use document-level fallbacks (e.g., document_currency for currencyID).
        """
        attributes = {}
        for attr_name_lower, attr_info in schema_attributes.items():
            attr_value = data_dict.get(attr_name_lower)

            # Fallback to document currency for currencyID if not in data
            if attr_value is None and attr_name_lower == "currencyid" and document_currency:
                attr_value = document_currency

            if attr_value is not None:
                attr_name = attr_info.get("name", attr_name_lower)
                attributes[attr_name] = str(attr_value)
        return attributes

    def _get_element_namespace(self, element_type: str, parent_ns: str) -> str:
        """
        Determine namespace for element based on type prefix.

        Element types like 'cbc:UBLVersionID' or 'cac:Party' have namespace prefixes.
        Map those to actual namespace URIs.
        """
        if not element_type:
            logger.debug("_get_element_namespace: No element_type, returning parent_ns")
            return parent_ns

        # Extract prefix (e.g., 'cbc' from 'cbc:UBLVersionID')
        prefix = element_type.split(":")[0] if ":" in element_type else None

        # Map prefixes to full namespaces
        namespace_map = {
            "cbc": NS_CBC,
            "cac": NS_CAC,
            "ext": NS_EXT,
        }

        result_ns = namespace_map.get(prefix, parent_ns)
        # logger.debug(
        #     f"_get_element_namespace: element_type={element_type}, prefix={prefix}, result_ns ends with={result_ns.split('/')[-1] if result_ns else 'NONE'}"
        # )
        return result_ns

    def _extract_value_for_field(self, value: Any, element_type: str) -> str:
        """Extract and format value for XML element based on type."""
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value) if value is not None else ""

    def _create_element(
        self,
        parent: etree._Element,
        tag_name: str,
        namespace: str,
        text: str = None,
        attrib: Dict[str, str] = None,
    ) -> etree._Element:
        """Create XML element with proper namespace."""
        element = etree.SubElement(parent, f"{{{namespace}}}{tag_name}", attrib or {})
        if text is not None:
            element.text = str(text)
        return element

    def _get_nsmap(self, namespace: str) -> Dict[str, str]:
        """Get namespace map with default namespace."""
        if namespace in self._nsmap_cache:
            return self._nsmap_cache[namespace]

        nsmap = dict(NSMAP_BASE)
        nsmap[None] = namespace
        self._nsmap_cache[namespace] = nsmap
        return nsmap

    def _capitalize_element_name(self, name_lower: str) -> str:
        """Capitalize element name for XML (PascalCase)."""
        return "".join(word.capitalize() for word in name_lower.split("_"))

    def _build_element_name_lookup(self) -> Dict[str, str]:
        """Build lookup table for element names from schema cache."""
        lookup = {}

        def extract_names(elements: Dict, lookup_dict: Dict):
            for key_lower, elem_info in elements.items():
                if isinstance(elem_info, dict):
                    if "name" in elem_info:
                        lookup_dict[key_lower] = elem_info["name"]
                    if "nested_elements" in elem_info:
                        extract_names(elem_info["nested_elements"], lookup_dict)

        if "elements" in self.schema_cache:
            extract_names(self.schema_cache["elements"], lookup)

        return lookup
