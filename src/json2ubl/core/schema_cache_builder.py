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
        # Cache type lookups to avoid repeated searches
        self._type_cache: Dict[str, Optional[etree._Element]] = {}

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

        for xsd_path in xsd_files:
            doc_name = xsd_path.stem.replace("UBL-", "").replace("-2.1", "")
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

        # Extract all elements from this type to full depth
        elements = self._extract_elements_from_type(
            type_ref, root, visited=None, depth=0, max_depth=20
        )

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

            # Try to extract nested elements recursively to FULL 20-level depth
            if elem_type and depth < max_depth:
                nested_local = elem_type.split(":")[-1] if ":" in elem_type else elem_type

                # Check if this type hasn't been visited yet (prevent cycles)
                if nested_local not in visited:
                    visited_copy = visited.copy()
                    visited_copy.add(nested_local)
                    nested_type_def = self._find_type(nested_local, main_root)

                    if nested_type_def is not None:
                        nested_seq = nested_type_def.find("xs:sequence", NS)
                        if nested_seq is not None:
                            # Recursively extract nested elements to full depth
                            nested = self._extract_nested_from_sequence(
                                nested_seq,
                                main_root,
                                visited_copy,
                                depth + 1,
                                max_depth,
                            )
                            # Store nested elements
                            elem_info["nested_elements"] = nested

            elements[elem_name_lower] = elem_info

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

            # Recursively extract deeper nested elements to FULL 20-level depth
            if elem_type and depth < max_depth:
                nested_local = elem_type.split(":")[-1] if ":" in elem_type else elem_type

                # Track visited to prevent infinite cycles
                if nested_local not in visited:
                    visited_copy = visited.copy()
                    visited_copy.add(nested_local)

                    type_def = self._find_type(nested_local, main_root)
                    if type_def is not None:
                        # Check for sequence (complex elements)
                        inner_seq = type_def.find("xs:sequence", NS)
                        if inner_seq is not None:
                            inner_nested = self._extract_nested_from_sequence(
                                inner_seq, main_root, visited_copy, depth + 1, max_depth
                            )
                            elem_info["nested_elements"] = inner_nested
                        else:
                            # Check for simpleContent with attributes
                            simple_content = type_def.find("xs:simpleContent", NS)
                            if simple_content is not None:
                                ext = simple_content.find("xs:extension", NS)
                                if ext is not None:
                                    # Extract attributes as special _attributes key
                                    attributes = {}
                                    for attr in ext.findall("xs:attribute", NS):
                                        attr_name = attr.get("name", "").lower()
                                        attr_type = attr.get("type", "")
                                        if attr_name:
                                            attributes[attr_name] = {
                                                "name": attr.get("name"),
                                                "type": attr_type,
                                            }
                                    if attributes:
                                        elem_info["_attributes"] = attributes

            nested[elem_name_lower] = elem_info

        return nested

    def _find_type(self, type_name: str, main_root: etree._Element) -> Optional[etree._Element]:
        """Find type definition or element ref in any loaded XSD."""
        # Check cache first
        if type_name in self._type_cache:
            return self._type_cache[type_name]

        result = None

        # Try main document first - direct children only
        for ctype in main_root.findall("xs:complexType[@name]", NS):
            if ctype.get("name") == type_name:
                result = ctype
                break

        # If not found, try common components (only direct children, not recursive)
        if result is None:
            for root in self._xsd_roots.values():
                if root is None:
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
            for root in [main_root] + list(self._xsd_roots.values()):
                if root is None:
                    continue
                for ctype in root.findall("xs:complexType[@name]", NS):
                    if ctype.get("name") == type_with_suffix:
                        result = ctype
                        break
                if result is not None:  # Early exit
                    break

        # Cache result (even if None to avoid repeated searches)
        self._type_cache[type_name] = result
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
