#!/usr/bin/env python3
"""CLI wrapper for the release preflight version guard."""

from __future__ import annotations

from modelops_core.release_preflight import main

if __name__ == "__main__":
    raise SystemExit(main())
