import json
import psycopg2

conn = psycopg2.connect("postgresql://transit_user:transit_password@localhost:5432/transit_db")
cur = conn.cursor()

# Current-conditions snapshot: aggregate across trips seen in the single most
# recent poll only. This is "delay right now", not a multi-day trend.
cur.execute(
    """
    WITH latest AS (SELECT MAX(poll_timestamp) AS ts FROM fact_trip_stop_delay)
    SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon,
           AVG(f.delay_seconds) AS avg_delay,
           MAX(f.delay_seconds) AS worst_delay,
           COUNT(*) AS observations
    FROM fact_trip_stop_delay f
    JOIN dim_stop s ON f.stop_id = s.stop_id
    JOIN latest ON f.poll_timestamp = latest.ts
    WHERE f.delay_seconds IS NOT NULL
      AND s.stop_lat IS NOT NULL AND s.stop_lon IS NOT NULL
    GROUP BY 1, 2, 3, 4
    """
)
rows = cur.fetchall()
cur.close()
conn.close()

features = []
for stop_id, stop_name, lat, lon, avg_delay, worst_delay, observations in rows:
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "stop_id": stop_id,
            "stop_name": stop_name,
            "avg_delay": round(avg_delay),
            "worst_delay": worst_delay,
            "observations": observations,
        },
    })

geojson = {"type": "FeatureCollection", "features": features}

with open("map/stops.geojson", "w") as f:
    json.dump(geojson, f)

print(f"Wrote {len(features)} stops to map/stops.geojson")
