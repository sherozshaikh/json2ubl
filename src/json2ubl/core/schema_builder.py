import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set
from lxml import etree

from .config import get_logger

logger = get_logger(__name__)

NSMAP = {
    "xs": "http://www.w3.org/2001/XMLSchema",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


class SchemaBuilder:
    """Parse UBL 2.1 XSD files and extract metadata for validation/mapping."""

    def __init__(self, schema_root: str):
        self.schema_root = Path(schema_root)
        self.metadata: Dict[str, Any] = {}
        self._element_cache: Dict[str, Dict[str, Any]] = {}

    def build_all(self) -> Dict[str, Any]:
        """Parse all main document XSDs and build metadata registry."""
        maindoc_dir = self.schema_root / "maindoc"
        
        if not maindoc_dir.exists():
            logger.error(f"Schema directory not found: {maindoc_dir}")
            raise FileNotFoundError(f"Schema root missing: {maindoc_dir}")

        xsd_files = sorted(maindoc_dir.glob("UBL-*.xsd"))
        logger.info(f"Found {len(xsd_files)} main document XSD files")

        for xsd_path in xsd_files:
            try:
                doc_name = xsd_path.stem.replace("UBL-", "").replace("-2.1", "")
                self._parse_document_schema(xsd_path, doc_name)
            except Exception as e:
                logger.warning(f"Failed to parse {xsd_path.name}: {e}")

        logger.info(f"Built metadata for {len(self.metadata)} document types")
        return self.metadata

    def _parse_document_schema(self, xsd_path: Path, doc_name: str) -> None:
        """Parse single document XSD and extract element structure."""
        try:
            tree = etree.parse(str(xsd_path))
            root = tree.getroot()
            
            # Find root element definition for this document
            root_elem_name = doc_name
            root_elem = self._find_element_def(root, root_elem_name)
            
            if root_elem is None:
                logger.warning(f"Root element {root_elem_name} not found in {xsd_path.name}")
                return

            # Extract all valid child elements
            valid_children = self._extract_element_children(root_elem, root)
            
            self.metadata[doc_name] = {
                "xsd_file": xsd_path.name,
                "root_element": root_elem_name,
                "valid_elements": valid_children,
            }
            logger.debug(f"Parsed {doc_name}: {len(valid_children)} valid elements")
        except Exception as e:
            logger.error(f"Error parsing {xsd_path}: {e}")
            raise

    def _find_element_def(self, root: etree._Element, elem_name: str) -> etree._Element | None:
        """Find element definition in schema by name."""
        for elem in root.findall(".//xs:element[@name]", NSMAP):
            if elem.get("name") == elem_name:
                return elem
        return None

    def _extract_element_children(self, elem: etree._Element, root: etree._Element) -> Dict[str, Dict[str, Any]]:
        """Extract all valid child elements and their properties."""
        children = {}
        
        # Find complex type definition
        complex_type_name = elem.get("type")
        if complex_type_name:
            complex_type = self._resolve_type(complex_type_name, root)
            if complex_type is not None:
                children = self._extract_sequence_elements(complex_type, root)
        
        return children

    def _resolve_type(self, type_name: str, root: etree._Element) -> etree._Element | None:
        """Resolve type reference to actual type definition."""
        # Strip namespace prefix if present
        local_name = type_name.split(":")[-1] if ":" in type_name else type_name
        
        for ctype in root.findall(".//xs:complexType[@name]", NSMAP):
            if ctype.get("name") == local_name:
                return ctype
        return None

    def _extract_sequence_elements(self, complex_type: etree._Element, root: etree._Element) -> Dict[str, Dict[str, Any]]:
        """Extract all elements from xs:sequence."""
        children = {}
        
        sequence = complex_type.find(".//xs:sequence", NSMAP)
        if sequence is None:
            return children

        for elem in sequence.findall(".//xs:element[@name]", NSMAP):
            elem_name = elem.get("name")
            min_occurs = int(elem.get("minOccurs", "1"))
            max_occurs = elem.get("maxOccurs", "1")
            is_array = max_occurs == "unbounded"
            elem_type = elem.get("type", "")

            children[elem_name] = {
                "type": elem_type,
                "min_occurs": min_occurs,
                "max_occurs": max_occurs,
                "is_array": is_array,
                "required": min_occurs > 0,
            }

        return children

    def save_cache(self, cache_path: Path) -> None:
        """Save metadata to JSON cache."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved schema metadata cache to {cache_path}")

    @staticmethod
    def load_cache(cache_path: Path) -> Dict[str, Any]:
        """Load metadata from JSON cache."""
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                logger.info(f"Loaded schema metadata from cache: {cache_path}")
                return json.load(f)
        return {}

    @staticmethod
    def get_or_build(schema_root: str, cache_path: Path | None = None) -> Dict[str, Any]:
        """Get metadata from cache or build fresh."""
        if cache_path is None:
            cache_path = Path(schema_root) / ".schema_metadata.json"
        
        cached = SchemaBuilder.load_cache(cache_path)
        if cached:
            return cached

        builder = SchemaBuilder(schema_root)
        metadata = builder.build_all()
        builder.save_cache(cache_path)
        return metadata
