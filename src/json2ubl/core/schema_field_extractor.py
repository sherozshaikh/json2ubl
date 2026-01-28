"""
Schema-based field extraction and validation.

This module provides schema-driven validation of JSON input against UBL XSD schemas.
It validates all fields recursively against the schema cache and collects dropped fields.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..config import get_logger

logger = get_logger(__name__)


class SchemaFieldExtractor:
    """Extract and validate JSON fields against UBL schema caches."""

    def __init__(self):
        """Initialize the extractor."""
        self.schema_cache = {}

    def load_schema_cache(self, document_type: str) -> Dict[str, Any]:
        """
        Load schema cache for a document type.

        Args:
            document_type: Document type name (e.g., 'Invoice', 'CreditNote')

        Returns:
            Schema cache dict with elements and mapping info

        Raises:
            FileNotFoundError: If cache file doesn't exist
            json.JSONDecodeError: If cache file is corrupted
        """
        # Normalize document type
        doc_type = str(document_type).strip()

        # Check if already loaded
        if doc_type in self.schema_cache:
            return self.schema_cache[doc_type]

        # Construct cache file path
        cache_dir = Path(__file__).parent.parent / "schemas" / "cache"
        cache_file = cache_dir / f"{doc_type}_schema_cache.json"

        if not cache_file.exists():
            raise FileNotFoundError(f"Schema cache not found: {cache_file}")

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            self.schema_cache[doc_type] = cache
            logger.debug(f"Loaded schema cache for {doc_type}")
            return cache
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted schema cache file {cache_file}: {e}")
            raise

    def validate_and_extract(
        self, json_dict: Dict[str, Any], schema: Dict[str, Any], path: str = ""
    ) -> Dict[str, Any]:
        """
        Validate and extract fields from JSON against schema.

        Args:
            json_dict: Input JSON dictionary
            schema: Schema elements dict from cache
            path: Current path in nested structure (for logging)

        Returns:
            Dict with:
                - cleaned_json: Only valid fields (with original JSON casing)
                - dropped_fields: List of dropped field paths
        """
        cleaned_json = {}
        dropped_fields = []

        if "elements" not in schema:
            # Top-level call - wrap the schema
            schema = {"elements": schema}

        schema_elements = schema.get("elements", {})

        for field_name, field_value in json_dict.items():
            field_path = f"{path}.{field_name}" if path else field_name

            # Normalize field name to lowercase for schema comparison
            field_name_normalized = field_name.lower()

            if field_name_normalized not in schema_elements:
                # Field not in schema - drop it
                dropped_fields.append(field_path)
                logger.debug(f"Dropped field: {field_path} (not in schema)")
                continue

            field_schema = schema_elements[field_name_normalized]

            # Extract the field value
            extracted_value, field_dropped = self._extract_field(
                field_value, field_schema, field_path
            )

            if extracted_value is not None:
                # Keep original field name casing in cleaned JSON
                cleaned_json[field_name] = extracted_value

            dropped_fields.extend(field_dropped)

        return {"cleaned_json": cleaned_json, "dropped_fields": dropped_fields}

    def _extract_field(
        self, value: Any, field_schema: Dict[str, Any], path: str
    ) -> Tuple[Any, List[str]]:
        """
        Extract a single field, handling nested objects and arrays.

        Args:
            value: The value to extract
            field_schema: Schema definition for this field
            path: Current path in structure

        Returns:
            Tuple of (extracted_value, dropped_fields_list)
        """
        dropped_fields = []

        field_type = field_schema.get("type", "").lower()

        # Handle array types (including maxOccurs="unbounded")
        max_occurs = field_schema.get("maxOccurs", "1")
        is_array = (
            field_type == "array"
            or field_schema.get("cardinality", "").startswith("1..")
            or max_occurs == "unbounded"
            or (max_occurs != "1" and max_occurs != "0")
        )

        if is_array:
            if not isinstance(value, list):
                # Not an array - drop it
                dropped_fields.append(path)
                return None, dropped_fields

            # Validate array structure only (not individual elements)
            extracted_array = []
            for idx, element in enumerate(value):
                # For array elements, pass through but collect nested dropped fields if object
                if isinstance(element, dict) and "nested_elements" in field_schema:
                    nested_result = self.validate_and_extract(
                        element, {"elements": field_schema["nested_elements"]}, f"{path}[{idx}]"
                    )
                    extracted_array.append(nested_result["cleaned_json"])
                    dropped_fields.extend(nested_result["dropped_fields"])
                else:
                    # Keep primitive array elements as-is
                    extracted_array.append(element)

            return extracted_array, dropped_fields

        # Handle nested objects
        if field_type in ("object", "xsd:complextype") or "nested_elements" in field_schema:
            if not isinstance(value, dict):
                # Not an object - drop it
                dropped_fields.append(path)
                return None, dropped_fields

            # If schema has nested_elements, validate against them
            # Otherwise pass through the whole object as-is (real data may not match schema exactly)
            if "nested_elements" not in field_schema:
                # No nested schema defined - pass through entire object
                return value, dropped_fields

            # Recursively validate nested object
            nested_result = self.validate_and_extract(
                value, {"elements": field_schema.get("nested_elements", {})}, path
            )
            return nested_result["cleaned_json"], nested_result["dropped_fields"]

        # Handle primitive types - keep as-is
        return value, dropped_fields

    def validate_json_against_schema(
        self, json_dict: Dict[str, Any], document_type: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Main entry point: Validate JSON against schema and return cleaned JSON + dropped fields.

        Args:
            json_dict: Input JSON document
            document_type: Document type (e.g., '380' or 'Invoice')

        Returns:
            Tuple of (cleaned_json, dropped_fields)
        """
        try:
            # Load schema cache
            cache = self.load_schema_cache(document_type)

            # Extract _document_type_mapping if needed for future use
            schema_elements = cache.get("elements", {})

            # Validate and extract
            result = self.validate_and_extract(json_dict, schema_elements)

            return result["cleaned_json"], result["dropped_fields"]

        except Exception as e:
            logger.error(f"Field validation error for {document_type}: {e}")
            raise

    def get_document_type_mapping(self, document_type: str) -> Dict[str, str]:
        """
        Get document type mapping from schema cache.

        Args:
            document_type: Any document type string/code

        Returns:
            Full _document_type_mapping dict from cache
        """
        try:
            cache = self.load_schema_cache(document_type)
            return cache.get("_document_type_mapping", {})
        except Exception as e:
            logger.error(f"Error loading document type mapping: {e}")
            return {}
