from time import perf_counter

from loguru import logger

from exceptions import ApiUnavailableError, CountryNotFoundError


class CountriesNowClient:
    def __init__(self, base_url: str, timeout: float):
        import httpx

        self._httpx = httpx
        self._base_url = base_url
        self._timeout = timeout

    async def get_country_details(self, country_name: str) -> dict[str, str]:
        currency_data = await self._get_country_data("currency", country_name)
        capital_data = await self._get_country_data("capital", country_name)

        country = currency_data.get("name")
        currency = currency_data.get("currency")
        capital = capital_data.get("capital")
        if not country or not currency or not capital:
            logger.warning("CountriesNow returned incomplete country details")
            raise ApiUnavailableError("Country information is incomplete")

        return {"country": country, "currency": currency, "capital": capital}

    async def _get_country_data(self, category: str, country_name: str) -> dict:
        path = f"/{category}/q"
        url = f"{self._base_url}{path}"
        started_at = perf_counter()
        try:
            async with self._httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params={"country": country_name})
        except self._httpx.TimeoutException as exc:
            self._log_failure(path, started_at, "timeout")
            raise ApiUnavailableError("External API request timed out") from exc
        except self._httpx.RequestError as exc:
            self._log_failure(path, started_at, type(exc).__name__)
            raise ApiUnavailableError("Unable to connect to CountriesNow") from exc

        self._log_response(path, response.status_code, started_at)

        if response.status_code == 404:
            raise CountryNotFoundError(f"Country '{country_name}' not found")
        if response.status_code != 200:
            raise ApiUnavailableError("CountriesNow is unavailable")

        try:
            result = response.json()
        except ValueError as exc:
            logger.warning("CountriesNow {} returned invalid JSON", path)
            raise ApiUnavailableError("CountriesNow returned an invalid response") from exc

        if not isinstance(result, dict):
            logger.warning("CountriesNow {} returned an unexpected response", path)
            raise ApiUnavailableError("CountriesNow returned an invalid response")
        if result.get("error"):
            logger.warning("CountriesNow did not find country {}", country_name)
            raise CountryNotFoundError(f"Country '{country_name}' not found")

        data = result.get("data")
        if not isinstance(data, dict):
            logger.warning("CountriesNow {} returned an unexpected data shape", path)
            raise ApiUnavailableError("Unexpected response from CountriesNow")
        return data

    @staticmethod
    def _log_response(path: str, status_code: int, started_at: float) -> None:
        latency_ms = (perf_counter() - started_at) * 1000
        log = logger.info if status_code < 400 else logger.warning
        log("CountriesNow GET {} -> {} in {:.0f} ms", path, status_code, latency_ms)

    @staticmethod
    def _log_failure(path: str, started_at: float, reason: str) -> None:
        latency_ms = (perf_counter() - started_at) * 1000
        logger.warning(
            "CountriesNow GET {} -> {} after {:.0f} ms",
            path,
            reason,
            latency_ms,
        )
