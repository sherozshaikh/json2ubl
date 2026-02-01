import json
from pathlib import Path

import pytest


@pytest.fixture
def test_files_dir():
    """Return test files directory path."""
    return Path(__file__).parent.parent / "test_files"


@pytest.fixture
def invoice_dict():
    """Load invoice test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "invoice.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data


@pytest.fixture
def credit_note_dict():
    """Load credit note test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "credit_note.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data


@pytest.fixture
def debit_note_dict():
    """Load debit note test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "debit_note.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data


@pytest.fixture
def self_billed_invoice_dict():
    """Load self-billed invoice test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "self_billed_invoice.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data


@pytest.fixture
def self_billed_credit_note_dict():
    """Load self-billed credit note test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "self_billed_credit_note.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data


@pytest.fixture
def freight_invoice_dict():
    """Load freight invoice test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "freight_invoice.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data


@pytest.fixture
def invalid_doctype_dict():
    """Load invalid document type test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "invoice_invalid_doctype.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data


@pytest.fixture
def missing_doctype_dict():
    """Load missing document type test data."""
    test_files_path = Path(__file__).parent.parent / "test_files" / "invoice_missing_doctype.json"
    data = json.loads(test_files_path.read_text())
    return data[0] if isinstance(data, list) else data
