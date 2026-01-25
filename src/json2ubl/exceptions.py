class Json2UblError(Exception):
    """Base exception for json2ubl package."""
    pass


class ConfigError(Json2UblError):
    """Configuration error."""
    pass


class SchemaError(Json2UblError):
    """Schema validation/parsing error."""
    pass


class MappingError(Json2UblError):
    """JSON to UBL mapping error."""
    pass


class ValidationError(Json2UblError):
    """XML validation error."""
    pass


class DocumentTypeError(Json2UblError):
    """Invalid or unsupported document type."""
    pass
