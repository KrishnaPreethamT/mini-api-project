# Mini API Project

A FastAPI app for country information, INR travel budget estimates, and saved travel plans. Country and exchange-rate data come from CountriesNow and Frankfurter. PostgreSQL stores trips.

## Run with Docker Compose

You need Docker Desktop with Compose enabled. If you do not already have a `.env` file, create one from the example. Then start the app and database from the project folder:

```cmd
if not exist .env copy .env.example .env
docker compose up --build
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) to try the API. The app waits for Postgres to become healthy before it starts.

To stop the services, press Ctrl+C and run:

```cmd
docker compose down
```

Trips remain in the named database volume. To remove the volume and start with an empty database, run:

```cmd
docker compose down -v
```

This deletes all saved trips in the database volume.

## Run locally

For local development, start only the database container:

```cmd
if not exist .env copy .env.example .env
docker compose up -d db
```

Create and activate a virtual environment, install the requirements, then start FastAPI:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

In PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1` instead.

The local `DATABASE_URL` in `.env` connects to Postgres on `localhost`. The Compose app uses the `db` service name instead.

## Configuration

| Setting | Purpose | Example or default |
| --- | --- | --- |
| `COUNTRIESNOW_BASE_URL` | CountriesNow API base URL | `https://countriesnow.space/api/v0.1/countries` |
| `FRANKFURTER_BASE_URL` | Frankfurter API base URL | `https://api.frankfurter.dev/v2` |
| `REQUEST_TIMEOUT` | Timeout for each outside API request, in seconds | `8` |
| `DATABASE_URL` | SQLAlchemy connection URL | Local: `postgresql+psycopg://mini_api:change-me@localhost:5432/mini_api` |
| `LOG_LEVEL` | Minimum application log level | `INFO` |
| `POSTGRES_USER` | Database username | `mini_api` |
| `POSTGRES_PASSWORD` | Database password | `change-me` in `.env.example` |
| `POSTGRES_DB` | Database name | `mini_api` |

The example password is for local development only. Keep your real `.env` out of Git. Compose supplies a container-specific `DATABASE_URL` that connects to the `db` service.

## API endpoints

### Existing endpoints

These endpoints keep their Day 2 behavior.

| Method and path | Purpose |
| --- | --- |
| `GET /health` | Check that the app is running |
| `GET /countries/{name}` | Return the country, currency, and capital |
| `GET /roam/{name}?budget_inr=150000` | Convert an INR budget using the current exchange rate |

### Trips

Create a trip with `POST /trips`:

```json
{
  "traveller": "Asha",
  "country": "Japan",
  "budget_inr": 150000,
  "travel_date": "2030-12-20"
}
```

The app looks up the country's currency, saves the trip, and returns `201 Created` with its generated ID, currency code, and creation time:

```json
{
  "id": 1,
  "traveller": "Asha",
  "country": "Japan",
  "currency_code": "JPY",
  "budget_inr": 150000,
  "travel_date": "2030-12-20",
  "created_at": "2026-11-17T10:42:00Z"
}
```

`GET /trips` returns a list. Each trip includes today's exchange rate and its converted budget:

```json
[
  {
    "id": 1,
    "traveller": "Asha",
    "country": "Japan",
    "currency_code": "JPY",
    "budget_inr": 150000,
    "rate": 1.8,
    "budget_local": 270000,
    "travel_date": "2030-12-20",
    "created_at": "2026-11-17T10:42:00Z"
  }
]
```

The rate and converted amount vary over time. Trips with the same currency share one rate lookup per list request.

`GET /trips/1` returns one saved trip, with the same fields as the create response.

`PATCH /trips/1` changes only the fields supplied and returns the updated trip:

```json
{
  "budget_inr": 120000
}
```

The response includes the updated trip, with `budget_inr` set to `120000`.

`DELETE /trips/1` returns `204 No Content` with an empty response body.

### Errors

| Status | Cause |
| --- | --- |
| `422` | Required fields are missing or invalid, the budget is zero or less, or the travel date is in the past |
| `404` | The country or trip ID does not exist |
| `503` | CountriesNow or Frankfurter is unavailable or times out |

## Logs

The app logs each incoming request and each call to CountriesNow or Frankfurter with its status and duration. To follow the app logs:

```powershell
docker compose logs -f app
```

`LOG_LEVEL` controls verbosity. Logs do not include the database password or full database URL.

## Postman

Import `postman/Mini Api Project.postman_collection.json` and run the collection against the local app. The `Trips` folder creates, lists, reads, updates, and deletes a trip, then checks the past-date, zero-budget, and missing-trip errors.

## Project structure

```text
mini-api-project/
├── clients/
│   ├── countries_client.py
│   └── rates_client.py
├── repositories/
│   └── trip_repository.py
├── services/
│   ├── travel_service.py
│   └── trip_service.py
├── postman/
│   └── Mini Api Project.postman_collection.json
├── .dockerignore
├── .env.example
├── config.py
├── db.py
├── Dockerfile
├── docker-compose.yml
├── exceptions.py
├── logging_setup.py
├── main.py
├── schemas.py
└── requirements.txt
```

`TripRepository` owns database operations and returns plain Python records. `TripService` coordinates country lookup, storage, and budget conversion. The routes call the service and map application errors to HTTP responses. SQLAlchemy models and sessions are defined in `db.py`.
