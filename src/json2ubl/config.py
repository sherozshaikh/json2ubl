import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml
from loguru import logger as _logger


@dataclass(frozen=True)
class UblConfig:
    schema_root: str
    log_level: str = "DEBUG"
    log_file: str = "json2ubl.log"
    log_format: str = "json"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "UblConfig":
        """Load config from YAML file."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            schema_root=data.get("schema_root", "schemas/ubl-2.1"),
            log_level=data.get("log_level", "DEBUG"),
            log_file=data.get("log_file", "json2ubl.log"),
            log_format=data.get("log_format", "json"),
        )

    def setup_logging(self) -> None:
        """Configure loguru with file and console output in logs folder."""
        _logger.remove()

        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"json2ubl_{timestamp}.log"
        log_path = logs_dir / log_filename

        _logger.add(
            str(log_path),
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            mode="a",
            rotation="100 MB",
            retention="30 days",
        )

        _logger.add(
            sys.stderr,
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        )


def get_logger(name: str):
    """Get logger instance."""
    return _logger.bind(name=name)
