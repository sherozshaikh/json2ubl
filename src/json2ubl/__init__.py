from pathlib import Path
from typing import Any, Dict, List

from .config import UblConfig, get_logger
from .converter import Json2UblConverter

logger = get_logger(__name__)
PACKAGE_DIR = Path(__file__).parent


def _ensure_schema_cache_exists() -> None:
    """
    Ensure schema cache directory exists for lazy loading.

    With lazy loading, individual document caches are built on first use.
    This function only ensures the cache directory structure is ready.
    """
    cache_dir = PACKAGE_DIR / "schemas" / "cache"

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Schema cache directory ready for lazy loading")
    except Exception as e:
        logger.error(f"Failed to create schema cache directory: {e}")
        raise


_ensure_schema_cache_exists()


def _load_config(config_path: str | None = None) -> UblConfig:
    """Load configuration from YAML file or use defaults."""
    if config_path:
        return UblConfig.from_yaml(config_path)

    default_config = PACKAGE_DIR / "config" / "ubl_converter.yaml"
    if default_config.exists():
        return UblConfig.from_yaml(str(default_config))

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

    for doc_dict in list_of_dicts:
        response = converter.convert_json_dict_to_xml_dict(doc_dict)

        if response.get("error_response"):
            logger.error(f"Conversion failed: {response['error_response']}")
            return response

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
