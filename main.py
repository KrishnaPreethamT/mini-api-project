from fastapi import FastAPI, HTTPException, Query

from clients.countries_client import CountriesNowClient
from clients.frankfurter_client import FrankfurterClient
from exceptions import CountryNotFoundError, ExternalAPIError
from services.travel_service import TravelService

app = FastAPI(
    title="Mini API Project",
    description="Country information and INR travel budget converter",
    version="2.0.0",
)

# --- Dependency setup (created once at startup) -----------------------
_service = TravelService(
    countries_client=CountriesNowClient(),
    frankfurter_client=FrankfurterClient(),
)


# --- Exception helpers -------------------------------------------------

def _handle(exc: Exception) -> None:
    """Translate domain exceptions into FastAPI HTTP responses."""
    if isinstance(exc, CountryNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ExternalAPIError):
        raise HTTPException(status_code=503, detail=exc.detail)
    raise exc


# --- Routes ------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Mini API Project is running"}


@app.get("/countries/{name}")
async def get_country(name: str):
    try:
        return await _service.get_country_info(name)
    except (CountryNotFoundError, ExternalAPIError) as exc:
        _handle(exc)


@app.get("/roam/{name}")
async def calculate_travel_budget(
    name: str,
    budget_inr: float = Query(..., gt=0, description="Travel budget in Indian Rupees"),
):
    try:
        return await _service.calculate_travel_budget(name, budget_inr)
    except (CountryNotFoundError, ExternalAPIError) as exc:
        _handle(exc)
