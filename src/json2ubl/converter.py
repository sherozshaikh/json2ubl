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
        self._schema_caches: Dict[str, Dict[str, Any]] = {}
        self._schema_cache_lock = Lock()
        self._output_dir_cache: Dict[str, bool] = {}
        self._output_dir_cache_lock = Lock()
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
        if path_str in self._output_dir_cache:
            return self._output_dir_cache[path_str]

        try:
            output_path.mkdir(parents=True, exist_ok=True)
            temp_test_file = output_path / ".json2ubl_write_test"
            temp_test_file.write_text("")
            temp_test_file.unlink()
            if temp_test_file.exists():
                raise OSError(f"Failed to delete temp test file: {temp_test_file}")
            with self._output_dir_cache_lock:
                self._output_dir_cache[path_str] = True
                self._save_permission_cache()
            logger.debug(f"Directory writable: {output_path}")
            return True
        except (IOError, OSError, FileNotFoundError) as err:
            logger.error(f"Directory not writable: {output_path}: {err}")
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
        if document_type in self._schema_caches:
            logger.debug(f"Using cached schema for {document_type}")
            return self._schema_caches[document_type]

        with self._schema_cache_lock:
            if document_type in self._schema_caches:
                logger.debug(f"Using cached schema for {document_type} (loaded by another thread)")
                return self._schema_caches[document_type]

            schema_root = Path(self.config.schema_root)
            if not schema_root.is_absolute():
                src_dir = Path(__file__).parent.parent.parent
                schema_root = src_dir / self.config.schema_root

            cache_file = schema_root.parent / "cache" / f"{document_type}_schema_cache.json"

            if not cache_file.exists():
                logger.info(f"Cache not found for {document_type}. Building on-demand...")
                try:
                    from .core.schema_cache_builder import SchemaCacheBuilder

                    builder = SchemaCacheBuilder(str(schema_root))
                    builder.build_cache_for_document(document_type)
                    logger.info(f"Built cache for {document_type}")
                except Exception as e:
                    logger.error(f"Failed to build cache for {document_type}: {e}")
                    raise

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

            document_type = NUMERIC_TYPE_TO_DOCUMENT_TYPE.get(str(doc_type_raw))
            if not document_type:
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

            schema_cache = self._load_schema_cache(document_type)
            if not schema_cache:
                logger.warning(f"No schema cache for {document_type}, using generic mode")
                schema_cache = {}

            mapper = JsonMapper(schema_cache)
            doc, dropped_fields = mapper.map_json_to_document(normalized_dict, document_type)

            if dropped_fields:
                fields_str = ", ".join(dropped_fields)
                logger.warning(
                    f"Dropped fields from input JSON (not in UBL-{document_type}-2.1.xsd): {fields_str}"
                )

            serializer = XmlSerializer(schema_cache)
            root = serializer.serialize(doc)

            validation_errors = []
            try:
                validator = XmlValidator(self.config.schema_root)
                validator.validate(root, document_type)
                logger.debug(f"XML validation passed for {doc_id}")
            except Exception as e:
                error_msg = str(e).split("\n")[0] if "\n" in str(e) else str(e)
                logger.warning(f"XML validation failed for {doc_id}: {error_msg}")
                validation_errors.append(error_msg)

                try:
                    schema_doc = etree.parse(
                        str(
                            Path(self.config.schema_root)
                            / "maindoc"
                            / f"UBL-{document_type}-2.1.xsd"
                        )
                    )
                    schema = etree.XMLSchema(schema_doc)
                    schema.validate(root)
                    for i, err in enumerate(schema.error_log[:10]):
                        logger.debug(f"  Error {i + 1}: {err}")
                except Exception as debug_err:
                    logger.debug(f"Failed to get detailed validation errors: {debug_err}")

            xml_string = etree.tostring(
                root, encoding="utf-8", pretty_print=True, xml_declaration=True
            ).decode("utf-8")

            logger.info(f"Successfully processed {document_type}: {doc_id}")

            return {
                "documents": [
                    {
                        "id": doc_id,
                        "xml": xml_string,
                        "unmapped_fields": dropped_fields,
                        "validation_errors": (validation_errors if validation_errors else None),
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

            merged_docs = self._group_and_merge_documents(data)
            logger.info(f"Grouped into {len(merged_docs)} unique documents")

            documents = []
            document_types: Dict[str, int] = {}
            first_error_response = None

            for merged in merged_docs:
                try:
                    doc_id = merged.get("id", "UNKNOWN")
                    response = self.convert_json_dict_to_xml_dict(merged)

                    if response.get("error_response"):
                        if first_error_response is None:
                            first_error_response = response.get("error_response")
                        logger.error(
                            f"Failed to convert document {doc_id}: {response.get('error_response')}"
                        )
                        continue

                    if not response.get("documents") or len(response["documents"]) == 0:
                        logger.error(f"No valid documents in response for {doc_id}")
                        continue

                    doc_info = response["documents"][0]
                    if not isinstance(doc_info, dict):
                        logger.error(f"Invalid document info format for {doc_id}")
                        continue
                    documents.append(doc_info)

                    doc_type = response["summary"]["document_types"]
                    for dtype, count in doc_type.items():
                        document_types[dtype] = document_types.get(dtype, 0) + count

                except Exception as e:
                    logger.error(f"Failed to convert document {doc_id}: {e}")
                    if first_error_response is None:
                        first_error_response = str(e)
                    continue

            logger.info(f"Converted {len(documents)} documents successfully")

            if not documents and first_error_response:
                return {
                    "documents": [],
                    "summary": {
                        "total_inputs": 0,
                        "files_created": 0,
                        "document_types": {},
                    },
                    "error_response": first_error_response,
                }

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

            response = self.convert_json_file_to_xml_dict(json_file_path)

            if response.get("error_response"):
                return response

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            json_name = Path(json_file_path).stem
            files_created = 0
            documents = []
            created_files = []

            for doc_info in response["documents"]:
                doc_id = "UNKNOWN"
                try:
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

                    temp_file_path = file_path.with_suffix(".tmp")
                    try:
                        with open(temp_file_path, "w", encoding="utf-8") as f:
                            f.write(xml_string)
                            logger.debug(f"Wrote temp file {temp_file_path.name}")

                        if file_path.exists():
                            logger.warning(f"Output file exists, overwriting: {file_path}")
                        try:
                            temp_file_path.replace(file_path)
                        except OSError as replace_err:
                            logger.error(f"Failed to move temp file to {file_path}: {replace_err}")
                            raise
                        logger.debug(f"Moved {temp_file_path.name} to {file_path.name}")
                        created_files.append(file_path)
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

                    documents.append(
                        {
                            "id": doc_id,
                            "unmapped_fields": unmapped_fields,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to write XML file for {doc_id}: {e}")

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

    def _group_and_merge_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group documents by ID and merge pages with same ID.

        Args:
            documents: List of document dictionaries (potentially with duplicate IDs)

        Returns:
            List of merged documents (one per unique ID)
        """
        if not documents:
            return []

        documents = [self._normalize_keys_recursive(doc) for doc in documents]

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for doc in documents:
            doc_id = doc.get("id")
            if not doc_id:
                logger.warning("Skipping document without 'id' field")
                continue
            grouped.setdefault(doc_id, []).append(doc)

        merged_documents = []
        for doc_id, pages in grouped.items():
            try:
                doc_type_raw = pages[0].get("document_type")
                document_type = NUMERIC_TYPE_TO_DOCUMENT_TYPE.get(str(doc_type_raw))

                schema_cache = {}
                if document_type:
                    schema_cache = self._load_schema_cache(document_type)

                merged = self._merge_pages(pages, schema_cache)
                merged_documents.append(merged)
            except Exception as e:
                logger.error(f"Failed to merge document {doc_id}: {e}")
                continue

        return merged_documents

    @staticmethod
    def _merge_pages(
        pages: List[Dict[str, Any]], schema_cache: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Merge multi-page invoice into single object.

        Args:
            pages: List of document pages (dictionaries)
            schema_cache: Schema cache to identify array fields dynamically

        Returns:
            Merged document dictionary
        """
        if not pages:
            return {}

        merged = deepcopy(pages[0])

        array_fields = set()
        if schema_cache and "elements" in schema_cache:
            for field_lower, field_info in schema_cache["elements"].items():
                if isinstance(field_info, dict) and field_info.get("maxOccurs") == "unbounded":
                    array_fields.add(field_lower)

        for page in pages[1:]:
            page_keys_lower = {k.lower(): k for k in page.keys()}

            for field_lower in array_fields:
                original_key = page_keys_lower.get(field_lower)
                if original_key and page.get(original_key):
                    merged_keys_lower = {k.lower(): k for k in merged.keys()}
                    merged_key_original = merged_keys_lower.get(field_lower)

                    if merged_key_original:
                        if not isinstance(merged[merged_key_original], list):
                            merged[merged_key_original] = [merged[merged_key_original]]
                        if isinstance(page[original_key], list):
                            merged[merged_key_original].extend(page[original_key])
                        else:
                            merged[merged_key_original].append(page[original_key])
                    else:
                        if isinstance(page[original_key], list):
                            merged[original_key] = page[original_key]
                        else:
                            merged[original_key] = [page[original_key]]

            for key, value in page.items():
                key_lower = key.lower()
                if key_lower not in array_fields and value is not None:
                    merged[key] = value

        return merged
