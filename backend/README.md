# Backend API Routes

Base URL (local): `http://localhost:8000`

All backend routes are mounted with `/api` prefix.

- Stations: `/api/stations`
- Weather: `/api/weather`
- Dashboard: `/api/dashboard`
- Compare: `/api/compare`

Interactive docs:
- Swagger UI: `http://localhost:8000/docs`

## Stations

### `GET /api/stations/`
Returns all stations.

## Weather

### `GET /api/weather/{station_id}/daily`
Returns daily weather rows for one station.

### `GET /api/weather/{station_id}/years`
Returns available years for one station.

### `GET /api/weather/{station_id}/monthly`
Returns monthly aggregates for one station.

Query params:
- `year` (int, optional)

## Dashboard

### `GET /api/dashboard/`
Single call dashboard payload.

Query params:
- `station_id` (int, optional)
- `year` (int, optional)
- `include_stations` (bool, optional, default `true`)

Behavior:
- If `station_id` is omitted, backend uses station `1` if it exists, otherwise first available station.
- If `year` is omitted, backend uses latest available year for selected station.
- Set `include_stations=false` on subsequent filter calls to avoid returning station list again.
- Returns calculated annual `summary` from selected year's monthly values.

Example calls:
- Initial load: `/api/dashboard/`
- Change filters: `/api/dashboard/?station_id=63&year=2026&include_stations=false`

Response shape:
```json
{
  "selected_station_id": 63,
  "available_years": [2026, 2025, 2024],
  "selected_year": 2026,
  "monthly": [ ... ],
  "summary": {
    "avgTemp": 22.1,
    "maxTemp": 32.4,
    "minTemp": 11.2,
    "totalRain": 812.7,
    "avgHumidity": 63.8,
    "avgWind": 18.5
  },
  "stations": [ ... ]
}
```

Errors:
- `404` if selected station does not exist.

## Compare

### `GET /api/compare/cities`
Returns supported cities.

Response shape:
```json
{
  "cities": ["adelaide", "brisbane", "cairns", "canberra", "darwin", "goldcoast", "hobart", "melbourne", "perth", "sydney"]
}
```

### `GET /api/compare/`
Single-call compare payload for two cities.

Query params:
- `city1` (string, optional, default `sydney`)
- `city2` (string, optional, default `melbourne`)
- `year` (int, optional)

Behavior:
- Maps `city1` and `city2` to station IDs using the internal mapping dict.
- `available_years` is the shared intersection between both cities.
- If `year` is omitted, backend uses latest shared year.
- Returns calculated annual `summary` for each city.

Example calls:
- Default compare load: `/api/compare/`
- Custom compare: `/api/compare/?city1=perth&city2=brisbane&year=2025`

Response shape:
```json
{
  "available_years": [2026, 2025, 2024],
  "selected_year": 2026,
  "city1": {
    "city_id": "sydney",
    "station_id": 63,
    "available_years": [ ... ],
    "monthly": [ ... ],
    "summary": {
      "avgTemp": 22.1,
      "maxTemp": 32.4,
      "minTemp": 11.2,
      "totalRain": 812.7,
      "avgHumidity": 63.8,
      "avgWind": 18.5
    }
  },
  "city2": {
    "city_id": "melbourne",
    "station_id": 274,
    "available_years": [ ... ],
    "monthly": [ ... ],
    "summary": {
      "avgTemp": 18.9,
      "maxTemp": 29.1,
      "minTemp": 8.3,
      "totalRain": 604.2,
      "avgHumidity": 61.4,
      "avgWind": 21.2
    }
  }
}
```

Errors:
- `400` for invalid city, same city chosen twice, or unavailable year for pair.
