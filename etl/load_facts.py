import glob
import os
from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2
import psycopg2

conn = psycopg2.connect("postgresql://transit_user:transit_password@localhost:5432/transit_db")
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

def load_trip_updates(file_path):
    feed = gtfs_realtime_pb2.FeedMessage()
    with open(file_path, "rb") as f:
        feed.ParseFromString(f.read())

    poll_ts = datetime.now(timezone.utc)
    date_id = int(poll_ts.strftime("%Y%m%d"))
    ensure_dim_date(date_id, poll_ts)

    rows_inserted = 0
    rows_skipped = 0

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update.trip
        trip_id = trip.trip_id
        route_id = trip.route_id

        for stu in entity.trip_update.stop_time_update:
            stop_id = stu.stop_id
            stop_sequence = stu.stop_sequence

            arrival_delay = stu.arrival.delay if stu.HasField("arrival") else None
            arrival_time = stu.arrival.time if stu.HasField("arrival") else None

            # Skip rows with zero signal (no arrival AND no departure)
            if not stu.HasField("arrival") and not stu.HasField("departure"):
                rows_skipped += 1
                continue

            cur.execute(
                """INSERT INTO fact_trip_stop_delay
                   (trip_id, route_id, stop_id, date_id, stop_sequence,
                    delay_seconds, predicted_arrival, poll_timestamp)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (trip_id, route_id, stop_id, date_id, stop_sequence,
                 arrival_delay,
                 datetime.fromtimestamp(arrival_time, tz=timezone.utc) if arrival_time else None,
                 poll_ts)
            )
            rows_inserted += 1

    conn.commit()
    print(f"Inserted {rows_inserted} rows, skipped {rows_skipped} (no arrival/departure)")

if __name__ == "__main__":
    latest_file = get_latest_file("raw/trip_updates")
    load_trip_updates(latest_file)
    cur.close()
    conn.close()