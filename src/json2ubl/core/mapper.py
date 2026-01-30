"""
Generic, schema-driven JSON to UBL document mapper.

This mapper is 100% schema-driven and works with any UBL 2.1 document type.
No hardcoded field names, no Pydantic models. Pure recursive schema-based processing.
"""

from typing import Any, Dict, List

from ..config import get_logger
from ..constants import NUMERIC_TYPE_TO_DOCUMENT_TYPE
from ..exceptions import DocumentTypeError, MappingError

logger = get_logger(__name__)


class JsonMapper:
    """
    Schema-driven generic JSON to UBL document mapper.

    Recursively processes JSON following schema structure with no hardcoded field names.
    Works with ANY UBL 2.1 document type (60+ types).
    """

    def __init__(self, schema_cache: Dict[str, Any] | None = None):
        """
        Initialize mapper with schema cache.

        Args:
            schema_cache: Loaded schema cache dict from schema_cache_builder for a document type
        """
        self.schema_cache = schema_cache or {}
        self._schema_elements = self.schema_cache.get("elements", {})
        self._dropped_fields: List[str] = []
        self._key_cache: Dict[str, Dict[str, str]] = {}  # Cache normalized key mappings

    def map_json_to_document(
        self, raw: Dict[str, Any], document_type: str | None = None
    ) -> tuple[Dict[str, Any], List[str]]:
        """
        Convert raw JSON dict to UBL document dict using SCHEMA-DRIVEN processing.

        Recursively processes JSON following schema structure with no hardcoded field names.
        Works with ANY UBL 2.1 document type.

        Args:
            raw: Raw JSON dictionary (normalized to lowercase keys)
            document_type: Optional override for document type (e.g. "Invoice").
                          If None, extracted from raw['document_type'].

        Returns:
            Tuple of (document_dict, dropped_fields_list)

            Note: dropped_fields_list excludes "document_type" (it's required for processing)
                  and only includes fields that truly couldn't be mapped due to schema mismatch.

        Raises:
            DocumentTypeError: If document_type cannot be determined
            MappingError: If critical schema elements missing
        """
        try:
            # Determine document type
            if document_type is None:
                doc_type_raw = raw.get("document_type")
                if not doc_type_raw:
                    raise DocumentTypeError("Missing 'document_type' field")
                document_type = NUMERIC_TYPE_TO_DOCUMENT_TYPE.get(
                    str(doc_type_raw), str(doc_type_raw)
                )
                logger.debug(f"Mapped document_type '{doc_type_raw}' -> '{document_type}'")

            self._dropped_fields = []

            doc = self._process_json_recursive(raw, self._schema_elements, depth=0)
            doc["document_type"] = document_type
            # Preserve None values to allow empty XML elements (don't filter None)

            # Filter out system fields and known annotations
            filtered_dropped = [
                f
                for f in self._dropped_fields
                if f != "document_type" and f.lower() not in ("annotations", "_metadata")
            ]
            logger.debug(f"Dropped {len(filtered_dropped)} fields not in schema")
            return doc, filtered_dropped

        except (DocumentTypeError, MappingError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in mapping: {e}")
            raise MappingError(f"Unexpected mapping error: {e}") from e

    def _process_json_recursive(
        self, json_obj: Any, schema_spec: Dict[str, Any], depth: int = 0
    ) -> Dict[str, Any]:
        """
        Recursively process JSON following schema structure.

        This is the core schema-driven processor. It:
        - Processes each element defined in the schema
        - Handles cardinality (maxOccurs for arrays vs single elements)
        - Recursively processes nested elements
        - Tracks dropped fields (JSON keys not in schema)

        Args:
            json_obj: JSON value to process (dict, list, or scalar)
            schema_spec: Schema specification for this level (dict of element definitions)
            depth: Current recursion depth

        Returns:
            Processed dict following schema structure
        """
        if depth > 50:
            logger.warning(f"Max recursion depth exceeded at depth {depth}")
            return {}

        if not isinstance(json_obj, dict) or not schema_spec:
            return {}

        result = {}
        json_keys_lower = {k.lower(): k for k in json_obj.keys()}

        # Process each field in schema
        for schema_key_lower, schema_info in schema_spec.items():
            json_key = json_keys_lower.get(schema_key_lower)

            if json_key is None:
                continue

            json_value = json_obj[json_key]

            if json_value is None:
                logger.debug(f"Null value for field '{json_key}' - preserving as empty element")
                result[schema_key_lower] = None
                continue

            max_occurs = schema_info.get("maxOccurs", "1")
            is_array = max_occurs == "unbounded"
            nested_elements = schema_info.get("nested_elements", {})

            if is_array:
                # Array field
                if not isinstance(json_value, list):
                    json_value = [json_value]

                result[schema_key_lower] = [
                    (
                        self._process_json_recursive(item, nested_elements, depth + 1)
                        if isinstance(item, dict) and nested_elements
                        else item
                    )
                    for item in json_value
                ]
            else:
                # Single element
                if isinstance(json_value, dict) and nested_elements:
                    result[schema_key_lower] = self._process_json_recursive(
                        json_value, nested_elements, depth + 1
                    )
                elif isinstance(json_value, list) and json_value:
                    # Take first element if list provided for non-array field
                    result[schema_key_lower] = json_value[0]
                else:
                    result[schema_key_lower] = json_value

        # Track dropped fields (JSON keys not in schema)
        # EXCEPT "document_type" which is a system field, not a schema validation issue
        schema_keys_lower = set(schema_spec.keys())
        json_keys_set = set(json_keys_lower.keys())
        dropped_keys = json_keys_set - schema_keys_lower  # Use set difference instead of loop

        for json_key_lower in dropped_keys:
            original_key = json_keys_lower[json_key_lower]
            # Skip "document_type" as it's required for processing, not a mapping error
            if original_key.lower() != "document_type" and original_key not in self._dropped_fields:
                self._dropped_fields.append(original_key)

        return result
