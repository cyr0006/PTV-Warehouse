import pandas as pd
import psycopg2

conn = psycopg2.connect("postgresql://transit_user:transit_password@localhost:5432/transit_db")
cur = conn.cursor()

routes = pd.read_csv("data\\gtfs_static\\gtfs\\2\\google_transit\\routes.txt", usecols=["route_id","route_short_name", "route_long_name", "route_type"])
routes["route_long_name"] = routes["route_long_name"].fillna(routes["route_short_name"])  # <-- add here
routes = routes[~routes["route_id"].str.endswith("-R:")]
for _, row in routes.iterrows():
    cur.execute(
        "INSERT INTO dim_route (route_id, route_name, route_type) VALUES (%s, %s, %s) ON CONFLICT (route_id) DO NOTHING",
        (row.route_id, row.route_long_name, row.route_type)
    )

stops = pd.read_csv("data\\gtfs_static\\gtfs\\2\\google_transit\\stops.txt", usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"])
for _, row in stops.iterrows():
    cur.execute(
        "INSERT INTO dim_stop (stop_id, stop_name, stop_lat, stop_lon) VALUES (%s, %s, %s, %s) ON CONFLICT (stop_id) DO NOTHING",
        (row.stop_id, row.stop_name, row.stop_lat, row.stop_lon)
    )


conn.commit()
cur.close()
conn.close()
print(f"Loaded {len(routes)} routes, {len(stops)} stops")