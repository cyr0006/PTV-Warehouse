from google.transit import gtfs_realtime_pb2

feed = gtfs_realtime_pb2.FeedMessage()

with open("raw/trip_updates/trip_updates_20260709T014924Z.pb", "rb") as f:
    feed.ParseFromString(f.read())

print(f"Feed timestamp: {feed.header.timestamp}")
print(f"Number of entities: {len(feed.entity)}")

# look at one entry
print(feed.entity[0])
print(len(feed.entity[0].trip_update.stop_time_update))
