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
from ..constants import NUMERIC_TYPE_TO_DOCUMENT_TYPE

logger = get_logger(__name__)

# Namespace map for XSD parsing
NS = {
    "xs": "http://www.w3.org/2001/XMLSchema",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "udt": "urn:oasis:names:specification:ubl:schema:xsd:UnqualifiedDataTypes-2",
    "ccts-cct": "urn:un:unece:uncefact:data:specification:CoreComponentTypeSchemaModule:2",
}


class SchemaCacheBuilder:
    """Build schema caches from UBL 2.1 XSD files."""

    def __init__(self, schema_root: Optional[str] = None):
        """Initialize cache builder."""
        if schema_root is None:
            self.schema_root = Path(__file__).parent.parent / "schemas" / "ubl-2.1"
        else:
            schema_root_path = Path(schema_root)
            if not schema_root_path.is_absolute():
                # Make relative paths absolute
                self.schema_root = Path(__file__).parent.parent / schema_root_path
            else:
                # Use absolute paths as-is
                self.schema_root = schema_root_path
        self.maindoc_dir = self.schema_root / "maindoc"
        self.common_dir = self.schema_root / "common"
        self.cache_dir = Path(__file__).parent.parent / "schemas" / "cache"

        # Store loaded XSD roots for type resolution
        self._xsd_roots: Dict[str, etree._Element] = {}
        # Cache type lookups to avoid repeated searches
        self._type_cache: Dict[str, Optional[etree._Element]] = {}
        # Cache element ref -> type mappings (e.g., "SellersItemIdentification" -> "ItemIdentificationType")
        self._elem_ref_cache: Dict[str, str] = {}
        # Cache extracted nested elements by type name to avoid re-extracting
        self._nested_cache: Dict[str, Dict[str, Any]] = {}

    def build_cache_for_document(self, doc_name: str) -> None:
        """Build and save cache for a single document type (lazy loading).

        Args:
            doc_name: Document type name (e.g., "Invoice", "CreditNote")

        Raises:
            FileNotFoundError: If document XSD not found
        """
        if not self.maindoc_dir.exists():
            raise FileNotFoundError(f"Schema directory not found: {self.maindoc_dir}")

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load common components first
        self._load_common_components()

        # Find XSD for this document
        xsd_path = self.maindoc_dir / f"UBL-{doc_name}-2.1.xsd"
        if not xsd_path.exists():
            raise FileNotFoundError(f"XSD not found for {doc_name}: {xsd_path}")

        try:
            logger.info(f"Building cache for {doc_name}...")
            tree = etree.parse(str(xsd_path))
            root = tree.getroot()
            self._xsd_roots["main"] = root
            self._cache_element_refs(root)

            # Clear nested cache for each new document
            self._nested_cache.clear()

            # Build cache data
            cache_data = self._build_cache_for_document(root, doc_name)

            # Save to file
            cache_file = self.cache_dir / f"{doc_name}_schema_cache.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Generated cache: {cache_file.name}")

        except Exception as e:
            logger.error(f"Failed to build cache for {doc_name}: {e}")
            raise

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

        caches_generated = 0
        caches_failed = 0

        # TESTING MODE: Build only Invoice for now to test attribute extraction logic
        # REMOVE THIS CONDITION when testing is complete to build all 65 schemas
        BUILD_ONLY_INVOICE = True

        for xsd_path in xsd_files:
            doc_name = xsd_path.stem.replace("UBL-", "").replace("-2.1", "")

            # TESTING: Skip non-Invoice documents
            if BUILD_ONLY_INVOICE and doc_name != "Invoice":
                continue
            try:
                logger.info(f"Building cache for {doc_name}...")

                # Parse XSD and extract schema
                try:
                    tree = etree.parse(str(xsd_path))
                    root = tree.getroot()
                except etree.XMLSyntaxError as xml_err:
                    logger.error(f"Invalid XSD syntax in {xsd_path.name}: {xml_err}")
                    continue
                except IOError as io_err:
                    logger.error(f"Cannot read XSD file {xsd_path.name}: {io_err}")
                    caches_failed += 1
                    continue

                self._xsd_roots["main"] = root
                # Note: Do NOT clear shared type cache during concurrent processing

                # Build cache data
                try:
                    cache_data = self._build_cache_for_document(root, doc_name)
                except Exception as build_err:
                    logger.error(f"Failed to extract schema from {doc_name}: {build_err}")
                    caches_failed += 1
                    continue

                # Save to file
                cache_file = self.cache_dir / f"{doc_name}_schema_cache.json"
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(cache_data, f, indent=2)
                    logger.info(f"Generated cache: {cache_file.name}")
                    caches_generated += 1
                except IOError as io_err:
                    logger.error(f"Failed to write cache file {cache_file.name}: {io_err}")
                    caches_failed += 1
                    continue

            except Exception as e:
                logger.error(f"Unexpected error building cache for {doc_name}: {e}")
                caches_failed += 1

        logger.info(
            f"Schema cache generation complete: {caches_generated} generated, {caches_failed} failed"
        )

    def _load_common_components(self) -> None:
        """Load common component XSD files including UDT and CCTS for attribute extraction."""
        try:
            cbc_file = self.common_dir / "UBL-CommonBasicComponents-2.1.xsd"
            if cbc_file.exists():
                tree = etree.parse(str(cbc_file))
                self._xsd_roots["cbc"] = tree.getroot()
                self._cache_element_refs(tree.getroot())

            cac_file = self.common_dir / "UBL-CommonAggregateComponents-2.1.xsd"
            if cac_file.exists():
                tree = etree.parse(str(cac_file))
                self._xsd_roots["cac"] = tree.getroot()
                self._cache_element_refs(tree.getroot())

            ext_file = self.common_dir / "UBL-CommonExtensionComponents-2.1.xsd"
            if ext_file.exists():
                tree = etree.parse(str(ext_file))
                self._xsd_roots["ext"] = tree.getroot()
                self._cache_element_refs(tree.getroot())

            # Load UDT (Unqualified Data Types) for attribute definitions in base types
            udt_file = self.common_dir / "UBL-UnqualifiedDataTypes-2.1.xsd"
            if udt_file.exists():
                tree = etree.parse(str(udt_file))
                self._xsd_roots["udt"] = tree.getroot()

            # Load CCTS (Core Component Types Schema) for attribute definitions
            ccts_file = self.common_dir / "CCTS_CCT_SchemaModule-2.1.xsd"
            if ccts_file.exists():
                tree = etree.parse(str(ccts_file))
                self._xsd_roots["ccts"] = tree.getroot()

            logger.debug("Loaded common component XSD files including UDT and CCTS")
        except Exception as e:
            logger.warning(f"Error loading common components: {e}")

    def _cache_element_refs(self, root: etree._Element) -> None:
        """Pre-cache element reference -> type mappings to avoid repeated XPath searches."""
        for elem_def in root.findall(".//xs:element[@name][@type]", NS):
            elem_name = elem_def.get("name")
            elem_type = elem_def.get("type")
            if elem_name and elem_type:
                # Store as elem_name -> type_name (without prefix)
                self._elem_ref_cache[elem_name] = elem_type.split(":")[-1]

    def _build_cache_for_document(self, root: etree._Element, doc_name: str) -> Dict[str, Any]:
        """Build cache for a single document type with full depth extraction."""
        # Find the root element
        root_elem = self._find_element(root, doc_name)
        if root_elem is None:
            raise ValueError(f"Root element {doc_name} not found")

        # Get type reference
        type_ref = root_elem.get("type")
        if not type_ref:
            raise ValueError(f"Root element {doc_name} has no type")

        # Extract root element name and namespace
        root_element_name = root_elem.get("name")
        root_namespace = root.get("targetNamespace")

        # PASS 1: Extract all elements from this type to reasonable depth
        # Note: We use depth 7 for most types to prevent exponential explosion.
        # With recursion path tracking, this completes in ~8-10 seconds.
        # For documents with deep delivery/shipment structures, we may need
        # greater depth, but that's handled at serialization time when we
        # look up schemas on-demand for missing nested specs.
        elements = self._extract_elements_from_type(
            type_ref, root, visited=None, depth=0, max_depth=7
        )

        # PASS 2: Separate attribute extraction with independent visited tracking
        # This ensures attributes are extracted even if types were already visited
        # during element extraction. Uses fresh visited set for each type.
        self._extract_attributes_for_all_types(elements, root)

        cache_data = {
            "_document_type_mapping": NUMERIC_TYPE_TO_DOCUMENT_TYPE,
            "root_element_name": root_element_name,
            "root_namespace": root_namespace,
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
        max_depth: int = 20,
    ) -> Dict[str, Any]:
        """Extract all child elements from a type reference recursively to full depth."""
        if visited is None:
            visited = set()

        # Prevent infinite recursion
        if type_ref in visited or depth > max_depth:
            return {}
        visited.add(type_ref)

        # IMPORTANT: We'll remove from visited at the end to allow sibling branches
        # to explore this type independently. This is safe because Python's recursion
        # limit and our max_depth check prevent infinite loops.

        elements = {}
        local_type = type_ref.split(":")[-1] if ":" in type_ref else type_ref

        # Find the type definition
        type_def = self._find_type(local_type, main_root)
        if type_def is None:
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

            # Normalize to lowercase for cache key
            elem_name_lower = elem_name.lower()

            # Get type from type= or ref= attribute
            elem_type = elem.get("type", "") or elem.get("ref", "")

            # Build element info with cardinality and proper element name
            elem_info = {
                "name": elem_name,  # Store proper XML element name from XSD
                "type": elem_type,
                "minOccurs": elem.get("minOccurs", "1"),
                "maxOccurs": elem.get("maxOccurs", "1"),
                "nested_elements": {},  # Always initialize
            }

            # Try to extract nested elements recursively
            if elem_type and depth < max_depth:
                nested_local = elem_type.split(":")[-1] if ":" in elem_type else elem_type

                # For element refs (e.g., cac:AccountingSupplierParty), resolve to actual type
                actual_type_name = nested_local
                if ":" in elem_type and nested_local in self._elem_ref_cache:
                    # Resolve element ref to its type
                    actual_type_name = self._elem_ref_cache[nested_local]

                # Prevent infinite recursion - use global visited set to avoid
                # re-exploring types already seen elsewhere in the tree
                if actual_type_name not in visited:
                    visited.add(actual_type_name)
                    nested_type_def = self._find_type(actual_type_name, main_root)

                    if nested_type_def is not None:
                        nested_seq = nested_type_def.find("xs:sequence", NS)
                        if nested_seq is not None:
                            # Recursively extract nested elements
                            nested = self._extract_nested_from_sequence(
                                nested_seq,
                                main_root,
                                visited,
                                depth + 1,
                                max_depth,
                            )
                            # Store nested elements
                            elem_info["nested_elements"] = nested

            elements[elem_name_lower] = elem_info

        # Remove from visited so sibling branches can explore this type independently
        visited.discard(type_ref)
        return elements

    def _extract_nested_from_sequence(
        self,
        sequence: etree._Element,
        main_root: etree._Element,
        visited: Set[str],
        depth: int,
        max_depth: int = 20,
    ) -> Dict[str, Any]:
        """Extract nested elements from a sequence element to FULL 20-level depth."""
        if depth >= max_depth:
            return {}

        nested = {}

        for seq_elem in sequence.findall("xs:element", NS):
            elem_name = self._get_element_name(seq_elem)
            if not elem_name:
                continue

            elem_name_lower = elem_name.lower()
            # Get type from type= or ref= attribute (ref= is used for element references)
            elem_type = seq_elem.get("type", "") or seq_elem.get("ref", "")

            # Include cardinality information and proper element name
            elem_info = {
                "name": elem_name,  # Store proper XML element name from XSD
                "type": elem_type,
                "minOccurs": seq_elem.get("minOccurs", "1"),
                "maxOccurs": seq_elem.get("maxOccurs", "1"),
                "nested_elements": {},  # Always initialize, will populate if has children
            }

            # Recursively extract deeper nested elements
            if elem_type and depth < max_depth:
                nested_local = elem_type.split(":")[-1] if ":" in elem_type else elem_type

                # For element refs (e.g., cbc:ID), resolve to actual type
                actual_type_name = nested_local
                if ":" in elem_type and nested_local in self._elem_ref_cache:
                    # Resolve element ref to its type
                    actual_type_name = self._elem_ref_cache[nested_local]

                # Prevent infinite recursion during THIS recursion path
                if actual_type_name not in visited:
                    visited.add(actual_type_name)

                    type_def = self._find_type(actual_type_name, main_root)
                    if type_def is not None:
                        # Check for sequence (complex elements)
                        inner_seq = type_def.find("xs:sequence", NS)
                        if inner_seq is not None:
                            inner_nested = self._extract_nested_from_sequence(
                                inner_seq, main_root, visited, depth + 1, max_depth
                            )
                            elem_info["nested_elements"] = inner_nested
                        else:
                            # Check for simpleContent with attributes
                            simple_content = type_def.find("xs:simpleContent", NS)
                            if simple_content is not None:
                                # Use fresh visited set for attribute extraction - don't inherit from type visited set
                                # Attribute extraction only needs to track circular references within its own recursion chain
                                elem_info["_attributes"] = self._extract_attributes_from_extension(
                                    simple_content, main_root, None
                                )

                    # Remove from visited so sibling branches can explore independently
                    visited.discard(actual_type_name)

            nested[elem_name_lower] = elem_info

        return nested

    def _extract_attributes_from_extension(
        self,
        simple_content: etree._Element,
        main_root: etree._Element,
        visited: Optional[Set[str]] = None,
    ) -> Dict[str, Dict[str, str]]:
        """
        Extract attributes from xs:simpleContent/xs:extension or xs:simpleContent/xs:restriction.

        Recursively extracts ALL attributes from base types, handling both extension and restriction.
        Works generically - not specific to any particular attribute.

        Args:
            simple_content: The xs:simpleContent element
            main_root: The main document root for type lookups
            visited: Set of visited types to prevent infinite recursion

        Returns:
            Dict of attribute_name -> {name, type} mappings
        """
        if visited is None:
            visited = set()

        attributes = {}

        # Try both extension and restriction
        ext = simple_content.find("xs:extension", NS)
        if ext is None:
            ext = simple_content.find("xs:restriction", NS)
        if ext is None:
            return attributes

        # Extract direct attributes from this extension/restriction
        for attr in ext.findall("xs:attribute", NS):
            attr_name = attr.get("name", "")
            attr_type = attr.get("type", "")
            if attr_name:
                attr_name_lower = attr_name.lower()
                attributes[attr_name_lower] = {"name": attr_name, "type": attr_type}

        # Also check base type for inherited attributes - recursively
        base_type = ext.get("base", "")
        if base_type:
            base_local = base_type.split(":")[-1] if ":" in base_type else base_type

            # Prevent infinite recursion with circular types in current chain
            # Use a fresh visited set for recursive call to allow other types to be explored
            if base_local not in visited:
                new_visited = visited.copy()
                new_visited.add(base_local)
                # For base types, respect the namespace prefix when present
                # This ensures we find the right type with correct attributes
                base_type_def = None

                # Determine which root(s) to search based on namespace prefix
                root_keys_to_search = []
                if base_type.startswith("ccts-cct:"):
                    root_keys_to_search = [
                        "ccts",
                        "udt",
                    ]  # Look in CCTS first if explicitly prefixed
                elif base_type.startswith("udt:"):
                    root_keys_to_search = [
                        "udt",
                        "ccts",
                    ]  # Look in UDT first if explicitly prefixed
                else:
                    root_keys_to_search = [
                        "udt",
                        "ccts",
                    ]  # Default: UDT first, then CCTS

                # Search for the base type in prioritized roots
                for root_key in root_keys_to_search:
                    root = self._xsd_roots.get(root_key)
                    if root is not None:
                        for ctype in root.findall("xs:complexType[@name]", NS):
                            if ctype.get("name") == base_local:
                                base_type_def = ctype
                                break
                    if base_type_def is not None:
                        break

                # Fallback to main_root if not found
                if base_type_def is None:
                    base_type_def = self._find_type(base_local, main_root)
                if base_type_def is not None:
                    base_simple_content = base_type_def.find("xs:simpleContent", NS)
                    if base_simple_content is not None:
                        # Recursively extract from base type with fresh visited set
                        base_attrs = self._extract_attributes_from_extension(
                            base_simple_content, main_root, new_visited
                        )
                        # Merge base attributes (local attributes override base)
                        for attr_name_lower, attr_info in base_attrs.items():
                            if attr_name_lower not in attributes:
                                attributes[attr_name_lower] = attr_info
                    else:
                        # No simpleContent - check if base type is a simpleType with restriction
                        for simple_type in base_type_def.findall("xs:simpleType", NS):
                            # Extract from simpleType restriction
                            restriction = simple_type.find("xs:restriction", NS)
                            if restriction is not None:
                                for attr in restriction.findall("xs:attribute", NS):
                                    attr_name = attr.get("name", "")
                                    attr_type = attr.get("type", "")
                                    if attr_name:
                                        attr_name_lower = attr_name.lower()
                                        if attr_name_lower not in attributes:
                                            attributes[attr_name_lower] = {
                                                "name": attr_name,
                                                "type": attr_type,
                                            }

        return attributes

    def _find_type(self, type_name: str, main_root: etree._Element) -> Optional[etree._Element]:
        """Find type definition or element ref in any loaded XSD, prioritizing types with attributes."""
        # Check cache first
        if type_name in self._type_cache:
            return self._type_cache[type_name]

        result = None

        # Try main document first - direct children only
        for ctype in main_root.findall("xs:complexType[@name]", NS):
            if ctype.get("name") == type_name:
                result = ctype
                break

        # If not found, try common components - prioritize CCTS (has attributes)
        if result is None:
            # First pass: try CCTS root (has attributes for base types)
            ccts_root = self._xsd_roots.get("ccts")
            if ccts_root is not None:
                for ctype in ccts_root.findall("xs:complexType[@name]", NS):
                    if ctype.get("name") == type_name:
                        result = ctype
                        break

            # Second pass: try other roots in order if not found in CCTS
            if result is None:
                for root_key, root in self._xsd_roots.items():
                    if root is None or root_key == "ccts":  # Skip CCTS (already checked)
                        continue
                    for ctype in root.findall("xs:complexType[@name]", NS):
                        if ctype.get("name") == type_name:
                            result = ctype
                            break
                    if result is not None:  # Early exit
                        break

        # If still not found, try with "Type" suffix (e.g., "InvoiceLine" -> "InvoiceLineType")
        if result is None and not type_name.endswith("Type"):
            type_with_suffix = type_name + "Type"
            # Again prioritize CCTS
            ccts_root = self._xsd_roots.get("ccts")
            if ccts_root is not None:
                for ctype in ccts_root.findall("xs:complexType[@name]", NS):
                    if ctype.get("name") == type_with_suffix:
                        result = ctype
                        break

            # Try other roots
            if result is None:
                for root_key, root in self._xsd_roots.items():
                    if root is None or root_key == "ccts":
                        continue
                    for ctype in root.findall("xs:complexType[@name]", NS):
                        if ctype.get("name") == type_with_suffix:
                            result = ctype
                            break
                    if result is not None:  # Early exit
                        break

            # Also check main document
            if result is None:
                for ctype in main_root.findall("xs:complexType[@name]", NS):
                    if ctype.get("name") == type_with_suffix:
                        result = ctype
                        break

        # Cache result (even if None to avoid repeated searches)
        self._type_cache[type_name] = result
        return result

    def _resolve_element_type(self, elem_ref: str, main_root: etree._Element) -> Optional[str]:
        """
        Resolve an element reference to its actual type.

        For example:
        - Input: "cac:AccountingSupplierParty"
        - Finds: <xs:element name="AccountingSupplierParty" type="SupplierPartyType"/>
        - Returns: "SupplierPartyType"

        If elem_ref looks like a type (no namespace prefix or already ends with Type), returns None.
        """
        if ":" not in elem_ref:
            return None  # Not a qualified reference

        elem_name = elem_ref.split(":")[-1]

        # Check cache first
        cache_key = f"elem_{elem_name}"
        if hasattr(self, "_element_cache") and cache_key in self._element_cache:
            return self._element_cache.get(cache_key)

        if not hasattr(self, "_element_cache"):
            self._element_cache = {}

        result = None

        # Try to find element definition in loaded XSD roots
        for root in self._xsd_roots.values():
            if root is None:
                continue
            # Use more efficient XPath without string concatenation
            for elem_def in root.findall(".//xs:element", NS):
                if elem_def.get("name") == elem_name:
                    result = elem_def.get("type")
                    if result:
                        break
            if result:
                break

        # Cache result
        self._element_cache[cache_key] = result
        return result

    def _extract_attributes_for_all_types(
        self, elements: Dict[str, Any], main_root: etree._Element
    ) -> None:
        """
        PASS 2: Extract attributes for all discovered types using independent visited tracking.

        This is called AFTER element extraction is complete. It recursively walks the element
        tree and extracts attributes from any type that has simpleContent/extension.

        Uses completely independent visited set for each type, ensuring attributes are
        captured even if the type was already visited during element extraction.

        Args:
            elements: Element tree from Pass 1
            main_root: Main document root for type lookups
        """

        def walk_and_extract(elem_info: Dict[str, Any]) -> None:
            """Walk element tree and extract attributes."""
            if not isinstance(elem_info, dict):
                return

            elem_type = elem_info.get("type", "")
            if elem_type:
                # Resolve element reference to actual type if needed
                # e.g., "cbc:InvoicedQuantity" -> "InvoicedQuantityType"
                resolved_type = elem_type
                elem_local_name = elem_type.split(":")[-1] if ":" in elem_type else elem_type
                if elem_local_name in self._elem_ref_cache:
                    resolved_type = self._elem_ref_cache[elem_local_name]

                # Extract attributes using fresh visited set for this type
                attributes = self._extract_all_attributes_from_type(
                    resolved_type, main_root, visited=None
                )

                # Always set _attributes (overwrites empty dict if attributes found)
                if attributes:
                    elem_info["_attributes"] = attributes
                elif "_attributes" not in elem_info:
                    # Only initialize empty if not already present
                    elem_info["_attributes"] = {}

            # Recurse into nested elements
            nested = elem_info.get("nested_elements", {})
            if isinstance(nested, dict):
                for nested_elem_info in nested.values():
                    walk_and_extract(nested_elem_info)

        # Walk the entire element tree
        for elem_info in elements.values():
            walk_and_extract(elem_info)

    def _extract_all_attributes_from_type(
        self,
        type_ref: str,
        main_root: etree._Element,
        visited: Optional[Set[str]] = None,
    ) -> Dict[str, Dict[str, str]]:
        """
        Extract ALL attributes from a type, recursively following its base types.

        This function uses a FRESH visited set for each initial call, allowing complete
        traversal of the type hierarchy without interference from element extraction.

        Works for both simpleContent/extension and simpleContent/restriction patterns.
        Handles the common UBL pattern where base types are in UDT/CCTS schemas.

        Args:
            type_ref: Type reference (e.g., 'cbc:InvoicedQuantityType' or just 'InvoicedQuantityType')
            main_root: Main document root for type lookups
            visited: Set of visited types to prevent infinite recursion (fresh set per initial call)

        Returns:
            Dict mapping attribute_name_lower -> {name, type}
        """
        if visited is None:
            visited = set()

        attributes = {}

        # Normalize type name (remove namespace prefix)
        local_type = type_ref.split(":")[-1] if ":" in type_ref else type_ref

        # Prevent infinite recursion within this traversal
        if local_type in visited:
            return attributes
        visited.add(local_type)

        # Find the type definition - use specialized search that looks in CCTS first for base types
        type_def = self._find_type_for_attributes(local_type, main_root)
        if type_def is None:
            return attributes

        # Check for simpleContent (has attributes)
        simple_content = type_def.find("xs:simpleContent", NS)
        if simple_content is not None:
            # Extract attributes from extension or restriction
            ext = simple_content.find("xs:extension", NS)
            if ext is None:
                ext = simple_content.find("xs:restriction", NS)

            if ext is not None:
                # Extract direct attributes from this extension/restriction
                for attr in ext.findall("xs:attribute", NS):
                    attr_name = attr.get("name", "")
                    attr_type = attr.get("type", "")
                    if attr_name:
                        attr_name_lower = attr_name.lower()
                        attributes[attr_name_lower] = {
                            "name": attr_name,
                            "type": attr_type,
                        }

                # Recursively extract attributes from base type
                base_type = ext.get("base", "")
                if base_type:
                    base_local = base_type.split(":")[-1] if ":" in base_type else base_type
                    if base_local not in visited:
                        # Recursively extract from base type using FRESH visited set
                        # This allows the type to be explored independently
                        base_attrs = self._extract_all_attributes_from_type(
                            base_type, main_root, visited.copy()
                        )
                        # Merge base attributes (local attributes take precedence)
                        for attr_name_lower, attr_info in base_attrs.items():
                            if attr_name_lower not in attributes:
                                attributes[attr_name_lower] = attr_info

        return attributes

    def _find_type_for_attributes(
        self, type_name: str, main_root: etree._Element
    ) -> Optional[etree._Element]:
        """
        Find type definition, prioritizing roots that have attribute definitions.

        For attribute extraction, we want to find the version of the type that HAS attributes.
        UBL pattern: base types are defined in CCTS with attributes, and wrapped in UDT/CBC
        without attributes.

        Search order:
        1. CCTS (has attributes)
        2. UDT (intermediate wrappers)
        3. Main document
        4. Other common components

        Args:
            type_name: Type name to find (without namespace prefix)
            main_root: Main document root

        Returns:
            Type element or None
        """
        # Check cache first
        cache_key = f"attr_type_{type_name}"
        if hasattr(self, "_attr_type_cache") and cache_key in self._attr_type_cache:
            return self._attr_type_cache.get(cache_key)

        if not hasattr(self, "_attr_type_cache"):
            self._attr_type_cache = {}

        result = None

        # Priority 1: CCTS (has attributes for base types like QuantityType)
        ccts_root = self._xsd_roots.get("ccts")
        if ccts_root is not None:
            for ctype in ccts_root.findall("xs:complexType[@name]", NS):
                if ctype.get("name") == type_name:
                    result = ctype
                    break

        # Priority 2: UDT (intermediate wrappers)
        if result is None:
            udt_root = self._xsd_roots.get("udt")
            if udt_root is not None:
                for ctype in udt_root.findall("xs:complexType[@name]", NS):
                    if ctype.get("name") == type_name:
                        result = ctype
                        break

        # Priority 3: Main document
        if result is None:
            for ctype in main_root.findall("xs:complexType[@name]", NS):
                if ctype.get("name") == type_name:
                    result = ctype
                    break

        # Priority 4: Other roots (CBC, CAC, etc.)
        if result is None:
            for root_key, root in self._xsd_roots.items():
                if root is None or root_key in ["ccts", "udt"]:  # Already checked
                    continue
                for ctype in root.findall("xs:complexType[@name]", NS):
                    if ctype.get("name") == type_name:
                        result = ctype
                        break
                if result is not None:
                    break

        # Cache result
        self._attr_type_cache[cache_key] = result
        return result

    def _get_element_name(self, elem: etree._Element) -> Optional[str]:
        """Get element name from name= or ref= attribute."""
        name = elem.get("name")
        if name:
            return name

        ref = elem.get("ref")
        if ref:
            return ref.split(":")[-1] if ":" in ref else ref

        return None
