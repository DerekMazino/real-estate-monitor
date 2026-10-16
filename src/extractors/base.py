from abc import ABC, abstractmethod
from typing import List
from src.models.property import PropertyListing

class BasePortalExtractor(ABC):
    @property
    @abstractmethod
    def portal_name(self) -> str:
        pass

    @abstractmethod
    async def extract_listings(self) -> List[PropertyListing]:
        pass
