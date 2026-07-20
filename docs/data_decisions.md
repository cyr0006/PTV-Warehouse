# A set of notes documenting and justifying design/cleaning decisions
- 19/07/2026: 8% of stop_time_updates lack an arrival block, 1.6% lack departure. Nulled rather than defaulted to 0 to avoid corrupting delay averages. Likely cause: origin stops have no arrival; terminus/incomplete trips may lack departure

- 19/07/2026: excluded bus replacement services from dim_route despite being in the Metro Train GTFS folder, as they're not rail services and out of scope

- 19/07/2026": In the static data, some route_long_names were NaN; for these the route_short_name was chosen as a backup to avoid NaNs. Reason; bad source data