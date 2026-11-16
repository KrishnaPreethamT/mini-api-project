"""
Custom exceptions shared across clients and services.
"""


class CountryNotFoundError(Exception):
    """Raised when a country name is not recognised by the upstream API."""

    def __init__(self, country: str):
        self.country = country
        super().__init__(f"Country not found: {country!r}")


class ExternalAPIError(Exception):
    """Raised when an upstream API is unreachable, times out, or returns garbage."""

    def __init__(self, detail: str = "External API error"):
        self.detail = detail
        super().__init__(detail)
