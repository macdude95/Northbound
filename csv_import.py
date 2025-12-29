import csv
import sqlite3
import sys
from datetime import datetime


def parse_volume(vol_str):
    """Parse volume string like '14.78M' to integer"""
    if not vol_str or vol_str == "":
        return 0

    vol_str = vol_str.strip()
    if vol_str.endswith("M"):
        # Remove 'M' and convert to float, then multiply by 1,000,000
        try:
            return int(float(vol_str[:-1]) * 1000000)
        except ValueError:
            return 0
    elif vol_str.endswith("K"):
        # Remove 'K' and convert to float, then multiply by 1,000
        try:
            return int(float(vol_str[:-1]) * 1000)
        except ValueError:
            return 0
    else:
        # Try to parse as direct integer
        try:
            return int(float(vol_str))
        except ValueError:
            return 0


def import_csv_to_db(csv_file_path, ticker="QQQ"):
    """Import CSV data to database"""

    # Connect to database
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()

    imported_count = 0
    skipped_count = 0

    try:
        with open(csv_file_path, "r", encoding="utf-8") as csvfile:
            # Skip header row
            next(csvfile)

            # Read CSV
            csv_reader = csv.reader(csvfile)

            for row in csv_reader:
                if len(row) < 6:
                    continue

                date_str, price_str, open_str, high_str, low_str, vol_str = row[:6]

                # Convert date from MM/DD/YYYY to YYYY-MM-DD
                try:
                    date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    print(f"Invalid date format: {date_str}")
                    continue

                # Parse OHLC values
                try:
                    open_val = float(open_str.replace(",", "")) if open_str else None
                    high_val = float(high_str.replace(",", "")) if high_str else None
                    low_val = float(low_str.replace(",", "")) if low_str else None
                    close_val = float(price_str.replace(",", "")) if price_str else None
                    volume_val = parse_volume(vol_str)
                except ValueError as e:
                    print(f"Error parsing values for date {date_str}: {e}")
                    continue

                # Insert or ignore (skip duplicates)
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO aggregates
                        (ticker, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            ticker.upper(),
                            formatted_date,
                            open_val,
                            high_val,
                            low_val,
                            close_val,
                            volume_val,
                        ),
                    )

                    if cursor.rowcount > 0:
                        imported_count += 1
                    else:
                        skipped_count += 1

                except sqlite3.Error as e:
                    print(f"Database error for date {formatted_date}: {e}")

        conn.commit()

    except FileNotFoundError:
        print(f"File not found: {csv_file_path}")
        return
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    finally:
        conn.close()

    print(
        f"Import complete: {imported_count} records imported, {skipped_count} duplicates skipped"
    )


def main():
    if len(sys.argv) != 3:
        print("Usage: python csv_import.py <TICKER> <CSV_PATH>")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    csv_path = sys.argv[2]
    import_csv_to_db(csv_path, ticker)


if __name__ == "__main__":
    main()
