from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime
from enum import Enum

class OpportunityType(str, Enum):
    NEW_LISTING = "NUEVA_PROPIEDAD"
    PRICE_DROP = "BAJA_DE_PRECIO"
    NO_CHANGE = "SIN_CAMBIO"

class PropertyListing(BaseModel):
    portal: str
    portal_id: str
    title: str
    url: str
    city: str
    zone: Optional[str] = "No especificada"
    price_cop: float
    area_m2: float
    rooms: int = 0
    bathrooms: int = 0
    has_elevator: bool = False
    has_balcony: bool = False
    property_condition: Optional[str] = "Usado"
    image_url: Optional[str] = None
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def price_per_m2(self) -> float:
        if self.area_m2 > 0:
            return round(self.price_cop / self.area_m2, 2)
        return 0.0

class OpportunityEvent(BaseModel):
    listing: PropertyListing
    event_type: OpportunityType
    previous_price_cop: Optional[float] = None
    price_drop_pct: Optional[float] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
