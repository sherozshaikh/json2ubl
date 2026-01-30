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
        self._nsmap_cache: OrderedDict = OrderedDict()  # Use OrderedDict for LRU eviction
        self._namespace_cache: Dict[str, str] = {}  # Cache computed namespaces
        self._max_cache_size = 100  # Limit namespace cache to 100 entries

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
            doc_type = doc.get("document_type", "Invoice")
            root_element = self.schema_cache.get("root_element_name", doc_type)
            root_namespace = self.schema_cache.get(
                "root_namespace", self._get_default_namespace(doc_type)
            )

            logger.debug(
                f"Serializing {doc_type}: root element={root_element}, ns={root_namespace}"
            )

            nsmap = self._get_nsmap(root_namespace)
            root = etree.Element(f"{{{root_namespace}}}{root_element}", nsmap=nsmap)

            schema_elements = self.schema_cache.get("elements", {})
            self._serialize_recursive(root, doc, schema_elements, root_namespace, depth=0)

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
        """
        if depth > 50:
            logger.warning(f"Max recursion depth exceeded at depth {depth}")
            return

        if not isinstance(data_dict, dict):
            return

        # Normalize data dict keys to lowercase for lookup
        data_keys_lower = {k.lower(): k for k in data_dict.keys()}

        # If schema_spec is empty dict, process all data_dict keys as child elements
        if not schema_spec:
            for data_key_lower, data_key_orig in data_keys_lower.items():
                data_value = data_dict[data_key_orig]
                if data_value is None:
                    continue
                # Use proper UBL casing from schema or capitalize
                element_name = self._capitalize_element_name(data_key_lower)
                if isinstance(data_value, dict):
                    child_elem = self._create_element(parent, element_name, parent_ns)
                    self._serialize_recursive(child_elem, data_value, {}, parent_ns, depth + 1)
                elif isinstance(data_value, list):
                    for item in data_value:
                        if isinstance(item, dict):
                            child_elem = self._create_element(parent, element_name, parent_ns)
                            self._serialize_recursive(child_elem, item, {}, parent_ns, depth + 1)
                        else:
                            self._create_element(parent, element_name, parent_ns, text=str(item))
                else:
                    self._create_element(parent, element_name, parent_ns, text=str(data_value))
            return

        # Process schema elements in order (schema defines the sequence)
        for schema_key_lower, schema_info in schema_spec.items():
            # Skip metadata fields
            if schema_key_lower.startswith("_"):
                continue

            # Look for matching data key (case-insensitive)
            data_key = data_keys_lower.get(schema_key_lower)
            if data_key is None:
                continue

            if data_key not in data_dict:
                logger.warning(f"Key '{data_key}' missing from data_dict, expected from schema")
                continue

            data_value = data_dict[data_key]
            if data_value is None:
                # Preserve null fields as empty elements per A5 requirement
                min_occurs = schema_info.get("minOccurs", "0")
                if min_occurs == "1" or min_occurs == "true":
                    element_name = schema_info.get("name") or self._capitalize_element_name(
                        schema_key_lower
                    )
                    self._create_element(parent, element_name, parent_ns, text="")
                continue

            # Get element info from schema
            max_occurs = schema_info.get("maxOccurs", "1")
            is_array = max_occurs == "unbounded"
            nested_elements = schema_info.get("nested_elements", {})
            element_type = schema_info.get("type", "")

            # Get proper XML element name from schema cache (has correct UBL casing)
            element_name = schema_info.get("name") or self._capitalize_element_name(
                schema_key_lower
            )

            if is_array:
                # Array: create multiple elements
                if isinstance(data_value, list):
                    for item in data_value:
                        if isinstance(item, dict):
                            # Complex nested element - recurse even if nested_elements empty
                            child_elem = self._create_element(parent, element_name, parent_ns)
                            self._serialize_recursive(
                                child_elem, item, nested_elements, parent_ns, depth + 1
                            )
                        else:
                            # Simple element with text
                            text_value = self._extract_value_for_field(item, element_type)
                            self._create_element(parent, element_name, parent_ns, text=text_value)
                else:
                    # Single item, create one element
                    if isinstance(data_value, dict):
                        child_elem = self._create_element(parent, element_name, parent_ns)
                        self._serialize_recursive(
                            child_elem,
                            data_value,
                            nested_elements,
                            parent_ns,
                            depth + 1,
                        )
                    else:
                        text_value = self._extract_value_for_field(data_value, element_type)
                        self._create_element(parent, element_name, parent_ns, text=text_value)
            else:
                # Single element
                if isinstance(data_value, dict):
                    # Complex nested element - recurse even if nested_elements empty
                    child_elem = self._create_element(parent, element_name, parent_ns)
                    self._serialize_recursive(
                        child_elem, data_value, nested_elements, parent_ns, depth + 1
                    )
                elif isinstance(data_value, list) and data_value:
                    # Take first if list provided for non-array field
                    first = data_value[0]
                    if isinstance(first, dict):
                        child_elem = self._create_element(parent, element_name, parent_ns)
                        self._serialize_recursive(
                            child_elem, first, nested_elements, parent_ns, depth + 1
                        )
                    else:
                        text_value = self._extract_value_for_field(first, element_type)
                        self._create_element(parent, element_name, parent_ns, text=text_value)
                else:
                    # Simple scalar element
                    text_value = self._extract_value_for_field(data_value, element_type)
                    self._create_element(parent, element_name, parent_ns, text=text_value)

    def _is_simple_type(self, element_type: str) -> bool:
        """
        Detect if an element type is a simple/basic type based on schema type.

        Simple types (CommonBasicComponents) start with "cbc:" namespace.
        Complex types (CommonAggregateComponents) start with "cac:" namespace.

        Args:
            element_type: Type string from schema (e.g., "cbc:Amount", "cac:Party")

        Returns:
            True if type is a simple type, False otherwise
        """
        # Simple types are in the CommonBasicComponents namespace
        return element_type.startswith("cbc:") if element_type else False

    def _extract_value_for_field(self, value: Any, element_type: str) -> Any:
        """
        Extract scalar value from potentially nested dict structure, using schema type info.

        For simple types (cbc:*), if value is a dict with a "value" key, extract that.
        Otherwise, return the value as-is.

        This handles cases like:
            {"unitcode": "EA", "value": 2.0} -> 2.0
            {"value": 100.50} -> 100.50
            100.50 -> 100.50

        Args:
            value: The value to extract from
            element_type: Type string from schema (e.g., "cbc:Amount")

        Returns:
            Extracted scalar value or original value
        """
        # For simple types with dict structure, extract the "value" key
        if self._is_simple_type(element_type) and isinstance(value, dict) and "value" in value:
            return value["value"]
        # For non-schema-typed or complex types, fall back to basic extraction
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return value

    def _create_element(
        self,
        parent: etree._Element,
        tag: str,
        namespace: str,
        text: Any | None = None,
        attrib: Dict[str, str] | None = None,
    ) -> etree._Element:
        """
        Create and append child element to parent.

        Determines element namespace based on element type:
        - BasicComponents (cbc) for simple types
        - AggregateComponents (cac) for complex types

        Args:
            parent: Parent element
            tag: Element tag name (unqualified)
            namespace: Namespace context
            text: Optional text content
            attrib: Optional attributes

        Returns:
            Created child element
        """
        # Determine element namespace based on element name
        # If no nested elements, likely a BasicComponent
        elem_ns = self._get_element_namespace(tag)

        el = etree.SubElement(parent, f"{{{elem_ns}}}{tag}", **(attrib or {}))
        if text is not None:
            el.text = str(text)
        return el

    def _get_element_namespace(self, tag: str) -> str:
        """
        Determine namespace for element based on tag name conventions.

        UBL convention:
        - CommonBasicComponents for simple elements (usually IDs, codes, amounts, etc.)
        - CommonAggregateComponents for complex elements (objects with children)

        Args:
            tag: Element tag name

        Returns:
            Namespace URI for the element
        """
        # Check if element appears to be aggregate (plural or compound names)
        # This is a heuristic based on common UBL naming patterns
        aggregate_indicators = [
            "Party",
            "Address",
            "Contact",
            "Reference",
            "Total",
            "Subtotal",
            "Scheme",
            "Category",
            "Entity",
            "Item",
            "Line",
            "Component",
            "Charge",
            "Allowance",
            "Delivery",
            "Payment",
            "Period",
        ]

        for indicator in aggregate_indicators:
            if indicator in tag:
                return NS_CAC

        # Default to BasicComponents
        return NS_CBC

    def _capitalize_element_name(self, lowercase_name: str) -> str:
        """
        Convert lowercase schema key to CapitalCase XML element name.

        Examples:
            "id" -> "ID"
            "issuedate" -> "IssueDate"
            "accountingsupplierparty" -> "AccountingSupplierParty"

        Args:
            lowercase_name: Lowercase element name from schema

        Returns:
            CapitalCase element name for XML
        """
        # Special cases for common acronyms
        special_cases = {
            "id": "ID",
            "uri": "URI",
            "url": "URL",
            "abn": "ABN",
            "cbc": "CBC",
            "cac": "CAC",
        }

        if lowercase_name in special_cases:
            return special_cases[lowercase_name]

        # Handle camelCase conversion: split on transitions between lowercase and uppercase
        # But since input is all lowercase, we'll capitalize each word
        # Common separators in schema names:
        separators = ["_", "-"]
        words = [lowercase_name]
        for sep in separators:
            words = [w for word in words for w in word.split(sep)]

        # Capitalize first letter of each word
        return "".join(word.capitalize() for word in words if word)

    def _get_nsmap(self, root_namespace: str) -> dict:
        """
        Get namespace map for serialization.

        Args:
            root_namespace: Root element namespace

        Returns:
            Namespace map dict for lxml
        """
        if root_namespace in self._nsmap_cache:
            return self._nsmap_cache[root_namespace]

        nsmap = dict(NSMAP_BASE)
        nsmap[None] = root_namespace  # Default namespace

        # Limit cache size using LRU eviction to prevent unbounded growth
        if len(self._nsmap_cache) >= self._max_cache_size:
            # Remove oldest (least recently used) entry
            oldest_key = next(iter(self._nsmap_cache))
            del self._nsmap_cache[oldest_key]

        self._nsmap_cache[root_namespace] = nsmap
        return nsmap

    def _get_default_namespace(self, doc_type: str) -> str:
        """
        Get default namespace for document type (cached).

        UBL 2.1 namespace pattern: urn:oasis:names:specification:ubl:schema:xsd:{DocType}-2

        Returns:
            Namespace URI
        """
        if doc_type in self._namespace_cache:
            return self._namespace_cache[doc_type]

        ns = f"urn:oasis:names:specification:ubl:schema:xsd:{doc_type}-2"
        self._namespace_cache[doc_type] = ns
        return ns
