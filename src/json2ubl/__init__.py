"""JSON to UBL 2.1 XML converter with schema-driven validation."""

import json
from pathlib import Path
from typing import Any, Dict, List

from .config import UblConfig, get_logger
from .converter import Json2UblConverter

logger = get_logger(__name__)
PACKAGE_DIR = Path(__file__).parent


def _ensure_schema_cache_exists() -> None:
    """
    Check if schema cache exists and is valid; regenerate if missing or corrupted.

    Called at module import to ensure caches are always available for
    schema-based field validation. If cache is missing, invalid, or has empty
    elements, it will be regenerated from XSD files.
    """
    cache_dir = PACKAGE_DIR / "schemas" / "cache"

    try:
        # Check if cache directory exists and has cache files
        if not cache_dir.exists() or not any(cache_dir.glob("*_schema_cache.json")):
            logger.warning("Schema cache not found. Generating from XSD files...")
            from .core.schema_cache_builder import SchemaCacheBuilder

            builder = SchemaCacheBuilder()
            builder.build_all_caches()
            logger.info("Schema cache generated successfully")
            return

        # Check if cache files are valid (have non-empty elements)
        cache_files = list(cache_dir.glob("*_schema_cache.json"))
        invalid_files = []

        for cache_file in cache_files:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    if not cache_data.get("elements"):
                        logger.warning(f"Schema cache {cache_file.name} has empty elements")
                        invalid_files.append(cache_file.name)
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_file.name}: {e}")
                invalid_files.append(cache_file.name)

        # If any invalid files found, regenerate ALL caches once
        if invalid_files:
            logger.warning(
                f"Regenerating cache due to {len(invalid_files)} invalid files: {invalid_files}"
            )
            try:
                from .core.schema_cache_builder import SchemaCacheBuilder

                builder = SchemaCacheBuilder()
                builder.build_all_caches()
                logger.info("Schema cache regenerated successfully")
            except Exception as regen_err:
                logger.error(f"Failed to regenerate cache: {regen_err}")
                raise
            return

    except Exception as e:
        logger.warning(f"Schema cache initialization failed: {e}. Attempting to regenerate...")
        try:
            from .core.schema_cache_builder import SchemaCacheBuilder

            builder = SchemaCacheBuilder()
            builder.build_all_caches()
            logger.info("Schema cache regenerated successfully")
        except Exception as regen_error:
            logger.error(f"Failed to regenerate schema cache: {regen_error}")
            logger.warning(
                "Continuing without schema cache - converter will fail if XSD files unavailable"
            )
            # Don't raise - allow module to load, converter will fail gracefully at runtime


# Initialize schema cache at module import
_ensure_schema_cache_exists()


def _load_config(config_path: str | None = None) -> UblConfig:
    """Load configuration from YAML file or use defaults."""
    if config_path:
        return UblConfig.from_yaml(config_path)

    # Try to load from package default config
    default_config = PACKAGE_DIR / "config" / "ubl_converter.yaml"
    if default_config.exists():
        return UblConfig.from_yaml(str(default_config))

    # Fallback to bundled schemas
    schema_root = str(PACKAGE_DIR / "schemas" / "ubl-2.1")
    return UblConfig(schema_root=schema_root)


