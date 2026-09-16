TV Delay Map — Spec for Tonight (Esri call, tomorrow 2:30pm)
Timebox: 90 min, hard stop. Win condition is a screenshot + one sentence, not a shipped app.

Step 0 — Verify first (5 min)
docker exec -it transit_db psql -U transit_user -d transit_db
\d dim_stop
SELECT MIN(poll_timestamp), MAX(poll_timestamp), COUNT(\*) FROM fact_trip_stop_delay;
Confirms stop_lat/stop_lon are populated, and how much history you actually have — adjust the interval below to match.

Phase 0 — Data prep (~20 min)
SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon,
AVG(f.delay_seconds) AS avg_delay,
MAX(f.delay_seconds) AS worst_delay,
COUNT(_) AS observations
FROM fact_trip_stop_delay f
JOIN dim_stop s ON f.stop_id = s.stop_id
WHERE f.poll_timestamp > now() - interval '<N> days' -- match actual history span
GROUP BY 1,2,3,4
HAVING COUNT(_) > 20;
Export to GeoJSON (FeatureCollection, Point geometries). Coordinate order is [lon, lat], not [lat, lon] — easy to get backwards and land every dot in the ocean. Filter to 200–400 points; thousands renders as soup.

Phase 1 — Map skeleton (~20 min)
Pin the SDK version explicitly: <script src="https://js.arcgis.com/4.34/"></script>. Don't use an unpinned/latest CDN link — ArcGIS moved to a component-based 5.x model in 2026 (<arcgis-map>, Calcite-based), which won't match the classic Map/MapView/GeoJSONLayer pattern most tutorials still show. 4.34 is the last 4.x release and behaves like every guide you'll find.
Map + MapView centred on Melbourne (-37.81, 144.96), zoom 10–11, dark basemap, GeoJSONLayer.
Serve over local HTTP, don't open via file:// — GeoJSONLayer's fetch silently fails under file:// CORS. python -m http.server is enough.
Free API key from the ArcGIS Location Platform dashboard (used to be called "Developer account" — same thing).
Milestone: dots on a map in the right places. That's 80% of the value.

Phase 2 — Symbology (~20 min)
ClassBreaksRenderer on avg_delay, five breaks yellow→red, marker size scaling with delay too (double encoding reads better in a screenshot).

Phase 3 — Popups (~10 min)
popupTemplate: stop name as title, then avg delay / worst delay / observation count.

Phase 4 — Deploy (~15 min)
Netlify drop as a separate site. Restrict the API key to that domain in the dashboard before you push.

Fallbacks
Data/geometry issue → skip the map, matplotlib delay-by-hour-of-day chart instead. Still an insight, 20 min.
Running low on time → stop and go to bed. A rushed, broken demo the morning of is worse than no demo.
Interview context
This is a 30-min intro/background call, not a technical interview. He wants to hear you talk fluently about what you built — the map is a garnish, not the meal. Don't let prepping it eat time you'd otherwise spend just being ready to talk.

Lead with what you already have, cold, regardless of whether the map ships:

Append-only fact grain (not upsert) — deliberate, so delay history is queryable as a trend, not a snapshot
Caught the GTFS-Realtime vs PTV Timetable API distinction early — different product, different auth
Auth header gotcha: docs say Ocp-Apim-Subscription-Key, actual working header is KeyId
Honest-scoping principle: only list what's genuinely built; Vehicle Positions/trams/buses deliberately deferred, not overclaimed
If the map comes together, drop it in naturally — don't open with it:

"After your email I loaded a week of it into the ArcGIS Maps SDK to see it spatially — took about an hour. Turns out [your finding]. It also made me realise why I'd built the schema append-only: I can scrub back through delay history rather than just seeing current state."

If it doesn't, this is still a genuinely good thing to say:

"I started wiring it into the ArcGIS SDK last night — got the points rendering, symbology was next."

Either way, the actual differentiator is that you reached for their own SDK, unprompted, the same day they emailed you. That's the story, independent of whether the demo ships.
