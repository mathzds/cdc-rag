from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    id: str
    text: str


class ServiceError(Exception):
    pass
