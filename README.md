# Weather at Your Fingertips

Full-stack weather dashboard for Australian city and station data.

Frontend: React + Vite  
Backend: FastAPI + PostgreSQL  
Data pipeline: BOM data scripts in `DATA/`

Base URLs (local):
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

Main app areas:
- Map: weather markers and map layers
- Dashboard: city weather overview
- Compare: city comparison charts
- Alerts: active weather alerts

## Start

### Full stack
Starts PostgreSQL, backend, and frontend.

```bash
make up
```

Equivalent Docker command:
```bash
docker compose up -d --build
```

### Full stack + data load
Starts containers, waits for the database, then loads cleaned weather data.

```bash
make all
```

### Backend only
Starts PostgreSQL and FastAPI only.

```bash
docker compose -f docker-compose.backend.yml up -d --build
```

### Stop

```bash
make down
```

Equivalent Docker command:
```bash
docker compose down
```

### Reset database
Removes the PostgreSQL volume and starts fresh containers.

```bash
make reset-db
```

## Environment

Copy the example environment file when API keys or a custom database URL are
needed.

```bash
cp .env.example .env
```

Common variables:
- `DATABASE_URL`: database connection string
- `VITE_API_BASE_URL`: frontend API base URL, usually `http://localhost:8000`
- `VITE_MAPBOX_TOKEN`: required for Mapbox map tiles
- `OPENWEATHER_API_KEY`: optional, enables OpenWeather alert sync
- `GEMINI_API_KEY`: optional, enriches OpenWeather alert content

Docker backend uses the `db` service host. Local backend development should use
`localhost` in `DATABASE_URL`.

Frontend local env file:
```bash
# frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_MAPBOX_TOKEN=your_mapbox_token
```

## Frontend

App routes:
- `/`: Map
- `/dashboard`: Dashboard
- `/compare`: Compare
- `/alerts`: Alerts

Local development:
```bash
cd frontend
npm install
npm run dev
```

If the API is unavailable, some frontend calls fall back to mock weather data.

## Backend

Base URL (local): `http://localhost:8000`

All backend routes are mounted with `/api` prefix.

- Cities: `/api/cities`
- Weather: `/api/weather/...`
- Alerts: `/api/alerts`
- Stations: `/api/stations`

Interactive docs:
- Swagger UI: `http://localhost:8000/docs`

Local development:
```powershell
docker compose up -d db
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/weather_at_your_fingertips_db"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Routes

### Cities

#### `GET /api/cities`
Returns supported city IDs that map to stations.

### Weather

#### `GET /api/weather/cities/summary`
Returns annual weather summary for all supported cities.

Query params:
- `year` (int, optional)

#### `GET /api/weather/city/{city_id}`
Returns consolidated city weather payload.

Path params:
- `city_id` (string): one of supported city IDs

Query params:
- `year` (int, optional)

#### `GET /api/weather/city/{city_id}/monthly`
Returns only monthly weather data for one city.

#### `GET /api/weather/city/{city_id}/current`
Returns only current weather data for one city.

#### `GET /api/weather/current`
Returns current weather using either city ID or station ID.

Query params:
- `city_id` (string, optional)
- `station_id` (string, optional)

#### `GET /api/weather/monthly`
Returns monthly weather using either city ID or station ID.

Query params:
- `city_id` (string, optional)
- `station_id` (string, optional)
- `year` (int, optional)

#### `GET /api/weather/historical`
Returns historical weather records.

Query params:
- `city_id` (string, optional)
- `station_id` (string, optional)
- `year` (int, optional)
- `month` (int, optional)
- `day` (int, optional)

#### `GET /api/weather/forecast`
Returns 7-day forecast data.

Query params:
- `city_id` (string, optional)
- `station_id` (string, optional)

### Alerts

#### `GET /api/alerts/`
Returns active alerts.

Query params:
- `include_inactive` (bool, optional)

#### `GET /api/alerts/{city_id}`
Returns alerts for one city.

Query params:
- `include_inactive` (bool, optional)

### Stations

#### `GET /api/stations/`
Returns all stations.

#### `GET /api/stations/{station_id}`
Returns one station by ID.

## Data

The `DATA/` directory contains scripts for downloading BOM data, preparing
station summaries, cleaning weather observations, loading PostgreSQL, and
running prediction workflows.

Run the full initial pipeline:
```bash
python DATA/initial_setup.py
```

Load already-cleaned data into PostgreSQL:
```bash
python DATA/utils/load_to_db.py
```

Loader requirements:
- `DATABASE_URL` points at a reachable PostgreSQL database
- Cleaned data exists at the path configured in `DATA/utils/config.json`
- Station rows already exist in the database

Unknown stations are skipped by the loader instead of being inserted.

## Project Folders

- `backend/`: FastAPI app, routers, services, scheduled jobs, database models
- `frontend/`: React/Vite app
- `DATA/`: data ingestion, cleaning, loading, and prediction scripts
- `docker-compose.yml`: full local stack
- `docker-compose.backend.yml`: backend + database only
- `Makefile`: common project commands
