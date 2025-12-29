import sqlite3


def init_database():
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()

    # Create table for stock aggregates
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS aggregates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            UNIQUE(ticker, date)
        )
    """
    )

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_database()