def json_dict_to_ubl_xml(
    list_of_dicts: List[Dict[str, Any]],
    config_path: str | None = None,
) -> Dict[str, Any]:
    """
    Method 1: Convert list of JSON dicts to UBL XML strings with metadata.

    Sequential processing - fails on first error.
    Works with ANY UBL 2.1 document type using schema-driven processing.

    Args:
        list_of_dicts: List of document dictionaries to convert
        config_path: Optional path to ubl_converter.yaml config file

    Returns:
        {
            "documents": [
                {
                    "id": "invoice_id",
                    "xml": "xml_string_content",
                    "unmapped_fields": ["field1", "field2"]
                }
            ],
            "summary": {
                "total_inputs": 1,
                "files_created": 0,
                "document_types": {"Invoice": 1}
            },
            "error_response": null or error dict on failure
        }

    Raises:
        MappingError: If JSON structure is invalid
        ValidationError: If XML fails schema validation
    """
    config = _load_config(config_path)
    config.setup_logging()

    converter = Json2UblConverter(config)
    documents = []
    document_types: Dict[str, int] = {}

    # Process sequentially - fail on first error
    for doc_dict in list_of_dicts:
        response = converter.convert_json_dict_to_xml_dict(doc_dict)

        # Early fail on error
        if response.get("error_response"):
            logger.error(f"Conversion failed: {response['error_response']}")
            return response

        # Validate documents list is non-empty
        if not response.get("documents") or len(response["documents"]) == 0:
            error_msg = "No valid documents in conversion response"
            logger.error(error_msg)
            return {
                "documents": [],
                "summary": {
                    "total_inputs": len(list_of_dicts),
                    "files_created": 0,
                    "document_types": {},
                },
                "error_response": error_msg,
            }

        doc_info = response["documents"][0]
        if not isinstance(doc_info, dict):
            error_msg = "Invalid document info format"
            logger.error(error_msg)
            return {
                "documents": [],
                "summary": {
                    "total_inputs": len(list_of_dicts),
                    "files_created": 0,
                    "document_types": {},
                },
                "error_response": error_msg,
            }

        documents.append(doc_info)

        # Track document types
        doc_type = response["summary"]["document_types"]
        for dtype, count in doc_type.items():
            document_types[dtype] = document_types.get(dtype, 0) + count

    return {
        "documents": documents,
        "summary": {
            "total_inputs": len(list_of_dicts),
            "files_created": 0,
            "document_types": document_types,
        },
        "error_response": None,
    }


def json_file_to_ubl_xml_dict(
    json_file_path: str,
    config_path: str | None = None,
) -> Dict[str, Any]:
    """
    Method 2: Convert JSON file to UBL XML strings with metadata (batch).

    Reads JSON file containing array of documents and processes all.

    Args:
        json_file_path: Path to JSON file containing array of documents
        config_path: Optional path to ubl_converter.yaml config file

    Returns:
        {
            "documents": [
                {
                    "id": "invoice_id",
                    "xml": "xml_string_content",
                    "unmapped_fields": ["field1", "field2"]
                }
            ],
            "summary": {
                "total_inputs": 2,
                "files_created": 0,
                "document_types": {"Invoice": 2}
            },
            "error_response": null
        }

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        MappingError: If JSON structure is invalid
        ValidationError: If XML fails schema validation
    """
    config = _load_config(config_path)
    config.setup_logging()

    converter = Json2UblConverter(config)
    response = converter.convert_json_file_to_xml_dict(json_file_path)

    # Ensure error_response field exists
    if "error_response" not in response:
        response["error_response"] = None

    return response


def json_file_to_ubl_xml_files(
    json_file_path: str,
    output_dir: str,
    config_path: str | None = None,
) -> Dict[str, Any]:
    """
    Method 3: Convert JSON file to UBL XML files on disk with metadata.

    Writes XML files to output directory and returns metadata (no XML in response).

    Args:
        json_file_path: Path to JSON file containing array of documents
        output_dir: Directory where XML files will be written
        config_path: Optional path to ubl_converter.yaml config file

    Returns:
        {
            "documents": [
                {
                    "id": "invoice_id",
                    "unmapped_fields": ["field1", "field2"]
                }
            ],
            "summary": {
                "total_inputs": 2,
                "files_created": 2,
                "document_types": {"Invoice": 2}
            },
            "error_response": null
        }

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        MappingError: If JSON structure is invalid
        ValidationError: If XML fails schema validation
    """
    config = _load_config(config_path)
    config.setup_logging()

    converter = Json2UblConverter(config)
    response = converter.convert_json_file_to_xml_files(json_file_path, output_dir)

    # Ensure error_response field exists
    if "error_response" not in response:
        response["error_response"] = None

    return response


__all__ = [
    "json_dict_to_ubl_xml",
    "json_file_to_ubl_xml_dict",
    "json_file_to_ubl_xml_files",
    "Json2UblConverter",
    "UblConfig",
    "get_logger",
]
