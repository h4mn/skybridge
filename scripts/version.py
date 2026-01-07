# -*- coding: utf-8 -*-
"""
Version reader for Skybridge project.

Reads version information from the VERSION file (single source of truth).
This module provides utilities to access version strings programmatically.

Usage:
    from scripts.version import get_version

    skybridge_version = get_version("SKYBRIDGE_VERSION")
    kernel_version = get_version("KERNEL_API_VERSION")
"""

import os
from pathlib import Path
from typing import Dict, Optional


# Path to VERSION file (relative to project root)
_VERSION_FILE = Path(__file__).parent.parent / "VERSION"


def _read_version_file() -> Dict[str, str]:
    """
    Read and parse the VERSION file.

    Returns:
        Dictionary mapping component names to version strings.

    Raises:
        FileNotFoundError: If VERSION file doesn't exist
        ValueError: If VERSION file is malformed
    """
    if not _VERSION_FILE.exists():
        raise FileNotFoundError(
            f"VERSION file not found at {_VERSION_FILE}. "
            "Please create it with the format: KEY=VALUE"
        )

    versions = {}
    with open(_VERSION_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                versions[key.strip()] = value.strip()

    if not versions:
        raise ValueError(
            f"VERSION file is empty or contains no valid entries: {_VERSION_FILE}"
        )

    return versions


def get_version(component: str, default: Optional[str] = None) -> str:
    """
    Get version string for a specific component.

    Args:
        component: Component name (e.g., "SKYBRIDGE_VERSION")
        default: Default value if component not found (raises if None)

    Returns:
        Version string (e.g., "0.1.0")

    Raises:
        ValueError: If component not found and no default provided
        FileNotFoundError: If VERSION file doesn't exist
    """
    versions = _read_version_file()

    if component not in versions:
        if default is not None:
            return default
        raise ValueError(
            f"Component '{component}' not found in VERSION file. "
            f"Available: {', '.join(versions.keys())}"
        )

    return versions[component]


def get_all_versions() -> Dict[str, str]:
    """
    Get all version strings from VERSION file.

    Returns:
        Dictionary mapping all component names to version strings.
    """
    return _read_version_file()


def get_skybridge_version() -> str:
    """Get Skybridge application version."""
    return get_version("SKYBRIDGE_VERSION")


def get_kernel_api_version() -> str:
    """Get Kernel API version."""
    return get_version("KERNEL_API_VERSION")


def get_openapi_contract_version() -> str:
    """Get OpenAPI contract version."""
    return get_version("OPENAPI_CONTRACT_VERSION")


# Allow running as script
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        component = sys.argv[1]
        try:
            version = get_version(component)
            print(version)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Print all versions
        for key, value in get_all_versions().items():
            print(f"{key}={value}")
