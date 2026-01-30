import json
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

from lxml import etree

from .config import UblConfig, get_logger
from .constants import NUMERIC_TYPE_TO_DOCUMENT_TYPE
from .core.mapper import JsonMapper
from .core.serializer import XmlSerializer
from .core.validator import XmlValidator
from .exceptions import DocumentTypeError

logger = get_logger(__name__)


class Json2UblConverter:
    """Convert JSON documents to UBL 2.1 XML for any document type.

    Works with all 60+ UBL 2.1 document types using schema-driven processing.
    """

    def __init__(self, config: UblConfig):
        self.config = config
        # Cache for loaded schema caches per document type
        self._schema_caches: Dict[str, Dict[str, Any]] = {}
        # Lock for thread-safe schema cache access
        self._schema_cache_lock = Lock()
        # Cache for output directory write permissions (path -> is_writable)
        self._output_dir_cache: Dict[str, bool] = {}
        # Lock for thread-safe output directory cache access
        self._output_dir_cache_lock = Lock()
        # Persistent write permission cache file (in logs folder)
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        self._permission_cache_file = logs_dir / "dir_permissions.json"
        self._load_permission_cache()

    def _load_permission_cache(self) -> None:
        """Load persistent write permission cache from file."""
        try:
            if self._permission_cache_file.exists():
                with open(self._permission_cache_file, "r", encoding="utf-8") as f:
                    self._output_dir_cache = json.load(f)
                    logger.debug(
                        f"Loaded permission cache with {len(self._output_dir_cache)} entries"
                    )
        except Exception as err:
            logger.warning(f"Failed to load permission cache: {err}")
            self._output_dir_cache = {}

    def _save_permission_cache(self) -> None:
        """Persist write permission cache to file."""
        try:
            with open(self._permission_cache_file, "w", encoding="utf-8") as f:
                json.dump(self._output_dir_cache, f)
                logger.debug(f"Saved permission cache with {len(self._output_dir_cache)} entries")
        except Exception as err:
            logger.error(f"Failed to save permission cache: {err}")

    def _check_output_dir_writable(self, output_path: Path) -> bool:
        """
        Check if output directory is writable.
        Uses cache for O(1) lookup, writes temp file for new directories.
        """
        path_str = str(output_path.resolve())

        # Check cache without lock first (fast path)
        if path_str in self._output_dir_cache:
            return self._output_dir_cache[path_str]

        # New path: test write permission with single lock acquisition
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            temp_test_file = output_path / ".json2ubl_write_test"
            temp_test_file.write_text("")
            temp_test_file.unlink()
            # Verify file was deleted
            if temp_test_file.exists():
                raise OSError(f"Failed to delete temp test file: {temp_test_file}")
            # Update cache with SINGLE lock (no nested locks)
            with self._output_dir_cache_lock:
                self._output_dir_cache[path_str] = True
                self._save_permission_cache()
            logger.debug(f"Directory writable: {output_path}")
            return True
        except (IOError, OSError, FileNotFoundError) as err:
            logger.error(f"Directory not writable: {output_path}: {err}")
            # Update cache with SINGLE lock (no nested locks)
            with self._output_dir_cache_lock:
                self._output_dir_cache[path_str] = False
                self._save_permission_cache()
            return False

    def _normalize_keys_recursive(self, obj: Any) -> Any:
        """
        Recursively normalize all dict keys to lowercase.
        Handles dicts, lists, and nested structures.
        """
        if isinstance(obj, dict):
            return {k.lower(): self._normalize_keys_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._normalize_keys_recursive(item) for item in obj]
        else:
            return obj

    def _load_schema_cache(self, document_type: str) -> Dict[str, Any]:
        """
        Load and cache schema for a document type (thread-safe).

        Args:
            document_type: UBL document type (e.g., "Invoice")

        Returns:
            Schema cache dict

        Raises:
            FileNotFoundError: If cache file not found
            json.JSONDecodeError: If cache file invalid
        """
        # Check cache without lock first (fast path)
        if document_type in self._schema_caches:
            logger.debug(f"Using cached schema for {document_type}")
            return self._schema_caches[document_type]

        # Acquire lock for loading
        with self._schema_cache_lock:
            # Double-check in case another thread loaded it while we waited
            if document_type in self._schema_caches:
                logger.debug(f"Using cached schema for {document_type} (loaded by another thread)")
                return self._schema_caches[document_type]

            cache_file = (
                Path(self.config.schema_root).parent
                / "cache"
                / f"{document_type}_schema_cache.json"
            )
            if not cache_file.exists():
                logger.error(f"Schema cache missing for {document_type} at {cache_file}")
                raise FileNotFoundError(
                    f"Schema cache not found for {document_type} at {cache_file}"
                )

            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    schema_cache = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in schema cache {cache_file}: {e}")
                raise
            except IOError as e:
                logger.error(f"Failed to read schema cache {cache_file}: {e}")
                raise

            self._schema_caches[document_type] = schema_cache
            logger.debug(f"Loaded schema cache for {document_type}")
            return schema_cache

    def convert_json_dict_to_xml_dict(self, document_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Method 1: Convert single document JSON to XML string dict with metadata.

        Works with ANY UBL 2.1 document type using schema-driven processing.

        Args:
            document_dict: Single document object (from memory/API)

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
                }
            }
        """
        try:
            # Validate input is dict
            if not isinstance(document_dict, dict):
                error_msg = f"Expected dict, got {type(document_dict).__name__}"
                logger.error(f"Validation failed: {error_msg}")
                return {
                    "documents": [],
                    "summary": {
                        "total_inputs": 0,
                        "files_created": 0,
                        "document_types": {},
                    },
                    "error_response": error_msg,
                }

            normalized_dict = self._normalize_keys_recursive(document_dict)
            doc_id = normalized_dict.get("id", "UNKNOWN")
            doc_type_raw = normalized_dict.get("document_type")

            # Validate document_type is present and valid
            if not doc_type_raw:
                exc = DocumentTypeError(
                    "Missing required field: document_type",
                    error_code="MISSING_DOCUMENT_TYPE",
                    details={"doc_id": doc_id, "required_field": "document_type"},
                )
                logger.error(f"Validation failed for {doc_id}: {exc.message}")
                return {
                    "documents": [],
                    "summary": {
                        "total_inputs": 0,
                        "files_created": 0,
                        "document_types": {},
                    },
                    "error_response": exc.to_dict(),
                }

            # Convert numeric type code to document type name
            document_type = NUMERIC_TYPE_TO_DOCUMENT_TYPE.get(str(doc_type_raw))
            if not document_type:
                # Get first 5 codes without full sort (O(n) instead of O(n log n))
                sample_codes = list(NUMERIC_TYPE_TO_DOCUMENT_TYPE.keys())[:5]
                valid_codes = ", ".join(sample_codes) + "..."
                exc = DocumentTypeError(
                    f"Invalid document_type: {doc_type_raw}. Must be numeric code (e.g., 380 for Invoice). Valid codes: {valid_codes}",
                    error_code="INVALID_DOCUMENT_TYPE",
                    details={
                        "doc_id": doc_id,
                        "provided": doc_type_raw,
                        "valid_sample": valid_codes,
                    },
                )
                logger.error(f"Validation failed for {doc_id}: {exc.message}")
                return {
                    "documents": [],
                    "summary": {
                        "total_inputs": 0,
                        "files_created": 0,
                        "document_types": {},
                    },
                    "error_response": exc.to_dict(),
                }

            logger.info(f"Processing {document_type}: {doc_id}")

            # Load schema cache for this document type
            schema_cache = self._load_schema_cache(document_type)
            if not schema_cache:
                logger.warning(f"No schema cache for {document_type}, using generic mode")
                schema_cache = {}

            # Map JSON to document dict using schema
            mapper = JsonMapper(schema_cache)
            doc, dropped_fields = mapper.map_json_to_document(normalized_dict, document_type)

            # Log dropped fields at middleware point (batch into single log)
            if dropped_fields:
                fields_str = ", ".join(dropped_fields)
                logger.warning(
                    f"Dropped fields from input JSON (not in UBL-{document_type}-2.1.xsd): {fields_str}"
                )

            # Serialize to XML using schema
            serializer = XmlSerializer(schema_cache)
            root = serializer.serialize(doc)

            # Validate XML against schema
            try:
                validator = XmlValidator(self.config.schema_root)
                validator.validate(root, document_type)
                logger.debug(f"XML validation passed for {doc_id}")
            except Exception as e:
                # Log validation failure but include in error_response field
                logger.error(f"XML validation failed for {doc_id}: {e}")
                return {
                    "documents": [],
                    "summary": {
                        "total_inputs": 0,
                        "files_created": 0,
                        "document_types": {},
                    },
                    "error_response": f"XML validation failed: {str(e)}",
                }

            # Convert to string with XML declaration
            xml_string = etree.tostring(
                root, encoding="utf-8", pretty_print=True, xml_declaration=True
            ).decode("utf-8")

            logger.info(f"Successfully processed {document_type}: {doc_id}")

            # Return structured response
            return {
                "documents": [
                    {
                        "id": doc_id,
                        "xml": xml_string,
                        "unmapped_fields": dropped_fields,
                    }
                ],
                "summary": {
                    "total_inputs": 1,
                    "files_created": 0,
                    "document_types": {document_type: 1},
                },
                "error_response": None,
            }
        except Exception as e:
            error_msg = f"Failed to convert document: {str(e)}"
            logger.error(error_msg)
            return {
                "documents": [],
                "summary": {
                    "total_inputs": 0,
                    "files_created": 0,
                    "document_types": {},
                },
                "error_response": error_msg,
            }

    def convert_json_file_to_xml_dict(self, json_file_path: str) -> Dict[str, Any]:
        """
        Method 2: Convert JSON file to XML string dict (batch) with metadata.

        Works with ANY UBL 2.1 document type.

        Args:
            json_file_path: Path to JSON file with array of documents

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
                }
            }
        """
        try:
            json_path = Path(json_file_path)
            if not json_path.exists():
                raise FileNotFoundError(f"JSON file not found: {json_file_path}")

            logger.info(f"Reading JSON file: {json_file_path}")
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                data = [data]

            logger.info(f"Found {len(data)} documents in file")

            # Normalize keys once for all pages
            data = [self._normalize_keys_recursive(page) for page in data]

            grouped: Dict[str, List[Dict[str, Any]]] = {}
            skipped_count = 0
            for page in data:
                doc_id = page.get("id")
                if not doc_id:
                    logger.warning("Skipping page without 'id' field")
                    skipped_count += 1
                    continue
                grouped.setdefault(doc_id, []).append(page)

            logger.info(
                f"Grouped into {len(grouped)} unique documents (skipped {skipped_count} without id)"
            )

            documents = []
            document_types: Dict[str, int] = {}

            for doc_id, pages in grouped.items():
                try:
                    # Merge multi-page documents
                    merged = self._merge_pages(pages)

                    # Convert using Method 1
                    response = self.convert_json_dict_to_xml_dict(merged)

                    # Check for errors in response
                    if response.get("error_response"):
                        # Log error but continue processing remaining documents instead of aborting
                        logger.error(
                            f"Failed to convert document {doc_id}: {response.get('error_response')}"
                        )
                        continue

                    # Validate documents list is non-empty
                    if not response.get("documents") or len(response["documents"]) == 0:
                        logger.error(f"No valid documents in response for {doc_id}")
                        continue

                    # Extract and validate document info
                    doc_info = response["documents"][0]
                    if not isinstance(doc_info, dict):
                        logger.error(f"Invalid document info format for {doc_id}")
                        continue
                    documents.append(doc_info)

                    # Track document type
                    doc_type = response["summary"]["document_types"]
                    for dtype, count in doc_type.items():
                        document_types[dtype] = document_types.get(dtype, 0) + count

                except Exception as e:
                    logger.error(f"Failed to convert document {doc_id}: {e}")
                    continue

            logger.info(f"Converted {len(documents)} documents successfully")

            return {
                "documents": documents,
                "summary": {
                    "total_inputs": len(documents),
                    "files_created": 0,
                    "document_types": document_types,
                },
                "error_response": None,
            }
        except Exception as e:
            error_msg = f"Failed to convert JSON file: {str(e)}"
            logger.error(error_msg)
            return {
                "documents": [],
                "summary": {
                    "total_inputs": 0,
                    "files_created": 0,
                    "document_types": {},
                },
                "error_response": error_msg,
            }

    def convert_json_file_to_xml_files(
        self, json_file_path: str, output_dir: str
    ) -> Dict[str, Any]:
        """
        Method 3: Convert JSON file and write XML files to disk.

        Works with ANY UBL 2.1 document type.
        Returns unmapped_fields only (no xml in response).

        Args:
            json_file_path: Path to JSON file
            output_dir: Output directory for XML files

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
                }
            }
        """
        logger.debug(
            f"DEBUG: convert_json_file_to_xml_files() START - json_file={json_file_path}, output={output_dir}"
        )
        try:
            # Check output directory write permissions early
            if not self._check_output_dir_writable(Path(output_dir)):
                error_msg = f"Cannot write to output directory: {output_dir}"
                logger.error(error_msg)
                return {
                    "documents": [],
                    "summary": {
                        "total_inputs": 0,
                        "files_created": 0,
                        "document_types": {},
                    },
                    "error_response": error_msg,
                }

            # Use Method 2 to get XML strings with metadata
            response = self.convert_json_file_to_xml_dict(json_file_path)

            # Check for errors from Method 2
            if response.get("error_response"):
                return response

            # Write to files
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            json_name = Path(json_file_path).stem
            files_created = 0
            documents = []
            created_files = []  # Track files for rollback on failure

            for doc_info in response["documents"]:
                doc_id = "UNKNOWN"
                try:
                    # Validate required fields exist
                    if not isinstance(doc_info, dict) or "id" not in doc_info:
                        raise ValueError(f"Missing 'id' in document: {doc_info}")
                    if "xml" not in doc_info:
                        raise ValueError(f"Missing 'xml' for document {doc_info.get('id')}")
                    if "unmapped_fields" not in doc_info:
                        raise ValueError(
                            f"Missing 'unmapped_fields' for document {doc_info.get('id')}"
                        )

                    doc_id = doc_info["id"]
                    xml_string = doc_info["xml"]
                    unmapped_fields = doc_info["unmapped_fields"]

                    # Validate XML string before writing to disk
                    try:
                        root = etree.fromstring(xml_string.encode("utf-8"))
                        doc_type = root.tag.split("}")[-1]
                        logger.debug(f"XML parsed and validated for {doc_id}")
                    except etree.XMLSyntaxError as xml_err:
                        logger.error(f"Invalid XML syntax for {doc_id}: {xml_err}")
                        raise
                    except Exception as parse_err:
                        logger.error(f"XML parsing failed for {doc_id}: {parse_err}")
                        raise

                    filename = f"{json_name}_{doc_id}_{doc_type}.xml"
                    file_path = output_path / filename

                    # Write to temp file first, then move to final location
                    temp_file_path = file_path.with_suffix(".tmp")
                    try:
                        with open(temp_file_path, "w", encoding="utf-8") as f:
                            f.write(xml_string)
                            logger.debug(f"Wrote temp file {temp_file_path.name}")

                        # Atomic rename with overwrite check (atomic on Unix, check errors on Windows)
                        if file_path.exists():
                            logger.warning(f"Output file exists, overwriting: {file_path}")
                        try:
                            temp_file_path.replace(file_path)
                        except OSError as replace_err:
                            logger.error(f"Failed to move temp file to {file_path}: {replace_err}")
                            raise
                        logger.debug(f"Moved {temp_file_path.name} to {file_path.name}")
                        created_files.append(file_path)  # Track for rollback
                    except IOError as io_err:
                        logger.error(f"File write failed for {doc_id}: {io_err}")
                        if temp_file_path.exists():
                            try:
                                temp_file_path.unlink()
                                logger.debug(f"Cleaned up temp file {temp_file_path}")
                            except Exception as cleanup_err:
                                logger.error(f"Failed to cleanup temp file: {cleanup_err}")
                        raise

                    files_created += 1
                    logger.info(f"Wrote {filename}")

                    # Add to documents list without xml content
                    documents.append(
                        {
                            "id": doc_id,
                            "unmapped_fields": unmapped_fields,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to write XML file for {doc_id}: {e}")
                    # Rollback: delete all previously created files
                    logger.warning(f"Rolling back: deleting {files_created} created files")
                    for created_file in created_files:
                        try:
                            created_file.unlink()
                            logger.debug(f"Rolled back file: {created_file}")
                        except Exception as rollback_err:
                            logger.error(f"Rollback failed for {created_file}: {rollback_err}")
                    raise

            summary = response["summary"]
            summary["files_created"] = files_created

            logger.info(f"Write complete: {files_created} files in {output_dir}")
            return {
                "documents": documents,
                "summary": summary,
                "error_response": None,
            }
        except Exception as e:
            error_msg = f"Failed to write XML files: {str(e)}"
            logger.error(error_msg)
            return {
                "documents": [],
                "summary": {
                    "total_inputs": 0,
                    "files_created": 0,
                    "document_types": {},
                },
                "error_response": error_msg,
            }

    @staticmethod
    def _merge_pages(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multi-page invoice into single object."""
        if not pages:
            return {}

        merged = deepcopy(pages[0])

        # List fields to merge
        list_fields = {
            "invoiceLines",
            "additionalDocumentReferences",
            "globalAllowanceCharges",
            "taxTotal",
        }

        for page in pages[1:]:
            for field in list_fields:
                if field in page and page[field]:
                    merged.setdefault(field, []).extend(page[field])

            # For scalar fields, use LAST non-null value strategy
            # (for multi-page docs, later pages override earlier ones e.g., due_date, payment_terms)
            for key, value in page.items():
                if key not in list_fields and value is not None:
                    merged[key] = value

        return merged
