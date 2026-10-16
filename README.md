# 🏠 Real Estate Investment Monitor & CDC Engine

[![Language: Python 3.11+](https://img.shields.io/badge/Language-Python%203.11+-blue.svg)](#)
[![Data Modeling: Pydantic v2](https://img.shields.io/badge/Data%20Modeling-Pydantic%20v2-red.svg)](#)
[![Storage: SQLite Relational](https://img.shields.io/badge/Storage-SQLite%203-lightgrey.svg)](#)
[![Workflow: Git Flow](https://img.shields.io/badge/Workflow-Git%20Flow-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Herramienta automatizada de extracción, normalización e identificación de oportunidades de inversión inmobiliaria en Colombia. Implementa un patrón de **Change Data Capture (CDC)** sobre listados inmobiliarios para detectar nuevas publicaciones, rastrear rebajas de precio históricas y alertar diariamente mediante reportes consolidados en HTML y planillas Excel.

---

## 🎯 Arquitectura del Pipeline

```mermaid
flowchart TD
    subgraph Extractors [1. Extracción de Listados]
        E1[Finca Raíz Connector] -->|JSON/HTML Stream| Norm[Normalizador Pydantic]
        E2[MetroCuadrado Connector] -->|Web Stream| Norm
        E3[Ciencuadras Connector] -->|API Stream| Norm
    end

    subgraph CDC_Engine [2. Procesamiento & CDC]
        Norm --> Filter[Filtros de Negocio: m2, Presupuesto, Comodidades]
        Filter --> CDC{Evaluador de Estados CDC}
        CDC -->|Nuevo ID| New[Evento: NUEVA_PROPIEDAD]
        CDC -->|Precio Menor| Drop[Evento: BAJA_DE_PRECIO]
        CDC -->|Sin Variación| Noop[Evento: SIN_CAMBIO]
    end

    subgraph Storage [3. Persistencia Relacional]
        New --> DB[(SQLite: properties)]
        Drop --> DB
        Drop --> Hist[(SQLite: price_history)]
    end

    subgraph Dispatch [4. Alertas & Reportería]
        DB --> Excel[Exportador Excel con URLs directas]
        DB --> Email[Servicio SMTP: Email HTML Enriquecido]
        DB -.-> Telegram[Extensión: Telegram Bot]
    end
```

---

## 🚀 Características Principales

* **Normalización de Datos Inmobiliarios:** Cálculo automático de métricas de rendimiento como valor por metro cuadrado ($\text{COP}/\text{m}^2$), ambientes, superficie y filtrado de comodidades (balcón, ascensor, estado).
* **CDC Inmobiliario & Detección de Bajas:** Rastrea el historial de cambios en cada propiedad. Si un inmueble reduce su precio, calcula el porcentaje de descuento respecto a su valor anterior y preserva la auditoría en `price_history`.
* **Deduplicación Estricta:** Identificación única por combinación de portal y clave de publicación, evitando falsos positivos e inundación de reportes.
* **Módulo de Notificaciones Desacoplado:** Arquitectura extensible mediante la interfaz `BaseNotifier`. Soporta actualmente envíos por correo electrónico (HTML responsivo vía SMTP) y está preparado para conectarse a bots de mensajería (Telegram).
* **Exportación Automatizada:** Generación de planillas estructuradas en `.xlsx` con hipervínculos directos a las publicaciones originales.

---

## 🛠️ Instalación y Uso Local

### 1. Clonar y configurar entorno

```bash
git clone https://github.com/<tu-usuario>/real-estate-monitor.git
cd real-estate-monitor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar Criterios de Inversión (`.env`)

Copia la plantilla de configuración:

```bash
cp .env.example .env
```

Ajusta tus parámetros en `.env`:

```ini
SEARCH_CITY=Bogota
MAX_PRICE_COP=400000000
MAX_PRICE_PER_M2_COP=7000000
MIN_AREA_M2=45
MIN_ROOMS=2
REQUIRE_ELEVATOR=false
REQUIRE_BALCONY=false

# Opcional: Credenciales SMTP para envíos automáticos de correo
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_app_password
EMAIL_FROM=tu_correo@gmail.com
EMAIL_TO=destinatario@correo.com
```

### 3. Ejecutar el Monitor

```bash
python -m src.main
```

Los resultados se almacenarán en `data/real_estate.db`, exportando la planilla en `data/oportunidades_YYYYMMDD_HHMMSS.xlsx` y el reporte visual en `data/last_report.html` (o enviándolo directamente si se configuraron credenciales SMTP).

---

## 👤 Autor

**Juan Camilo Marín García**  
*SQL Data Engineer & Backend Architecture Specialist*