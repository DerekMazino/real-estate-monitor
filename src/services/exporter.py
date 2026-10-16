import pandas as pd
from typing import List
from datetime import datetime
import os
from src.models.property import OpportunityEvent

class ExcelExporter:
    @staticmethod
    def export_opportunities(events: List[OpportunityEvent], output_dir: str = "data"):
        if not events:
            return None

        os.makedirs(output_dir, exist_ok=True)
        filename = f"oportunidades_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        full_path = os.path.join(output_dir, filename)

        records = []
        for evt in events:
            records.append({
                "Evento": evt.event_type.value,
                "Portal": evt.listing.portal,
                "Título": evt.listing.title,
                "Ciudad": evt.listing.city,
                "Zona": evt.listing.zone,
                "Precio (COP)": evt.listing.price_cop,
                "Precio Anterior (COP)": evt.previous_price_cop if evt.previous_price_cop else "",
                "% Rebaja": f"{evt.price_drop_pct}%" if evt.price_drop_pct else "",
                "Área (m²)": evt.listing.area_m2,
                "Precio por m² (COP)": evt.listing.price_per_m2,
                "Habitaciones": evt.listing.rooms,
                "Baños": evt.listing.bathrooms,
                "Ascensor": "Sí" if evt.listing.has_elevator else "No",
                "Balcón": "Sí" if evt.listing.has_balcony else "No",
                "Enlace": evt.listing.url,
                "Detectado": evt.detected_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        df = pd.DataFrame(records)
        df.to_excel(full_path, index=False)
        print(f"[EXPORTER] Planilla generada con éxito: {full_path}")
        return full_path
