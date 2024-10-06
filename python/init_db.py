import sqlite3

def init_db():
    db = sqlite3.connect('database/database.db')
    cur = db.cursor()
    # cur.execute("""
    # DROP TABLE IF EXISTS requests;
    # """)
    cur.execute(
    """
    CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude FLOAT,
                longitude FLOAT,
                track_period VARCHAR(32),
                time_range_start VARCHAR(64),
                time_range_end VARCHAR(64),
                cloud_cover FLOAT,
                notification_frequency_15m BOOLEAN,
                notification_frequency_30m BOOLEAN,
                notification_frequency_1hr BOOLEAN,
                notification_frequency_6hr BOOLEAN,
                notification_frequency_12hr BOOLEAN,
                notification_frequency_1d BOOLEAN,
                notification_frequency_1w BOOLEAN,
                email VARCHAR(128)
    );
    """)
    db.commit()
    cur.close()