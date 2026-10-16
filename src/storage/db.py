import sqlite3
from typing import Optional, List, Tuple
from datetime import datetime
from src.models.property import PropertyListing, OpportunityEvent, OpportunityType

class DatabaseManager:
    def __init__(self, db_path: str = "data/real_estate.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal TEXT NOT NULL,
                    portal_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    city TEXT NOT NULL,
                    zone TEXT,
                    price_cop REAL NOT NULL,
                    area_m2 REAL NOT NULL,
                    price_per_m2 REAL NOT NULL,
                    rooms INTEGER,
                    bathrooms INTEGER,
                    has_elevator INTEGER,
                    has_balcony INTEGER,
                    property_condition TEXT,
                    image_url TEXT,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    UNIQUE(portal, portal_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id INTEGER NOT NULL,
                    price_cop REAL NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY(property_id) REFERENCES properties(id)
                )
            """)
            conn.commit()

    def process_and_track_listing(self, listing: PropertyListing) -> OpportunityEvent:
        """
        Detecta si la propiedad es nueva, si bajó de precio o si se mantiene idéntica (CDC).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, price_cop FROM properties WHERE portal = ? AND portal_id = ?",
                (listing.portal, listing.portal_id)
            )
            row = cursor.fetchone()

            now_str = datetime.utcnow().isoformat()

            if row is None:
                # 1. Nueva Propiedad
                cursor.execute("""
                    INSERT INTO properties (
                        portal, portal_id, title, url, city, zone, price_cop, area_m2, 
                        price_per_m2, rooms, bathrooms, has_elevator, has_balcony, 
                        property_condition, image_url, first_seen_at, last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    listing.portal, listing.portal_id, listing.title, listing.url,
                    listing.city, listing.zone, listing.price_cop, listing.area_m2,
                    listing.price_per_m2, listing.rooms, listing.bathrooms,
                    1 if listing.has_elevator else 0,
                    1 if listing.has_balcony else 0,
                    listing.property_condition, listing.image_url,
                    now_str, now_str
                ))
                prop_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO price_history (property_id, price_cop, recorded_at) VALUES (?, ?, ?)",
                    (prop_id, listing.price_cop, now_str)
                )
                conn.commit()
                return OpportunityEvent(listing=listing, event_type=OpportunityType.NEW_LISTING)

            else:
                prop_id = row["id"]
                current_stored_price = row["price_cop"]

                # Actualizar última vez visto
                cursor.execute(
                    "UPDATE properties SET last_seen_at = ? WHERE id = ?",
                    (now_str, prop_id)
                )

                if listing.price_cop < current_stored_price:
                    # 2. Baja de Precio
                    drop_amount = current_stored_price - listing.price_cop
                    drop_pct = round((drop_amount / current_stored_price) * 100, 2)

                    cursor.execute("""
                        UPDATE properties 
                        SET price_cop = ?, price_per_m2 = ?
                        WHERE id = ?
                    """, (listing.price_cop, listing.price_per_m2, prop_id))

                    cursor.execute(
                        "INSERT INTO price_history (property_id, price_cop, recorded_at) VALUES (?, ?, ?)",
                        (prop_id, listing.price_cop, now_str)
                    )
                    conn.commit()

                    return OpportunityEvent(
                        listing=listing,
                        event_type=OpportunityType.PRICE_DROP,
                        previous_price_cop=current_stored_price,
                        price_drop_pct=drop_pct
                    )
                else:
                    conn.commit()
                    return OpportunityEvent(listing=listing, event_type=OpportunityType.NO_CHANGE)
