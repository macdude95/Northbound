import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


def plot_stock_data():
    # Connect to database
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()

    # Tickers to plot
    tickers = ["SQQQ", "QQQ", "TQQQ"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for i, ticker in enumerate(tickers):
        ax = axes[i]

        # Query data for this ticker
        cursor.execute(
            "SELECT date, close FROM aggregates WHERE ticker = ? ORDER BY date",
            (ticker,),
        )
        data = cursor.fetchall()

        # Extract dates and values
        dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in data]
        values = [row[1] for row in data]

        # Plot the line
        ax.plot(dates, values, linewidth=1, color="blue")

        # Format the subplot
        ax.set_title(f"{ticker} Values Over Time", fontsize=14)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Close Value", fontsize=12)
        ax.grid(True, alpha=0.3)

        # Format x-axis to show years (every 5 years to avoid overlap)
        ax.xaxis.set_major_locator(mdates.YearLocator(base=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()

    # Display the plot
    plt.show()

    conn.close()


if __name__ == "__main__":
    plot_stock_data()
