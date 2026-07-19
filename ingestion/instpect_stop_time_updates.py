from google.transit import gtfs_realtime_pb2

feed = gtfs_realtime_pb2.FeedMessage()
with open("raw/trip_updates/trip_updates_20260709T014924Z.pb", "rb") as f:
    feed.ParseFromString(f.read())

counts = []
for entity in feed.entity:
    if entity.HasField("trip_update"):
        n = len(entity.trip_update.stop_time_update)
        counts.append(n)

print(f"Entities with trip_update: {len(counts)}")
print(f"Min stop_time_updates per entity: {min(counts)}")
print(f"Max stop_time_updates per entity: {max(counts)}")
print(f"Avg: {sum(counts)/len(counts):.1f}")

# Also check: does every stop_time_update have both arrival AND departure?
missing_arrival = 0
missing_departure = 0
total_stus = 0
for entity in feed.entity:
    if entity.HasField("trip_update"):
        for stu in entity.trip_update.stop_time_update:
            total_stus += 1
            if not stu.HasField("arrival"):
                missing_arrival += 1
            if not stu.HasField("departure"):
                missing_departure += 1

print(f"\nTotal stop_time_updates: {total_stus}")
print(f"Missing arrival: {missing_arrival}")
print(f"Missing departure: {missing_departure}")