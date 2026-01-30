"""Test fixtures and configuration."""

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
    return json.loads(Path("test_files/invoice.json").read_text())


@pytest.fixture
def credit_note_dict():
    """Load credit note test data."""
    return json.loads(Path("test_files/credit_note.json").read_text())


@pytest.fixture
def debit_note_dict():
    """Load debit note test data."""
    return json.loads(Path("test_files/debit_note.json").read_text())


@pytest.fixture
def self_billed_invoice_dict():
    """Load self-billed invoice test data."""
    return json.loads(Path("test_files/self_billed_invoice.json").read_text())


@pytest.fixture
def self_billed_credit_note_dict():
    """Load self-billed credit note test data."""
    return json.loads(Path("test_files/self_billed_credit_note.json").read_text())


@pytest.fixture
def freight_invoice_dict():
    """Load freight invoice test data."""
    return json.loads(Path("test_files/freight_invoice.json").read_text())


@pytest.fixture
def invalid_doctype_dict():
    """Load invalid document type test data."""
    return json.loads(Path("test_files/invoice_invalid_doctype.json").read_text())


@pytest.fixture
def missing_doctype_dict():
    """Load missing document type test data."""
    return json.loads(Path("test_files/invoice_missing_doctype.json").read_text())
