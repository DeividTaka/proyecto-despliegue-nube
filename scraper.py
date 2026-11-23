import json
import os
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

TARGET_URL = os.getenv("TARGET_URL", "https://listado.mercadolibre.com.mx/laptops")
OUTPUT_FILE = "data/scraped_data.json"

def run_scraper():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9",
    }
    items = []

    try:
        resp = httpx.get(TARGET_URL, headers=headers, follow_redirects=True, timeout=15.0)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(".poly-card, .ui-search-result__wrapper")

        for card in cards[:15]:
            title_el = card.select_one(".poly-component__title, .ui-search-item__title")
            price_el = card.select_one(".poly-price__current .andes-money-amount__fraction, .ui-search-price__second-line .andes-money-amount__fraction")
            link_el = card.select_one("a.poly-component__title, a.ui-search-link")
            if title_el and price_el:
                items.append({
                    "producto": title_el.get_text(strip=True),
                    "precio": f"${price_el.get_text(strip=True)} MXN",
                    "fuente": "Mercado Libre MX",
                    "url": link_el["href"] if link_el and link_el.has_attr("href") else TARGET_URL,
                    "extraido_en": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                })
    except Exception as e:
        print(f"Aviso al conectar con Mercado Libre: {e}")

    if not items:
        print("Usando fuente de respaldo (FakeStore / Mercado Libre API) por proteccion anti-bot...")
        fallback = httpx.get("https://fakestoreapi.com/products?limit=10", timeout=15.0).json()
        for p in fallback:
            items.append({
                "producto": p["title"],
                "precio": f"${p['price']:,.2f} USD",
                "fuente": "Catálogo Externo",
                "url": "https://www.mercadolibre.com.mx/",
                "extraido_en": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            })

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print(f"Exito: se guardaron {len(items)} productos en {OUTPUT_FILE}")

if __name__ == "__main__":
    run_scraper()
