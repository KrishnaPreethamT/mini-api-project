# Mini API Project

A small FastAPI app that takes a country and a budget in Indian Rupees, queries two public APIs, and tells you what that budget is worth in the local currency.

Built as a 3-day intern project. Day 1 = working endpoints. Day 2 = refactor + Docker. Day 3 = database.

---

## Project structure

```
mini-api-project/
├── clients/
│   ├── countries_client.py   # Adapter – CountriesNow API
│   └── frankfurter_client.py # Adapter – Frankfurter exchange-rate API
├── services/
│   └── travel_service.py     # Facade – orchestrates both clients
├── main.py                   # FastAPI routes only
├── config.py                 # All settings read from environment variables
├── exceptions.py             # CountryNotFoundError, ExternalAPIError
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── .env.example              # Copy this to .env and fill in values
└── postman/
    └── Mini Api Project.postman_collection.json
```

---

## Requirements

- Python 3.10+  **or**  Docker Desktop

---

## Running locally (without Docker)

### 1 — Clone the repo

```bash
git clone <your-repo-url>
cd mini-api-project
```

### 2 — Create and activate a virtual environment

```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Set up environment variables

```bash
cp .env.example .env
```

The defaults in `.env.example` already point at the live public APIs, so no edits are needed unless you want to change the timeout.

### 5 — Start the server

```bash
uvicorn main:app --reload
```

The app is now at **http://127.0.0.1:8000**. Open **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

---

## Running in Docker

### 1 — Build the image

```bash
docker build -t mini-api-project .
```

### 2 — Run the container

```bash
docker run --rm -p 8000:8000 --env-file .env mini-api-project
```

> **Note:** stop any local uvicorn first — both use port 8000.

The app is now at **http://localhost:8000**. Open **http://localhost:8000/docs** for Swagger UI.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/countries/{name}` | Country name, currency code, capital city |
| GET | `/roam/{name}?budget_inr=<amount>` | INR budget converted to local currency |

### Example response — `/roam/japan?budget_inr=150000`

```json
{
  "country": "Japan",
  "capital": "Tokyo",
  "currency": "JPY",
  "exchange_rate": 1.84,
  "rate_date": "2026-11-13",
  "budget_inr": 150000.0,
  "budget_local": 276000.0
}
```

### Error responses

| Scenario | Status |
|----------|--------|
| Country not recognised | 404 |
| External API down / timeout | 503 |
| Missing or invalid `budget_inr` | 422 |

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COUNTRIESNOW_BASE_URL` | ✅ Yes | — | CountriesNow API base URL |
| `FRANKFURTER_BASE_URL` | ✅ Yes | — | Frankfurter API base URL |
| `REQUEST_TIMEOUT_SECONDS` | No | `8.0` | HTTP timeout in seconds |

If either required variable is missing the app will **refuse to start** and print the name of the missing variable.

---

## Testing startup validation

```bash
# Should refuse to start and name the missing variable
COUNTRIESNOW_BASE_URL="" uvicorn main:app
```

```powershell
# PowerShell equivalent
$env:COUNTRIESNOW_BASE_URL=""; uvicorn main:app
```

## Testing timeout handling

Set `REQUEST_TIMEOUT_SECONDS=0.001` in `.env`, then call `/roam/japan?budget_inr=150000`. You should get a **503**. Reset the value afterwards.
