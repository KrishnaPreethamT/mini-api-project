class NotFoundError(Exception):
    pass


class CountryNotFoundError(NotFoundError):
    pass


class TripNotFoundError(NotFoundError):
    pass


class ApiUnavailableError(Exception):
    pass
