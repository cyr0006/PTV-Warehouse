# Melbourne Transit Pipeline

An end-to-end data pipeline that ingests live Melbourne Metro Train data from PTV's GTFS-Realtime feeds, cleans and models it into a Postgres star schema, and (soon) surfaces it through a dashboard.

Built as a portfolio project by Aryan Cyrus. 

---

## Scope

- **Data source:** GTFS-Realtime (protobuf) via `opendata.transport.vic.gov.au`. Not the PTV Timetable API. That's a separate JSON/HMAC product, unused here.
- **Feed:** Trip Updates only (Metro Train). Vehicle Positions, Service Alerts, trams, and buses are explicitly out of scope for this version.
- **Fact grain:** append-only. Every poll writes new rows rather than upserting, to preserve delay history as a trend rather than a latest-snapshot.
- **Poll interval:** every 3 minutes IF the scheduler is running. The feed itself only refreshes server-side every 30s, so faster polling just duplicates data without adding signal.

### Explicitly deferred (not forgotten)
- **Vehicle Positions feed** — same ingestion pattern as Trip Updates, needs its own fact table (`vehicle_id`, `trip_id`, `lat`, `lon`, `timestamp`). Deferred to keep weekend scope achievable; planned as a near-term extension.
- **Trams, buses, regional services** — out of scope. Metro Train only.

---

## Architecture

```
[GTFS-Realtime feed: Trip Updates]
          │  polled every 3 min (scheduler.py)
          ▼
[ingestion/fetch_gtfs_realtime.py]  → raw .pb files → raw/trip_updates/
          │
          ▼
[etl/load_facts.py]  → parses protobuf, applies null-handling rules
          │
          ▼
[Postgres star schema]
    dim_route, dim_stop, dim_date  ← loaded once from GTFS Static
    fact_trip_stop_delay           ← appended every poll
          │
          ▼
[Dashboard — tool TBD, leaning Streamlit]
```

---

## Infrastructure

- Postgres running in Docker (`transit_db` container, db `transit_db`, user `transit_user`).
- Connection string: `postgresql://transit_user:transit_pass@localhost:5432/transit_db`
- `.env` holds `GTFS_SUBSCRIPTION_KEY`, `GTFS_TRIP_UPDATES_URL`, `GTFS_VEHICLE_POSITIONS_URL`.

### Auth NOTE
The PTV Open Data portal's OpenAPI spec lists the auth header as `Ocp-Apim-Subscription-Key`. I tried this and it did NOT work. Correct header seems to be, corroborated via the portal's own curl example, is `KeyId`.

---

## Data shape (GTFS-Realtime, decoded)

```
FeedMessage
├── header (feed timestamp, version)
└── entity[]                       ← repeated, one per trip
    └── entity[i].trip_update
        ├── trip { trip_id, route_id, start_time, start_date }
        └── stop_time_update[]     ← repeated, one per stop on that trip
            ├── stop_sequence
            ├── stop_id
            ├── arrival { delay, time }     (optional)
            └── departure { delay, time }   (optional)
```

Confirmed from a live sample (176 entities):
- `stop_time_update` count per entity ranges from **0 to 32** (avg 7.4). Some entities have zero stop_time_updates — parser must handle this without erroring.
- Of 1,307 total stop_time_updates: **104 missing `arrival`**, **21 missing `departure`**. Not every update has both fields populated.
- `delay` is relative (seconds vs scheduled), not an absolute time. Cross-referencing the actual scheduled time requires GTFS Static's `stop_times.txt` (not currently loaded — dims only use `routes.txt`/`stops.txt`).
- `stop_sequence` is the trip's internal stop order, not a universal stop ID. Stop identity is `stop_id`.

---

## Star schema

- **`dim_route`** (`route_id` PK, `route_name`, `route_type`) — loaded from GTFS Static, folder `2` (Metropolitan Train).
- **`dim_stop`** (`stop_id` PK, `stop_name`, `stop_lat`, `stop_lon`) — loaded from GTFS Static.
- **`dim_date`** (`date_id` PK — `DATE` type, `day_of_week`, `is_weekend`) — populated on the fly by the fact loader as new dates appear.
- **`fact_trip_stop_delay`** (`id`, `trip_id`, `route_id` FK, `stop_id` FK, `date_id` FK, `stop_sequence`, `delay_seconds`, `predicted_arrival`, `poll_timestamp`, `created_at`), grain is `(trip_id, stop_id, poll_timestamp)`. Append-only.

GTFS Static folder reference (Melbourne DoT static zip is split by mode):

| Folder | Mode |
|---|---|
| 1 | Regional Train |
| **2** | **Metropolitan Train** ← used |
| 3 | Metropolitan Tram |
| 4 | Myki Bus (Metro + Regional Town Bus) |
| 5 | Regional Coach |
| 6 | Regional Bus |
| 10 | Interstate Train |
| 11 | SkyBus |

---

## Data cleaning decisions
Please consult PTV-Warehouse\docs\data_decisions.md for details. 

---

## Pipeline components

| File | Purpose |
|---|---|
| `ingestion/fetch_gtfs_realtime.py` | Pulls Trip Updates feed, saves timestamped `.pb` to `raw/trip_updates/` |
| `etl/load_statics_to_dims.py` | One-off loader: GTFS Static `routes.txt`/`stops.txt` → `dim_route`/`dim_stop` |
| `etl/load_facts.py` | Parses latest `.pb`, applies null-handling rules, inserts into `fact_trip_stop_delay`; creates `dim_date` rows as needed |
| `scheduler.py` | Runs fetch + load in a loop every 3 min. Long-running process (Ctrl+C to stop). No cron on Windows, so this replaces it. |
| `warehouse/schema.sql` | DDL for the star schema |

### Running the pipeline
```bash
# One-time: load reference dimensions
python etl/load_statics_to_dims.py

# Start continuous polling (fetch + load every 3 min)
python scheduler.py
```

Verify accumulation:
```sql
SELECT poll_timestamp, COUNT(*)
FROM fact_trip_stop_delay
GROUP BY poll_timestamp
ORDER BY poll_timestamp;
```

---

## Status / next steps

- [x] Infrastructure (Docker, Postgres)
- [x] Ingestion script (Trip Updates)
- [x] Star schema DDL, deployed
- [x] Dimension loaders (`dim_route`, `dim_stop`)
- [x] Fact parser with null-handling
- [x] Scheduler (3-min polling loop)
- [ ] Let scheduler run long enough to build meaningful history
- [ ] Dashboard: tool not yet finalized, leaning Streamlit over Power BI for portfolio shareability
- [ ] Possible extension: Vehicle Positions feed + `fact_vehicle_position`

## Contributor(s)
Aryan Cyrus - Aryan.m10@yahoo.com