DROP TABLE IF EXISTS fact_trip_stop_delay CASCADE;
DROP TABLE IF EXISTS dim_route CASCADE;
DROP TABLE IF EXISTS dim_stop CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;


create table dim_route (
   route_id   text primary key,
   route_name text,
   route_type text
);

create table dim_stop (
   stop_id   text primary key,
   stop_name text,
   stop_lat  double precision,
   stop_lon  double precision
);

create table dim_date (
   date_id     date primary key,
   day_of_week text,
   is_weekend  boolean
);

create table fact_trip_stop_delay (
   id                     bigserial primary key,
   trip_id                text not null,
   route_id               text
      references dim_route ( route_id ),
   stop_id                text
      references dim_stop ( stop_id ),
   date_id                date
      references dim_date ( date_id ),
   stop_sequence          integer,
   delay_seconds          integer,
   predicted_arrival_time timestamptz,
   poll_timestamp         timestamptz,
   created_at             timestamptz default now()
);

create index idx_fact_trip_id on
   fact_trip_stop_delay (
      trip_id
   );
create index idx_fact_poll_time on
   fact_trip_stop_delay (
      poll_timestamp
   );