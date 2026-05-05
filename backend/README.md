# Backend API Routes

Base URL (local): `http://localhost:8000`

All backend routes are mounted with `/api` prefix.

- Cities: `/api/cities`
- Weather (city-based): `/api/weather/city/...`
- Alerts: `/api/alerts`
- Stations: `/api/stations`

Interactive docs:
- Swagger UI: `http://localhost:8000/docs`

## Cities

### `GET /api/cities`
Returns supported city IDs that map to stations.

Response shape:
```json
{
  "cities": ["adelaide", "brisbane", "cairns", "canberra", "darwin", "goldcoast", "hobart", "melbourne", "perth", "sydney"]
}
```

## Weather

### `GET /api/weather/city/{city_id}`
Returns consolidated city weather payload.

Path params:
- `city_id` (string): one of supported city IDs

Query params:
- `year` (int, optional)

Behavior:
- Resolves `city_id` to internal `station_id`
- If `year` is omitted, uses latest available year
- Returns frontend friendly monthly shape + derived `current`

Response shape:
```json
{
  "cityId": "sydney",
  "station_id": 64,
  "available_years": [2026, 2025, 2024],
  "selected_year": 2026,
  "monthly": [
    {
      "year": 2026,
      "month": "Jan",
      "monthIndex": 0,
      "date": "2026-01-01",
      "tempMin": 18.2,
      "tempMax": 27.3,
      "tempAvg": 22.7,
      "rainfall": 102.4,
      "humidity": 66.1,
      "windSpeed": 19.4
    }
  ],
  "current": {
    "temp": 22.7,
    "condition": "N/A",
    "humidity": 66.1,
    "windSpeed": 19.4,
    "rainfall": 102.4,
    "uvIndex": null
  }
}
```

Errors:
- `404` for unsupported city, missing mapped station or invalid year for city.

### `GET /api/weather/city/{city_id}/monthly`
Returns only monthly segment.

Query params:
- `year` (int, optional)

Response shape:
```json
{
  "cityId": "sydney",
  "station_id": 64,
  "available_years": [2026, 2025, 2024],
  "selected_year": 2026,
  "monthly": [ ... ]
}
```

### `GET /api/weather/city/{city_id}/current`
Returns only current segment.

Query params:
- `year` (int, optional)

Response shape:
```json
{
  "cityId": "sydney",
  "station_id": 64,
  "selected_year": 2026,
  "current": {
    "temp": 22.7,
    "condition": "N/A",
    "humidity": 66.1,
    "windSpeed": 19.4,
    "rainfall": 102.4,
    "uvIndex": null
  }
}
```

## Alerts

### `GET /api/alerts/`
Returns all active alerts.

Response shape:
```json
{
  "alerts": [
    {
      "id": "alert-12",
      "cityId": "cairns",
      "cityName": "Cairns Aero",
      "type": "Heavy Rainfall",
      "severity": "high",
      "title": "Heavy Rainfall Warning",
      "description": "Forecast rainfall may reach 120.0 mm. Heavy rainfall and localized flooding are possible.",
      "issued": "2026-05-05T03:00:00+10:00",
      "expires": null,
      "affectedAreas": [],
      "safetyTips": [
        "Watch for local flooding and avoid driving through floodwater.",
        "Monitor official weather updates.",
        "Heavy rainfall and localized flooding are possible."
      ],
      "isActive": true
    }
  ]
}
```

### `GET /api/alerts/{city_id}`
Returns active alerts for one city.

Response shape:
```json
{
  "cityId": "cairns",
  "alerts": [ ... ]
}
```

Errors:
- `404` for unsupported city or missing mapped station.

## Stations

### `GET /api/stations/`
Returns all stations.

Response shape:
```json
[
  {
    "station_id": 64,
    "station_name": "Sydney Observatory Hill",
    "state": "NSW",
    "latitude": -33.86,
    "longitude": 151.2,
    "elevation_m": 39.0,
    "start_date": "1858-01-01",
    "end_date": null,
    "coverage_pct": 98.3
  }
]
```
