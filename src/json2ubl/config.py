from dataclasses import dataclass
from pathlib import Path

import yaml
from loguru import logger as _logger


@dataclass(frozen=True)
class UblConfig:
    schema_root: str
    log_level: str = "DEBUG"
    log_file: str = "json2ubl.log"
    cache_dir: str = ".json2ubl_cache"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "UblConfig":
        """Load config from YAML file."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            schema_root=data.get("schema_root", "schemas/ubl-2.1"),
            log_level=data.get("log_level", "DEBUG"),
            log_file=data.get("log_file", "json2ubl.log"),
            cache_dir=data.get("cache_dir", ".json2ubl_cache"),
        )

    def setup_logging(self) -> None:
        """Configure loguru with file and console output."""
        _logger.remove()
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        _logger.add(
            str(log_path),
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        )
        _logger.add(
            lambda msg: print(msg, end=""),
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        )


def get_logger(name: str):
    """Get logger instance."""
    return _logger.bind(name=name)
