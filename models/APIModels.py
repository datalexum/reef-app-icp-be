from enum import Enum
from typing import List

from pydantic import BaseModel

from scrapping.scraper import FaunaMarinScraper
from session.session_provider import FaunaMarinSessionProvider


class ICPAnalysis(BaseModel):
    id: str
    data: str


class ReefTank(BaseModel):
    id: int
    name: str


class Credentials(BaseModel):
    username: str
    password: str


class ICPProviders(BaseModel):
    icp_providers: List[str]


class ICPProvider(Enum):
    FAUNA_MARIN = "FaunaMarin"

    def get_scraper_instance(self):
        if self == ICPProvider.FAUNA_MARIN:
            return FaunaMarinScraper(FaunaMarinSessionProvider())
        else:
            raise ValueError("Invalid provider")
