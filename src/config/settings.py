from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Base de datos
    DATABASE_PATH: str = "data/real_estate.db"

    # Filtros de búsqueda (Valores por defecto orientados a inversión)
    SEARCH_CITY: str = "Bogota"
    SEARCH_ZONE: Optional[str] = None
    MAX_PRICE_COP: float = 450_000_000.0        # Precio máximo en COP
    MAX_PRICE_PER_M2_COP: float = 7_500_000.0   # Precio máx por m²
    MIN_AREA_M2: float = 40.0                   # Superficie mínima
    MIN_ROOMS: int = 1                          # Ambientes / Habitaciones mínimas
    REQUIRE_ELEVATOR: bool = False
    REQUIRE_BALCONY: bool = False

    # Configuración de Correo (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_TO: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
