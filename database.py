import sqlite3

DB_NAME = "lottery.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            issueNumber TEXT PRIMARY KEY,
            number INTEGER NOT NULL,
            colour TEXT NOT NULL,
            size TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_draw(issue, number, colour, size):
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO draws
        (issueNumber, number, colour, size)
        VALUES (?, ?, ?, ?)
    """, (issue, number, colour, size))

    conn.commit()
    conn.close()


def get_total_draws():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM draws")

    total = cursor.fetchone()[0]

    conn.close()

    return total