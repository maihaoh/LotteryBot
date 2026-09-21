import sqlite3
import json

DB_NAME = "lottery.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            issueNumber TEXT PRIMARY KEY,
            number INTEGER NOT NULL,
            colour TEXT NOT NULL,
            size TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            issueNumber TEXT PRIMARY KEY,

            predicted_number INTEGER NOT NULL,

            predicted_size TEXT NOT NULL,

            predicted_colours TEXT NOT NULL,

            actual_number INTEGER,

            actual_size TEXT,

            actual_colours TEXT,

            number_result TEXT,

            size_result TEXT,

            colour_result TEXT,

            checked INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def save_draw(
    issue,
    number,
    colour,
    size
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO draws
        (
            issueNumber,
            number,
            colour,
            size
        )
        VALUES (?, ?, ?, ?)
    """, (
        issue,
        number,
        colour,
        size
    ))

    conn.commit()
    conn.close()


def get_total_draws():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM draws"
    )

    total = cursor.fetchone()[0]

    conn.close()

    return total


def get_all_draws():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            issueNumber,
            number,
            colour,
            size
        FROM draws
        ORDER BY issueNumber ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def save_prediction(
    issue,
    predicted_number,
    predicted_size,
    predicted_colours
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO predictions
        (
            issueNumber,
            predicted_number,
            predicted_size,
            predicted_colours,
            checked
        )
        VALUES (?, ?, ?, ?, 0)
    """, (
        issue,
        predicted_number,
        predicted_size,
        json.dumps(
            predicted_colours,
            ensure_ascii=False
        )
    ))

    conn.commit()
    conn.close()


def get_unchecked_predictions():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            issueNumber,
            predicted_number,
            predicted_size,
            predicted_colours
        FROM predictions
        WHERE checked = 0
        ORDER BY issueNumber ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def update_prediction_result(
    issue,
    actual_number,
    actual_size,
    actual_colours,
    number_result,
    size_result,
    colour_result
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE predictions

        SET
            actual_number = ?,
            actual_size = ?,
            actual_colours = ?,

            number_result = ?,
            size_result = ?,
            colour_result = ?,

            checked = 1

        WHERE issueNumber = ?
    """, (
        actual_number,
        actual_size,

        json.dumps(
            actual_colours,
            ensure_ascii=False
        ),

        number_result,
        size_result,
        colour_result,

        issue
    ))

    conn.commit()
    conn.close()


def get_prediction_stats():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            number_result,
            size_result,
            colour_result
        FROM predictions
        WHERE checked = 1
    """)

    rows = cursor.fetchall()

    conn.close()

    number_win = 0
    number_loss = 0

    size_win = 0
    size_loss = 0

    colour_win = 0
    colour_loss = 0

    for row in rows:

        number_result = row[0]
        size_result = row[1]
        colour_result = row[2]

        if number_result == "WIN":
            number_win += 1

        elif number_result == "LOSS":
            number_loss += 1


        if size_result == "WIN":
            size_win += 1

        elif size_result == "LOSS":
            size_loss += 1


        if colour_result == "WIN":
            colour_win += 1

        elif colour_result == "LOSS":
            colour_loss += 1


    def win_rate(
        win,
        loss
    ):

        total = win + loss

        if total == 0:
            return 0

        return round(
            win / total * 100,
            2
        )


    return {

        "number": {
            "win": number_win,
            "loss": number_loss,
            "total": number_win + number_loss,
            "rate": win_rate(
                number_win,
                number_loss
            )
        },

        "colour": {
            "win": colour_win,
            "loss": colour_loss,
            "total": colour_win + colour_loss,
            "rate": win_rate(
                colour_win,
                colour_loss
            )
        },

        "size": {
            "win": size_win,
            "loss": size_loss,
            "total": size_win + size_loss,
            "rate": win_rate(
                size_win,
                size_loss
            )
        }
    }


def get_latest_checked_prediction():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            issueNumber,
            predicted_number,
            predicted_size,
            predicted_colours,
            actual_number,
            actual_size,
            actual_colours,
            number_result,
            size_result,
            colour_result
        FROM predictions
        WHERE checked = 1
        ORDER BY issueNumber DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    return row
