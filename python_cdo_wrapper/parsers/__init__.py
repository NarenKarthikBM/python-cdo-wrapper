"""Output parsers for v1.0.0+ API."""

from __future__ import annotations

from .base import CDOParser
from .grid import GriddesParser, ZaxisdesParser
from .info import InfoParser, PartabParser, SinfoParser, VlistParser


# Backward compatibility: provide legacy functions
def parse_cdo_output(cmd: str, output: str) -> dict[str, object]:
    """Legacy function for backward compatibility with v0.2.x."""
    # Import the legacy implementation
    import importlib.util
    from pathlib import Path

    parsers_legacy_path = Path(__file__).parent.parent / "parsers.py"
    if parsers_legacy_path.exists():
        spec = importlib.util.spec_from_file_location(
            "parsers_legacy", parsers_legacy_path
        )
        if spec and spec.loader:
            parsers_legacy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parsers_legacy)
            result: dict[str, object] = parsers_legacy.parse_cdo_output(cmd, output)
            return result
    raise NotImplementedError("Legacy parse_cdo_output not available")


def get_supported_structured_commands() -> frozenset[str]:
    """Legacy function for backward compatibility with v0.2.x."""
    import importlib.util
    from pathlib import Path

    parsers_legacy_path = Path(__file__).parent.parent / "parsers.py"
    if parsers_legacy_path.exists():
        spec = importlib.util.spec_from_file_location(
            "parsers_legacy", parsers_legacy_path
        )
        if spec and spec.loader:
            parsers_legacy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parsers_legacy)
            result: frozenset[str] = parsers_legacy.get_supported_structured_commands()
            return result
    return frozenset()


__all__ = [
    "CDOParser",
    "GriddesParser",
    "InfoParser",
    "PartabParser",
    "SinfoParser",
    "VlistParser",
    "ZaxisdesParser",
    "get_supported_structured_commands",
    "parse_cdo_output",
]
