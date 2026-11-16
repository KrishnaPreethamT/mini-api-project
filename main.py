
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

load_dotenv()

COUNTRIESNOW_BASE_URL = os.getenv(
    "COUNTRIESNOW_BASE_URL",
    "https://countriesnow.space/api/v0.1/countries"
).rstrip("/")

FRANKFURTER_BASE_URL = os.getenv(
    "FRANKFURTER_BASE_URL",
    "https://api.frankfurter.dev/v2"
).rstrip("/")

REQUEST_TIMEOUT = 8.0

app = FastAPI(
    title="Mini API Project",
    description="Country information and INR travel budget converter",
    version="1.0.0"
)


async def make_api_request(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None
):
    try:
        response = await client.get(url, params=params)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=503,
            detail="External API request timed out"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to the external API"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Requested information was not found"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=503,
            detail="External API service is unavailable"
        )

    try:
        return response.json()
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="External API returned an invalid response"
        )


async def get_country_details(
    client: httpx.AsyncClient,
    country_name: str
):
    currency_url = f"{COUNTRIESNOW_BASE_URL}/currency/q"
    capital_url = f"{COUNTRIESNOW_BASE_URL}/capital/q"

    currency_response = await make_api_request(
        client,
        currency_url,
        params={"country": country_name}
    )

    capital_response = await make_api_request(
        client,
        capital_url,
        params={"country": country_name}
    )

    if currency_response.get("error") or capital_response.get("error"):
        raise HTTPException(
            status_code=404,
            detail=f"Country '{country_name}' not found"
        )

    currency_data = currency_response.get("data")
    capital_data = capital_response.get("data")

    if not isinstance(currency_data, dict) or not isinstance(capital_data, dict):
        raise HTTPException(
            status_code=503,
            detail="Unexpected response from CountriesNow"
        )

    country = currency_data.get("name")
    currency = currency_data.get("currency")
    capital = capital_data.get("capital")

    if not country or not currency or not capital:
        raise HTTPException(
            status_code=503,
            detail="Country information is incomplete"
        )

    return {
        "country": country,
        "currency": currency,
        "capital": capital
    }


async def get_exchange_rate(
    client: httpx.AsyncClient,
    target_currency: str
):
    url = f"{FRANKFURTER_BASE_URL}/rate/INR/{target_currency}"

    rate_data = await make_api_request(client, url)

    try:
        rate = Decimal(str(rate_data["rate"]))
        rate_date = rate_data["date"]

    except (KeyError, TypeError, InvalidOperation):
        raise HTTPException(
            status_code=503,
            detail="Unable to read exchange rate information"
        )

    if not rate.is_finite() or rate <= 0:
        raise HTTPException(
            status_code=503,
            detail="External API returned an invalid exchange rate"
        )

    return {
        "base": rate_data.get("base", "INR"),
        "quote": rate_data.get("quote", target_currency),
        "rate": rate,
        "date": rate_date
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Mini API Project is running"
    }


@app.get("/countries/{name}")
async def get_country(name: str):
    timeout = httpx.Timeout(REQUEST_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        country_details = await get_country_details(
            client,
            name
        )

    return country_details


@app.get("/roam/{name}")
async def calculate_travel_budget(
    name: str,
    budget_inr: float = Query(
        ...,
        gt=0,
        description="Travel budget in Indian Rupees"
    )
):
    timeout = httpx.Timeout(REQUEST_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        country_details = await get_country_details(
            client,
            name
        )

        exchange_details = await get_exchange_rate(
            client,
            country_details["currency"]
        )

    budget = Decimal(str(budget_inr))
    rate = exchange_details["rate"]

    local_budget = (budget * rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return {
        "country": country_details["country"],
        "capital": country_details["capital"],
        "currency": country_details["currency"],
        "exchange_rate": float(rate),
        "rate_date": exchange_details["date"],
        "budget_inr": budget_inr,
        "budget_local": float(local_budget)
    }
