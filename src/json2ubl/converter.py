import gc
import json
from pathlib import Path
from typing import Any, Dict, List

from lxml import etree

from .config import UblConfig, get_logger
from .core.mapper import JsonMapper
from .core.serializer import XmlSerializer
from .core.validator import XmlValidator

logger = get_logger(__name__)


class Json2UblConverter:
    """Convert JSON invoices to UBL 2.1 XML documents."""

    def __init__(self, config: UblConfig):
        self.config = config
        self.mapper = JsonMapper()
        self.serializer = XmlSerializer()
        self.validator = XmlValidator(config.schema_root)

    def convert_json_dict_to_xml_dict(self, invoice_dict: Dict[str, Any]) -> Dict[str, str]:
        """
        Method 1: Convert single invoice JSON to XML string dict.

        Args:
            invoice_dict: Single invoice object (from memory/API)

        Returns:
            {invoice_id: xml_string}
        """
        try:
            invoice_id = invoice_dict.get("id", "UNKNOWN")
            logger.info(f"Processing Invoice: {invoice_id}")

            # Map JSON to Pydantic model (returns tuple with dropped fields)
            doc, dropped_fields = self.mapper.map_json_to_document(invoice_dict)

            # Log dropped fields at middleware point (Option A: Per-Document Summary)
            if dropped_fields:
                doc_type = doc.document_type or "Invoice"
                logger.warning(f"Dropped fields from input JSON (not in UBL-{doc_type}-2.1.xsd):")
                for field in dropped_fields:
                    logger.warning(f"  - {field}")

            # Serialize to XML
            root = self.serializer.serialize(doc)

            # Validate (optional - log warnings but don't fail)
            try:
                self.validator.validate(root, doc.document_type or "Invoice")
            except Exception as e:
                logger.warning(f"XML validation warning for {doc.id}: {e}")

            # Convert to string with XML declaration added manually
            xml_string = etree.tostring(
                root, encoding="utf-8", pretty_print=True, xml_declaration=True
            ).decode("utf-8")

            result = {doc.id: xml_string}
            logger.info(f"Successfully processed Invoice: {doc.id}")

            del doc, root
            gc.collect()

            return result
        except Exception as e:
            logger.error(f"Failed to convert invoice: {e}")
            raise

    def convert_json_file_to_xml_dict(self, json_file_path: str) -> Dict[str, str]:
        """
        Method 2: Convert JSON file to XML string dict (batch).

        Args:
            json_file_path: Path to JSON file with array of invoices

        Returns:
            {invoice_id_1: xml_string_1, invoice_id_2: xml_string_2, ...}
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

            logger.info(f"Found {len(data)} invoices in file")

            # Group by invoice ID
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for page in data:
                inv_id = page.get("id")
                if not inv_id:
                    logger.warning("Skipping page without 'id' field")
                    continue
                grouped.setdefault(inv_id, []).append(page)

            logger.info(f"Grouped into {len(grouped)} unique invoices")

            result = {}
            for inv_id, pages in grouped.items():
                try:
                    # Merge multi-page invoices
                    merged = self._merge_pages(pages)

                    # Convert using Method 1
                    xml_dict = self.convert_json_dict_to_xml_dict(merged)
                    result.update(xml_dict)
                except Exception as e:
                    logger.error(f"Failed to convert invoice {inv_id}: {e}")
                    raise

            logger.info(f"Converted {len(result)} invoices successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to convert JSON file: {e}")
            raise

    def convert_json_file_to_xml_files(
        self, json_file_path: str, output_dir: str
    ) -> Dict[str, Any]:
        """
        Method 3: Convert JSON file and write XML files to disk.

        Args:
            json_file_path: Path to JSON file
            output_dir: Output directory for XML files

        Returns:
            {
                "json_file": str,
                "output_dir": str,
                "total_invoices": int,
                "files_created": int,
                "document_types": {type: count}
            }
        """
        try:
            # Use Method 2 to get XML strings
            xml_dict = self.convert_json_file_to_xml_dict(json_file_path)

            # Write to files
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            json_name = Path(json_file_path).stem
            document_types: Dict[str, int] = {}
            files_created = 0

            for inv_id, xml_string in xml_dict.items():
                try:
                    # Parse to get document type for filename
                    root = etree.fromstring(xml_string.encode("utf-8"))
                    doc_type = root.tag.split("}")[-1]  # Extract tag name

                    filename = f"{json_name}_{inv_id}_{doc_type}.xml"
                    file_path = output_path / filename

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(xml_string)

                    files_created += 1
                    document_types[doc_type] = document_types.get(doc_type, 0) + 1
                    logger.info(f"Wrote {filename}")

                    del root
                except Exception as e:
                    logger.error(f"Failed to write XML file for {inv_id}: {e}")
                    raise

            summary = {
                "json_file": str(json_file_path),
                "output_dir": str(output_dir),
                "total_invoices": len(xml_dict),
                "files_created": files_created,
                "document_types": document_types,
            }

            logger.info(f"Write complete: {files_created} files in {output_dir}")
            return summary
        except Exception as e:
            logger.error(f"Failed to write XML files: {e}")
            raise

    @staticmethod
    def _merge_pages(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multi-page invoice into single object."""
        if not pages:
            return {}

        merged = dict(pages[0])

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

            # For scalar fields, use first non-null
            for key, value in page.items():
                if key not in list_fields and merged.get(key) is None and value is not None:
                    merged[key] = value

        return merged
