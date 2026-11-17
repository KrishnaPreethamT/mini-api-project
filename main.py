from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger

from clients.countries_client import CountriesNowClient
from clients.rates_client import FrankfurterClient
from config import settings
from db import Base, engine, get_db_session
from exceptions import ApiUnavailableError, CountryNotFoundError, NotFoundError
from logging_setup import configure_logging
from repositories.trip_repository import TripRepository
from schemas import TripCreate, TripOut, TripUpdate
from services.trip_service import TripService
from services.travel_service import TravelService


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Mini API Project",
    description="Country information and INR travel budget converter",
    version="1.0.0",
    lifespan=lifespan,
)

countries_client = CountriesNowClient(
    base_url=settings.countriesnow_base_url,
    timeout=settings.request_timeout,
)
rates_client = FrankfurterClient(
    base_url=settings.frankfurter_base_url,
    timeout=settings.request_timeout,
)
travel_service = TravelService(
    countries_client=countries_client,
    rates_client=rates_client,
)


@app.middleware("http")
async def log_request(request: Request, call_next):
    started_at = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        latency_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "{} {} -> {} in {:.0f} ms",
            request.method,
            request.url.path,
            status_code,
            latency_ms,
        )


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ApiUnavailableError)
async def handle_api_unavailable(request: Request, exc: ApiUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def get_trip_service(session=Depends(get_db_session)) -> TripService:
    repository = TripRepository(session)
    return TripService(repository, countries_client, rates_client)


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


@app.post(
    "/trips",
    response_model=TripOut,
    response_model_exclude_none=True,
    status_code=201,
)
async def create_trip(
    trip: TripCreate,
    service: TripService = Depends(get_trip_service),
):
    return await service.create_trip(trip)


@app.get("/trips", response_model=list[TripOut], response_model_exclude_none=True)
async def list_trips(service: TripService = Depends(get_trip_service)):
    return await service.list_trips()


@app.get("/trips/{trip_id}", response_model=TripOut, response_model_exclude_none=True)
async def get_trip(trip_id: int, service: TripService = Depends(get_trip_service)):
    return await service.get_trip(trip_id)


@app.patch("/trips/{trip_id}", response_model=TripOut, response_model_exclude_none=True)
async def update_trip(
    trip_id: int,
    update: TripUpdate,
    service: TripService = Depends(get_trip_service),
):
    return await service.update_trip(trip_id, update)


@app.delete("/trips/{trip_id}", status_code=204)
async def delete_trip(trip_id: int, service: TripService = Depends(get_trip_service)):
    await service.delete_trip(trip_id)
    return Response(status_code=204)
