#!/usr/bin/env python3
"""
Backfill historical data using Polygon.io API.
Standalone script for data management.
"""

import argparse
import sys
import os

# Add src directory to path so we can import northbound package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from northbound.data_utils import backfill_all_tickers


def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(
        description="Backfill historical data using Polygon.io API"
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data",
        help="Path to data directory (default: data)",
    )
    parser.add_argument(
        "--tickers", nargs="*", help="Specific tickers to backfill (default: all)"
    )

    args = parser.parse_args()

    backfill_all_tickers(args.data_dir, args.tickers)


if __name__ == "__main__":
    main()
