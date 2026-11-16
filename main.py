from fastapi import FastAPI, HTTPException, Query

from clients.countries_client import CountriesNowClient
from clients.rates_client import FrankfurterClient
from config import settings
from exceptions import ApiUnavailableError, CountryNotFoundError
from services.travel_service import TravelService

app = FastAPI(
    title="Mini API Project",
    description="Country information and INR travel budget converter",
    version="1.0.0",
)

travel_service = TravelService(
    countries_client=CountriesNowClient(
        base_url=settings.countriesnow_base_url,
        timeout=settings.request_timeout,
    ),
    rates_client=FrankfurterClient(
        base_url=settings.frankfurter_base_url,
        timeout=settings.request_timeout,
    ),
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Mini API Project is running"}


@app.get("/countries/{name}")
async def get_country(name: str):
    try:
        return await travel_service.get_country_details(name)
    except CountryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ApiUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/roam/{name}")
async def calculate_travel_budget(
    name: str,
    budget_inr: float = Query(
        ...,
        gt=0,
        description="Travel budget in Indian Rupees",
    ),
):
    try:
        return await travel_service.calculate_travel_budget(name, budget_inr)
    except CountryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ApiUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
