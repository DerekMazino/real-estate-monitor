import re
import httpx
from bs4 import BeautifulSoup
from typing import List
from src.extractors.base import BasePortalExtractor
from src.models.property import PropertyListing
from src.config.settings import settings

class MetroCuadradoExtractor(BasePortalExtractor):
    @property
    def portal_name(self) -> str:
        return "MetroCuadrado"

    async def extract_listings(self) -> List[PropertyListing]:
        # Formato de URL directa con query params estándar de Metrocuadrado
        url = f"https://www.metrocuadrado.com/apartamento/venta/bogota/?precio-hasta={int(settings.MAX_PRICE_COP)}&area-desde={int(settings.MIN_AREA_M2)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CO,es-419;q=0.9,es;q=0.8",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"'
        }

        results: List[PropertyListing] = []

        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return results

                soup = BeautifulSoup(response.text, "html.parser")

                # Seleccionar contenedores de inmuebles
                cards = soup.find_all(lambda tag: tag.name in ["div", "article", "li"] and (
                    "card" in tag.get("class", []) or 
                    any("listing" in c.lower() for c in tag.get("class", [])) or
                    tag.find("a", href=lambda h: h and ("/inmueble/" in h or "/apartamento/" in h))
                ))

                for card in cards:
                    link = card.find("a", href=lambda h: h and ("/inmueble/" in h or "/apartamento/" in h))
                    if not link:
                        continue
                    href = link["href"]
                    full_url = href if href.startswith("http") else f"https://www.metrocuadrado.com{href}"

                    # Evitar duplicar dentro del mismo ciclo
                    if any(r.url == full_url for r in results):
                        continue

                    title_el = card.find(["h2", "h3"]) or link
                    title = title_el.get_text(strip=True) if title_el else "Apartamento en Venta"

                    text = card.get_text(" ", strip=True)

                    # Regex para extraer precio
                    price_match = re.search(r"\$\s*([\d\.,]+)", text)
                    if not price_match:
                        continue
                    raw_price = price_match.group(1).replace(".", "").replace(",", "")
                    try:
                        price = float(raw_price)
                    except ValueError:
                        continue

                    # Regex para extraer m2
                    area_match = re.search(r"(\d+[\.,]?\d*)\s*(?:m²|m2|mts)", text, re.IGNORECASE)
                    area = float(area_match.group(1).replace(",", ".")) if area_match else 0.0

                    if price <= 0 or area <= 0 or price > settings.MAX_PRICE_COP or area < settings.MIN_AREA_M2:
                        continue

                    # Habitaciones y baños
                    rooms_match = re.search(r"(\d+)\s*(?:hab|alc|cuarto)", text, re.IGNORECASE)
                    rooms = int(rooms_match.group(1)) if rooms_match else 1

                    baths_match = re.search(r"(\d+)\s*(?:baño|bano)", text, re.IGNORECASE)
                    baths = int(baths_match.group(1)) if baths_match else 1

                    has_elevator = "ascensor" in text.lower()
                    has_balcony = "balc" in text.lower()

                    if settings.REQUIRE_ELEVATOR and not has_elevator:
                        continue
                    if settings.REQUIRE_BALCONY and not has_balcony:
                        continue

                    id_match = re.search(r"(\d+)(?:[/?#]|$)", full_url)
                    prop_id = id_match.group(1) if id_match else str(abs(hash(full_url)))

                    listing = PropertyListing(
                        portal=self.portal_name,
                        portal_id=prop_id,
                        title=title[:80],
                        url=full_url,
                        city="Bogotá",
                        zone="Bogotá D.C.",
                        price_cop=price,
                        area_m2=area,
                        rooms=rooms,
                        bathrooms=baths,
                        has_elevator=has_elevator,
                        has_balcony=has_balcony
                    )

                    if listing.price_per_m2 <= settings.MAX_PRICE_PER_M2_COP:
                        results.append(listing)

        except Exception as e:
            print(f"[ERROR] Extractor MetroCuadrado: {e}")

        return results
