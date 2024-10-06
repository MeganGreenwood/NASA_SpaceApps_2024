import sqlite3

db = sqlite3.connect('database.db')
cur = db.cursor()
cur.execute("""
CREATE TABLE requests (
            latitude FLOAT,
            longitude FLOAT,
            track_period VARCHAR(32),
            time_range VARCHAR(64),
            cloud_cover FLOAT,
            notification_frequency_15m BOOLEAN,
            email VARCHAR(128)
);
""")
cur.close()