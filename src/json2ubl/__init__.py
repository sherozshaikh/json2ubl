"""JSON to UBL 2.1 XML converter with schema-driven validation."""

from pathlib import Path
from typing import Any, Dict

from .config import UblConfig, get_logger
from .converter import Json2UblConverter

logger = get_logger(__name__)
PACKAGE_DIR = Path(__file__).parent


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
    invoice_dict: Dict[str, Any],
    config_path: str | None = None,
) -> Dict[str, str]:
    """
    Method 1: Convert single invoice JSON dict to UBL XML string.

    Args:
        invoice_dict: Single invoice object
        config_path: Optional path to ubl_converter.yaml config file

    Returns:
        {invoice_id: xml_string}

    Raises:
        MappingError: If JSON structure is invalid
        ValidationError: If XML fails schema validation
    """
    config = _load_config(config_path)
    config.setup_logging()

    converter = Json2UblConverter(config)
    return converter.convert_json_dict_to_xml_dict(invoice_dict)


def json_file_to_ubl_xml_dict(
    json_file_path: str,
    config_path: str | None = None,
) -> Dict[str, str]:
    """
    Method 2: Convert JSON file to dict of UBL XML strings (batch).

    Args:
        json_file_path: Path to JSON file containing array of invoices
        config_path: Optional path to ubl_converter.yaml config file

    Returns:
        {invoice_id_1: xml_string_1, invoice_id_2: xml_string_2, ...}

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        MappingError: If JSON structure is invalid
        ValidationError: If XML fails schema validation
    """
    config = _load_config(config_path)
    config.setup_logging()

    converter = Json2UblConverter(config)
    return converter.convert_json_file_to_xml_dict(json_file_path)


def json_file_to_ubl_xml_files(
    json_file_path: str,
    output_dir: str,
    config_path: str | None = None,
) -> Dict[str, Any]:
    """
    Method 3: Convert JSON file to UBL XML files on disk.

    Args:
        json_file_path: Path to JSON file containing array of invoices
        output_dir: Directory where XML files will be written
        config_path: Optional path to ubl_converter.yaml config file

    Returns:
        {
            "json_file": str,
            "output_dir": str,
            "total_invoices": int,
            "files_created": int,
            "document_types": {type: count}
        }

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        MappingError: If JSON structure is invalid
        ValidationError: If XML fails schema validation
    """
    config = _load_config(config_path)
    config.setup_logging()

    converter = Json2UblConverter(config)
    return converter.convert_json_file_to_xml_files(json_file_path, output_dir)


__all__ = [
    "json_dict_to_ubl_xml",
    "json_file_to_ubl_xml_dict",
    "json_file_to_ubl_xml_files",
    "Json2UblConverter",
    "UblConfig",
    "get_logger",
]
