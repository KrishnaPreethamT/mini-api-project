# Mini API Project

A small FastAPI service for looking up a country's capital and currency, then estimating how much an INR travel budget is worth in that currency. Country details come from CountriesNow, and exchange rates come from Frankfurter.

## Getting started

You need Python 3.12 to run the app locally. Docker Desktop is optional unless you want to use the container.

Clone the repository and open a terminal in the project folder. Create and activate a virtual environment, install the packages, and copy the example settings file:

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS or Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Start the API:

```bash
uvicorn main:app --reload
```

The interactive API docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

## Run with Docker

With Docker Desktop running and `.env` created, run these commands from the project folder:

```bash
docker build -t mini-api-project .
docker run --rm -p 8000:8000 --env-file .env mini-api-project
```

Open [http://localhost:8000/docs](http://localhost:8000/docs). Press Ctrl+C to stop the container.

## Settings

The app reads its settings from the environment or `.env`.

| Name | What it controls | Example or default |
| --- | --- | --- |
| `COUNTRIESNOW_BASE_URL` | CountriesNow API address | `https://countriesnow.space/api/v0.1/countries` (required) |
| `FRANKFURTER_BASE_URL` | Frankfurter API address | `https://api.frankfurter.dev/v2` (required) |
| `REQUEST_TIMEOUT` | Maximum wait for an upstream request, in seconds | `8` |

The app reports which base URL is missing if a required setting is not provided. The timeout must be a positive number. Keep `.env` on your machine; it is excluded from Git and from the Docker image.

## API

### `GET /health`

Checks that the app is running.

```json
{
  "status": "healthy",
  "message": "Mini API Project is running"
}
```

### `GET /countries/{name}`

For example, `GET /countries/Japan` returns:

```json
{
  "country": "Japan",
  "currency": "JPY",
  "capital": "Tokyo"
}
```

### `GET /roam/{name}?budget_inr={amount}`

For example, `GET /roam/Japan?budget_inr=150000` returns the country details, the exchange rate used, and the converted budget. Rates change over time, so the date and amounts below are examples:

```json
{
  "country": "Japan",
  "capital": "Tokyo",
  "currency": "JPY",
  "exchange_rate": 1.7,
  "rate_date": "2026-11-13",
  "budget_inr": 150000.0,
  "budget_local": 255000.0
}
```

Errors return a JSON `detail` message:

| Status | Cause | Example |
| --- | --- | --- |
| `404` | Country not found | `GET /countries/Atlantis` |
| `503` | An upstream API is unavailable, times out, or returns invalid data | Set `REQUEST_TIMEOUT=0.001`, then call `/roam/Japan?budget_inr=150000` |
| `422` | The budget is missing or is zero or less | `GET /roam/Japan?budget_inr=0` |

## How the code is organized

```text
mini-api-project/
├── clients/
│   ├── countries_client.py
│   └── rates_client.py
├── services/
│   └── travel_service.py
├── postman/
│   └── Mini Api Project.postman_collection.json
├── config.py
├── exceptions.py
├── main.py
├── Dockerfile
├── .dockerignore
├── .env.example
└── requirements.txt
```

The two client classes handle communication with CountriesNow and Frankfurter. `TravelService` calls those clients and calculates the converted budget. `main.py` exposes the routes and turns application errors into HTTP responses. Settings and application exceptions live in `config.py` and `exceptions.py`.

The clients act as Adapters because they hide each provider's URLs and response format. `TravelService` acts as a Facade, giving the routes one place to request the work done by both clients. It receives the clients when it is created, which makes them easy to replace later.

The Postman collection in `postman/` contains requests for the local API.
