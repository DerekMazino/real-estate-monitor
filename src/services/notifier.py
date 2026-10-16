from abc import ABC, abstractmethod
from typing import List
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from src.models.property import OpportunityEvent, OpportunityType
from src.config.settings import settings

class BaseNotifier(ABC):
    @abstractmethod
    async def send_report(self, events: List[OpportunityEvent]):
        pass

class EmailNotifier(BaseNotifier):
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }
            .container { max-width: 750px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .header { background: #1e293b; color: #ffffff; padding: 24px; text-align: center; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
            .badge-new { background-color: #dbeafe; color: #1e40af; }
            .badge-drop { background-color: #dcfce7; color: #166534; }
            .card { border-bottom: 1px solid #e2e8f0; padding: 20px; display: flex; flex-direction: column; }
            .card:last-child { border-bottom: none; }
            .price { font-size: 20px; font-weight: bold; color: #0f172a; margin: 8px 0; }
            .meta { font-size: 14px; color: #64748b; margin-bottom: 12px; }
            .btn { display: inline-block; background-color: #2563eb; color: #ffffff !important; text-decoration: none; padding: 10px 16px; border-radius: 6px; font-weight: 500; font-size: 14px; width: fit-content; }
            .footer { padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; background: #f8fafc; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🏢 Monitor Inmobiliario de Oportunidades</h2>
                <p>Se detectaron {{ events|length }} oportunidades que cumplen tus filtros</p>
            </div>
            {% for evt in events %}
            <div class="card">
                <div>
                    {% if evt.event_type.value == 'NUEVA_PROPIEDAD' %}
                        <span class="badge badge-new">✨ Nueva Oportunidad</span>
                    {% else %}
                        <span class="badge badge-drop">🔥 Bajó de Precio (-{{ evt.price_drop_pct }}%)</span>
                    {% endif %}
                </div>
                <h3 style="margin: 8px 0;">{{ evt.listing.title }} ({{ evt.listing.portal }})</h3>
                <div class="price">
                    ${{ "{:,.0f}".format(evt.listing.price_cop) }} COP
                    {% if evt.previous_price_cop %}
                        <span style="font-size: 14px; color: #ef4444; text-decoration: line-through;">
                            ${{ "{:,.0f}".format(evt.previous_price_cop) }}
                        </span>
                    {% endif %}
                </div>
                <div class="meta">
                    📍 <strong>{{ evt.listing.zone }}, {{ evt.listing.city }}</strong> | 
                    📐 {{ evt.listing.area_m2 }} m² | 
                    💰 <strong>${{ "{:,.0f}".format(evt.listing.price_per_m2) }}/m²</strong> | 
                    🛏️ {{ evt.listing.rooms }} hab | 
                    🚿 {{ evt.listing.bathrooms }} baños | 
                    🛗 Ascensor: {{ "Sí" if evt.listing.has_elevator else "No" }} | 
                    🌅 Balcón: {{ "Sí" if evt.listing.has_balcony else "No" }}
                </div>
                <a href="{{ evt.listing.url }}" class="btn" target="_blank">Ver Publicación Completa &rarr;</a>
            </div>
            {% endfor %}
            <div class="footer">
                Reporte automatizado generado por Real Estate Monitor Portfolio Suite.
            </div>
        </div>
    </body>
    </html>
    """

    async def send_report(self, events: List[OpportunityEvent]):
        if not events:
            print("[NOTIFIER] No hay nuevas oportunidades para reportar.")
            return

        # Si no hay credenciales SMTP configuradas, genera el archivo HTML localmente para inspección
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print("[NOTIFIER] Credenciales SMTP no configuradas. Guardando reporte HTML en 'data/last_report.html'...")
            template = Template(self.HTML_TEMPLATE)
            rendered_html = template.render(events=events)
            with open("data/last_report.html", "w", encoding="utf-8") as f:
                f.write(rendered_html)
            print("[NOTIFIER] Reporte guardado localmente en data/last_report.html")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎯 [Oportunidad Inmobiliaria] {len(events)} propiedades detectadas"
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = settings.EMAIL_TO

        template = Template(self.HTML_TEMPLATE)
        html_content = template.render(events=events)
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, [settings.EMAIL_TO], msg.as_string())
            print(f"[NOTIFIER] Correo enviado exitosamente a {settings.EMAIL_TO}")
        except Exception as e:
            print(f"[ERROR SMTP] No se pudo enviar el correo: {e}")

# Extensibilidad lista: Para Telegram, simplemente se implementa:
# class TelegramNotifier(BaseNotifier):
#     async def send_report(self, events: List[OpportunityEvent]): ...
