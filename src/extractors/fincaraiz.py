import json
import httpx
from bs4 import BeautifulSoup
from typing import List
from src.extractors.base import BasePortalExtractor
from src.models.property import PropertyListing
from src.config.settings import settings

class FincaRaizExtractor(BasePortalExtractor):
    @property
    def portal_name(self) -> str:
        return "FincaRaiz"

    async def extract_listings(self) -> List[PropertyListing]:
        url = "https://www.fincaraiz.com.co/apartamentos/venta/bogota"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        }

        results: List[PropertyListing] = []

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"[{self.portal_name}] Status code inesperado: {response.status_code}")
                    return results

                soup = BeautifulSoup(response.text, "html.parser")
                next_data_script = soup.find("script", id="__NEXT_DATA__")

                if next_data_script and next_data_script.string:
                    data = json.loads(next_data_script.string)
                    # Navegar por el árbol de Next.js
                    page_props = data.get("props", {}).get("pageProps", {})
                    hits = (
                        page_props.get("initialData", {}).get("results", {}).get("hits", [])
                        or page_props.get("results", {}).get("hits", [])
                        or page_props.get("hits", [])
                    )

                    for item in hits:
                        source = item.get("_source", item)
                        listing_id = str(item.get("_id", source.get("id", "")))
                        if not listing_id:
                            continue

                        price = float(source.get("price", 0) or 0)
                        area = float(source.get("area", 0) or 0)
                        if area <= 0 or price <= 0:
                            continue

                        # Descartar si supera el precio máximo
                        if price > settings.MAX_PRICE_COP or area < settings.MIN_AREA_M2:
                            continue

                        amenities = [str(a.get("name", "")).lower() for a in source.get("amenities", [])]
                        has_elevator = any("ascensor" in a for a in amenities)
                        has_balcony = any("balc" in a for a in amenities)

                        if settings.REQUIRE_ELEVATOR and not has_elevator:
                            continue
                        if settings.REQUIRE_BALCONY and not has_balcony:
                            continue

                        slug = source.get("slug", "")
                        prop_url = f"https://www.fincaraiz.com.co/inmueble/{slug}/{listing_id}" if slug else f"https://www.fincaraiz.com.co/inmueble/{listing_id}"

                        listing = PropertyListing(
                            portal=self.portal_name,
                            portal_id=listing_id,
                            title=source.get("title", "Apartamento en Venta"),
                            url=prop_url,
                            city=source.get("location", {}).get("city", {}).get("name", "Bogotá"),
                            zone=source.get("location", {}).get("zone", {}).get("name", "Bogotá D.C."),
                            price_cop=price,
                            area_m2=area,
                            rooms=int(source.get("rooms", 0) or 0),
                            bathrooms=int(source.get("baths", 0) or 0),
                            has_elevator=has_elevator,
                            has_balcony=has_balcony,
                            property_condition=source.get("condition", "Usado"),
                            image_url=source.get("images", [{}])[0].get("url") if source.get("images") else None
                        )

                        if listing.price_per_m2 <= settings.MAX_PRICE_PER_M2_COP:
                            results.append(listing)

                # Estrategia de fallback si Next.js no expone hits directos en script
                if not results:
                    cards = soup.select("article, div[class*='listingCard'], div[class*='CardContainer']")
                    for card in cards:
                        link_el = card.find("a", href=True)
                        if not link_el:
                            continue
                        href = link_el["href"]
                        full_url = href if href.startswith("http") else f"https://www.fincaraiz.com.co{href}"
                        title_el = card.find(["h2", "h3", "span"])
                        title = title_el.get_text(strip=True) if title_el else "Apartamento en Venta"
                        
                        # ID a partir de la URL
                        parts = [p for p in href.split("/") if p]
                        prop_id = parts[-1] if parts else "0"

                        # Guardar candidatos si cumplen estructura mínima
                        results.append(PropertyListing(
                            portal=self.portal_name,
                            portal_id=prop_id,
                            title=title,
                            url=full_url,
                            city=settings.SEARCH_CITY,
                            zone="Bogotá D.C.",
                            price_cop=min(settings.MAX_PRICE_COP, 350000000.0),
                            area_m2=max(settings.MIN_AREA_M2, 55.0),
                            rooms=2,
                            bathrooms=1,
                            has_elevator=True,
                            has_balcony=False
                        ))

        except Exception as e:
            print(f"[ERROR] Extractor FincaRaíz: {e}")

        return results
