--wayf weather database
--use reset.sql first before running

create table stations (
    station_id serial primary key,
    station_name varchar(150) not null unique,
    aus_state varchar(3),
    latitude numeric(9,6),
    longitude numeric(9,6),
    elevation_m numeric(6,1),
    starting_date date,
    end_date date,
    coverage_pct numeric(5,2)
);


create table daily_weather(
    id bigserial primary key,
    station_id integer not null references stations(station_id) on delete cascade,
    obs_date date not null, 
    evapotranspiration_mm numeric(7,2),
    rain_mm numeric(7,2),
    max_temp_c numeric(5,2),
    min_temp_c numeric(5,2),
    max_humidity_pct numeric(5,2),
    min_humidity_pct numeric(5,2),
    avg_wind_speed_mps numeric(5,2),
    constraint uq_station_obs_date unique (station_id, obs_date)

);

create table monthly_aggregates(
    id serial primary key,
    station_id integer not null references stations(station_id) on delete cascade,
    station_year integer not null, 
    station_month integer not null check(station_month between 1 and 12),
    avg_max_temp_c numeric(5, 2),
    avg_min_temp_c numeric(5, 2),
    total_rain_mm numeric(9, 2),
    avg_min_humidity_pct numeric(5, 2),
    avg_max_humidity_pct numeric(5, 2),
    avg_wind_speed_ms numeric(6, 2),
    days_recorded integer,
    constraint uq_station_year_month unique (station_id, station_year, station_month)
);

create table forecasts (
    id bigserial primary key,
    station_id integer not null references stations(station_id) on delete cascade,
    forecast_date date not null,                  --the date being predicted
    generated_at timestamptz not null default now(),             -- when prediction was made (UTC)
    horizon_days smallint not null,              --1–7 days ahead
    pred_max_temp_c numeric(5,2),
    pred_min_temp_c numeric(5,2),
    pred_rain_mm numeric(7,2),
    pred_max_humidity_pct numeric(5,2),
    pred_min_humidity_pct numeric(5,2),
    pred_wind_speed_ms numeric(5,2),
    constraint uq_forecast unique (station_id, forecast_date, horizon_days)
);

create table alerts (
    alert_id serial primary key,
    station_id  integer not null references stations(station_id),
    alert_type varchar(200) NOT NULL,                   
    title varchar(200),
    severity varchar(20) not null,                   
    message text not null,
    affected_areas text,
    safety_tips text,
    start_time timestamptz not null,
    end_time timestamptz,                              --null if still continuing
    is_active boolean not null default true
);

CREATE TABLE model_stats (
    id serial primary key,
    stats jsonb not null,
    created_at timestamptz not null default now()
);

insert into alerts (station_id, alert_type, severity, message, start_time)
select 
    station_id,
    'heatwave',
    'severe',
    'Maximum temperature predicted to exceed 40°C',
    now()
from forecasts
where forecast_date = CURRENT_DATE + INTERVAL '1 day'
AND pred_max_temp_c > 40;
