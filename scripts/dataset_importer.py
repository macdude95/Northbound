#!/usr/bin/env python3
"""
Data processing utilities for the trading suite.
Handles importing and reformatting external CSV data.
"""

import pandas as pd
import os
from datetime import datetime


def process_investing_csv(input_path: str, output_path: str, ticker: str):
    """
    Process CSV files from investing.com format to our standard format.

    Expected input columns: ,Date,Price,Open,High,Low,Vol.,Change %
    Output columns: Date,Open,High,Low,Close,Volume
    """
    # Read CSV, skip the empty first column
    df = pd.read_csv(
        input_path, usecols=["Date", "Price", "Open", "High", "Low", "Vol."]
    )

    # Rename columns
    df = df.rename(columns={"Price": "Close", "Vol.": "Volume"})

    # Convert date format from MM/DD/YYYY to YYYY-MM-DD
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")

    # Clean numeric columns (remove commas and convert to float, then back to string)
    def clean_numeric(value):
        if isinstance(value, str):
            # Remove commas and convert to float then back to string
            return str(float(value.replace(",", "")))
        return str(value)

    # Clean price columns
    for col in ["Close", "Open", "High", "Low"]:
        df[col] = df[col].apply(clean_numeric)

    # Clean volume column (remove 'M', 'K', 'B', convert to float, then back to string)
    def clean_volume(vol):
        if isinstance(vol, str):
            vol = vol.replace(",", "")  # Remove commas first
            if vol.endswith("B"):
                return str(float(vol[:-1]) * 1000000000)
            elif vol.endswith("M"):
                return str(float(vol[:-1]) * 1000000)
            elif vol.endswith("K"):
                return str(float(vol[:-1]) * 1000)
            else:
                return str(float(vol))
        return str(vol)

    df["Volume"] = df["Volume"].apply(clean_volume)

    # Sort by date ascending
    df = df.sort_values("Date").reset_index(drop=True)

    # Save to output path
    df.to_csv(output_path, index=False)
    print(f"Processed {ticker}: {len(df)} rows saved to {output_path}")


def import_single_dataset(input_file: str, ticker: str, datasets_dir: str):
    """Import and process a single CSV dataset."""
    output_path = os.path.join(datasets_dir, "real_tickers", f"{ticker}.csv")

    if os.path.exists(input_file):
        # Automatically merge if ticker data already exists, otherwise create new
        merge_existing = os.path.exists(output_path)
        process_and_merge_investing_csv(input_file, output_path, ticker, merge_existing)
    else:
        print(f"Error: Input file not found: {input_file}")


def process_and_merge_investing_csv(
    input_path: str, output_path: str, ticker: str, merge_existing: bool = False
):
    """Process CSV and merge with existing data if requested."""
    # Process the new data
    new_df = process_investing_csv_to_df(input_path, ticker)

    if merge_existing and os.path.exists(output_path):
        # Load existing data and merge
        existing_df = pd.read_csv(output_path)

        # Combine and remove duplicates, keeping newer data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=["Date"], keep="last")
        combined_df = combined_df.sort_values("Date").reset_index(drop=True)

        combined_df.to_csv(output_path, index=False)
        print(
            f"Merged {len(new_df)} rows with existing {ticker} data (total: {len(combined_df)} rows)"
        )
    else:
        # Just save the new data
        new_df.to_csv(output_path, index=False)
        print(f"Processed {ticker}: {len(new_df)} rows saved to {output_path}")


def process_investing_csv_to_df(input_path: str, ticker: str) -> pd.DataFrame:
    """Process investing.com CSV and return DataFrame (modified from original function)."""
    # Read CSV, skip the empty first column
    df = pd.read_csv(
        input_path, usecols=["Date", "Price", "Open", "High", "Low", "Vol."]
    )

    # Rename columns
    df = df.rename(columns={"Price": "Close", "Vol.": "Volume"})

    # Convert date format from MM/DD/YYYY to YYYY-MM-DD
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")

    # Clean numeric columns (remove commas and convert to float, then back to string)
    def clean_numeric(value):
        if isinstance(value, str):
            # Remove commas and convert to float then back to string
            return str(float(value.replace(",", "")))
        return str(value)

    # Clean price columns
    for col in ["Close", "Open", "High", "Low"]:
        df[col] = df[col].apply(clean_numeric)

    # Clean volume column (remove 'M', 'K', 'B', convert to float, then back to string)
    def clean_volume(vol):
        if isinstance(vol, str):
            vol = vol.replace(",", "")  # Remove commas first
            if vol.endswith("B"):
                return str(float(vol[:-1]) * 1000000000)
            elif vol.endswith("M"):
                return str(float(vol[:-1]) * 1000000)
            elif vol.endswith("K"):
                return str(float(vol[:-1]) * 1000)
            else:
                return str(float(vol))
        return str(vol)

    df["Volume"] = df["Volume"].apply(clean_volume)

    # Sort by date ascending
    df = df.sort_values("Date").reset_index(drop=True)

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import and process trading datasets")
    parser.add_argument("input_file", help="Path to input CSV file")
    parser.add_argument("ticker", help="Ticker symbol for the data")
    args = parser.parse_args()

    # Process the specified dataset
    datasets_dir = "datasets"
    import_single_dataset(args.input_file, args.ticker, datasets_dir)
