import asyncio
from src.storage.db import DatabaseManager
from src.extractors.fincaraiz import FincaRaizExtractor
from src.extractors.metrocuadrado import MetroCuadradoExtractor
from src.extractors.ciencuadras import CienCuadrasExtractor
from src.services.notifier import EmailNotifier
from src.services.exporter import ExcelExporter
from src.models.property import OpportunityType

async def run_pipeline():
    print("======================================================")
    print("🚀 INICIANDO MONITOR INMOBILIARIO DE OPORTUNIDADES")
    print("======================================================")

    db = DatabaseManager()
    extractors = [
        FincaRaizExtractor(),
        MetroCuadradoExtractor(),
        CienCuadrasExtractor()
    ]
    notifier = EmailNotifier()

    all_opportunities = []

    for extractor in extractors:
        print(f"[*] Extrayendo listados desde {extractor.portal_name}...")
        listings = await extractor.extract_listings()
        print(f"[*] {len(listings)} propiedades cumplen los criterios iniciales en {extractor.portal_name}.")

        for listing in listings:
            event = db.process_and_track_listing(listing)
            if event.event_type in (OpportunityType.NEW_LISTING, OpportunityType.PRICE_DROP):
                all_opportunities.append(event)

    print(f"\n[+] Total de oportunidades detectadas (Nuevas o Bajas de precio): {len(all_opportunities)}")

    if all_opportunities:
        ExcelExporter.export_opportunities(all_opportunities)
        await notifier.send_report(all_opportunities)
    else:
        print("[-] No se detectaron variaciones ni nuevas propiedades en esta ejecución.")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
