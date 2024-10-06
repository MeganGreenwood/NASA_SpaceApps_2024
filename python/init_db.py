import sqlite3

def init_db():
    db = sqlite3.connect('database.db')
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
                time_range VARCHAR(64),
                cloud_cover FLOAT,
                notification_frequency_15m BOOLEAN,
                email VARCHAR(128)
    );
    """)
    db.commit()
    cur.close()