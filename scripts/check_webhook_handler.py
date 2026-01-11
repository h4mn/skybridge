#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify webhook handler is registered.

Usage:
    python scripts/check_webhook_handler.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    """Check if webhook handler is registered."""
    from skybridge.kernel import get_query_registry
    from skybridge.platform.config.config import get_discovery_config
    from skybridge.kernel.registry.discovery import discover_modules

    print("=" * 60)
    print("  Webhook Handler Registration Check")
    print("=" * 60)
    print()

    # Load discovery config
    discovery_config = get_discovery_config()
    print(f"Discovery packages: {discovery_config.packages}")
    print()

    # Run discovery
    print("Running module discovery...")
    modules = discover_modules(
        discovery_config.packages,
        include_submodules=discovery_config.include_submodules,
    )
    print(f"Discovered modules: {modules}")
    print()

    # Get registry
    registry = get_query_registry()
    all_handlers = registry.list_all()
    print(f"Total handlers registered: {len(all_handlers)}")
    print()

    # Check for webhook handler
    webhook_handler = registry.get("webhooks.github.receive")

    if webhook_handler:
        print("✅ SUCCESS: Handler 'webhooks.github.receive' is registered!")
        print(f"   Description: {webhook_handler.description}")
        print(f"   Kind: {webhook_handler.kind}")
        print(f"   Module: {getattr(webhook_handler, 'module', 'unknown')}")
    else:
        print("❌ ERROR: Handler 'webhooks.github.receive' NOT found!")
        print()
        print("Registered handlers:")
        for name in sorted(all_handlers.keys()):
            print(f"  - {name}")

    print()
    print("=" * 60)

    return 0 if webhook_handler else 1


if __name__ == "__main__":
    sys.exit(main())
