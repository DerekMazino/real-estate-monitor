import httpx
from typing import List
from src.extractors.base import BasePortalExtractor
from src.models.property import PropertyListing
from src.config.settings import settings

class CienCuadrasExtractor(BasePortalExtractor):
    @property
    def portal_name(self) -> str:
        return "Ciencuadras"

    async def extract_listings(self) -> List[PropertyListing]:
        url = "https://api.ciencuadras.com/v2/real-estate/search"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://www.ciencuadras.com",
            "Referer": "https://www.ciencuadras.com/"
        }

        payload = {
            "transactionType": "VENTA",
            "propertyType": ["APARTAMENTO"],
            "city": "BOGOTA",
            "priceMax": int(settings.MAX_PRICE_COP),
            "areaMin": int(settings.MIN_AREA_M2),
            "limit": 30,
            "page": 1
        }

        results: List[PropertyListing] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    # Fallback a petición GET pública si la API v2 exige token
                    fallback_url = "https://www.ciencuadras.com/api/search/properties"
                    params = {
                        "tipoTransaccion": "venta",
                        "tipoInmueble": "apartamento",
                        "ciudad": "bogota",
                        "precioHasta": int(settings.MAX_PRICE_COP),
                        "areaDesde": int(settings.MIN_AREA_M2)
                    }
                    response = await client.get(fallback_url, params=params, headers=headers)
                    if response.status_code != 200:
                        return results

                data = response.json()
                items = data.get("data", []) or data.get("properties", []) or data.get("results", [])

                for item in items:
                    prop_id = str(item.get("id", item.get("propertyId", "")))
                    if not prop_id:
                        continue

                    price = float(item.get("price", item.get("salePrice", 0)) or 0)
                    area = float(item.get("area", item.get("builtArea", 0)) or 0)
                    if area <= 0 or price <= 0:
                        continue

                    features = [str(f).lower() for f in item.get("features", []) + item.get("amenities", [])]
                    has_elevator = any("ascensor" in f for f in features)
                    has_balcony = any("balc" in f for f in features)

                    if settings.REQUIRE_ELEVATOR and not has_elevator:
                        continue
                    if settings.REQUIRE_BALCONY and not has_balcony:
                        continue

                    path = item.get("slug", item.get("url", f"inmueble/{prop_id}"))
                    prop_url = path if path.startswith("http") else f"https://www.ciencuadras.com/{path.lstrip('/')}"

                    listing = PropertyListing(
                        portal=self.portal_name,
                        portal_id=prop_id,
                        title=item.get("title", "Apartamento en Venta"),
                        url=prop_url,
                        city="Bogotá",
                        zone=item.get("neighborhood", item.get("zone", "Bogotá")),
                        price_cop=price,
                        area_m2=area,
                        rooms=int(item.get("rooms", item.get("bedrooms", 0)) or 0),
                        bathrooms=int(item.get("bathrooms", 0) or 0),
                        has_elevator=has_elevator,
                        has_balcony=has_balcony,
                        property_condition=item.get("condition", "Usado"),
                        image_url=item.get("mainImage", item.get("image"))
                    )

                    if listing.price_per_m2 <= settings.MAX_PRICE_PER_M2_COP:
                        results.append(listing)

        except Exception as e:
            print(f"[ERROR] Extractor Ciencuadras: {e}")

        return results
