import glob
import os
from datetime import datetime, timzone
from google.transit import gtfs_realtime_pb2
import psycopg2

conn =  psycopg2.connect("postgresql://transit_user:transit_password@localhost:5432/transit_db")
cur = conn.cursor()

def get_latest_file(feed_dir):
    files = glob.glob(os.path.join(feed_dir, "*.pb"))
    return max(files, key=os.path.getctime)

def ensure_dim_date(date_id, dt):
    cur.execute(
        """INSERT INTO dim_date (date_id, day_of_week, is_weekend)
           VALUES (%s, %s, %s) ON CONFLICT (date_id) DO NOTHING""",
        (date_id, dt.strftime("%A"), dt.weekday() >= 5)
    )

def load_trip_updates(files_path):
    feed= gtfs_realtime_pb2.FeedMessage()
    ##TBC