"""Custom exception classes for json2ubl converter."""


class Json2UblException(Exception):
    """Base exception for json2ubl errors."""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        """Convert to dict for JSON response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(Json2UblException):
    """Document validation failed."""

    pass


class DocumentTypeError(Json2UblException):
    """Invalid or missing document type."""

    pass


class MappingError(Json2UblException):
    """JSON to schema mapping failed."""

    pass


class SerializationError(Json2UblException):
    """XML serialization failed."""

    pass


class SchemaError(Json2UblException):
    """Schema loading/parsing failed."""

    pass


class FileError(Json2UblException):
    """File I/O error."""

    pass


class PermissionError(Json2UblException):
    """Permission denied (write directory, etc)."""

    pass


class ConfigError(Json2UblException):
    """Configuration error."""

    pass


class CacheError(Json2UblException):
    """Schema cache error."""

    pass
