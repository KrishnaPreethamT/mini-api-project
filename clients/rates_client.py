from decimal import Decimal, InvalidOperation
from time import perf_counter

from loguru import logger

from exceptions import ApiUnavailableError


class FrankfurterClient:
    def __init__(self, base_url: str, timeout: float):
        import httpx

        self._httpx = httpx
        self._base_url = base_url
        self._timeout = timeout

    async def get_exchange_rate(self, base_currency: str, target_currency: str) -> dict:
        path = f"/rate/{base_currency}/{target_currency}"
        url = f"{self._base_url}{path}"
        started_at = perf_counter()
        try:
            async with self._httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
        except self._httpx.TimeoutException as exc:
            self._log_failure(path, started_at, "timeout")
            raise ApiUnavailableError("External API request timed out") from exc
        except self._httpx.RequestError as exc:
            self._log_failure(path, started_at, type(exc).__name__)
            raise ApiUnavailableError("Unable to connect to Frankfurter") from exc

        self._log_response(path, response.status_code, started_at)

        if response.status_code != 200:
            raise ApiUnavailableError("Frankfurter is unavailable")

        try:
            result = response.json()
            rate = Decimal(str(result["rate"]))
            rate_date = result["date"]
        except (ValueError, KeyError, TypeError, InvalidOperation) as exc:
            logger.warning("Frankfurter {} returned invalid exchange rate data", path)
            raise ApiUnavailableError("Unable to read exchange rate information") from exc

        if not rate.is_finite() or rate <= 0:
            logger.warning("Frankfurter {} returned a non-positive exchange rate", path)
            raise ApiUnavailableError("External API returned an invalid exchange rate")

        return {
            "base": result.get("base", base_currency),
            "quote": result.get("quote", target_currency),
            "rate": rate,
            "date": rate_date,
        }

    @staticmethod
    def _log_response(path: str, status_code: int, started_at: float) -> None:
        latency_ms = (perf_counter() - started_at) * 1000
        log = logger.info if status_code < 400 else logger.warning
        log("Frankfurter GET {} -> {} in {:.0f} ms", path, status_code, latency_ms)

    @staticmethod
    def _log_failure(path: str, started_at: float, reason: str) -> None:
        latency_ms = (perf_counter() - started_at) * 1000
        logger.warning(
            "Frankfurter GET {} -> {} after {:.0f} ms",
            path,
            reason,
            latency_ms,
        )
