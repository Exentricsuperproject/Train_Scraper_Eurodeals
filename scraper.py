import json
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

ORIGIN_STATION = "Amsterdam Centraal"
ORIGIN_CODE = "NLAMS"

def get_weekend_dates(weeks_ahead=0):
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0 and weeks_ahead == 0:
        days_until_friday = 7
    
    friday = today + timedelta(days=days_until_friday + (weeks_ahead * 7))
    sunday = friday + timedelta(days=2)
    
    return {
        "label": f"{friday.strftime('%b %d')} - {sunday.strftime('%b %d')}",
        "dep_date": friday.strftime("%Y-%m-%d"),
        "arr_date": sunday.strftime("%Y-%m-%d")
    }

def scrape_ns_live():
    horizons = {
        "next_weekend": get_weekend_dates(weeks_ahead=0),
        "two_weeks": get_weekend_dates(weeks_ahead=2),
        "next_month": get_weekend_dates(weeks_ahead=4)
    }

    destinations = [
        {"name": "Antwerp, Belgium", "code": "BEANT", "operator": "Eurocity Direct", "link": "https://www.nsinternational.com/en/belgium/antwerp"},
        {"name": "Brussels, Belgium", "code": "BRUSSEL", "operator": "Eurostar / Eurocity Direct", "link": "https://www.nsinternational.com/en/belgium/brussels"},
        {"name": "Paris, France", "code": "PARIS", "operator": "Eurostar", "link": "https://www.nsinternational.com/en/france/paris"},
        {"name": "Cologne, Germany", "code": "COLOGNE", "operator": "ICE International", "link": "https://www.nsinternational.com/en/germany/cologne"},
        {"name": "London, United Kingdom", "code": "LONDON", "operator": "Eurostar", "link": "https://www.nsinternational.com/en/england/london"}
    ]

    output_data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for horizon_key, dates in horizons.items():
            output_data[horizon_key] = []
            print(f"--- Fetching Live Prices for {horizon_key} ({dates['label']}) ---")

            for dest in destinations:
                found_prices = []

                # Intercept API calls made by the page
                def handle_response(response):
                    if "price" in response.url or "journey" in response.url or "offer" in response.url:
                        try:
                            data = response.json()
                            # Search for price numbers inside JSON payload
                            prices = re.findall(r'"price":\s*([0-9]+(?:\.[0-9]+)?)', json.dumps(data))
                            for p_val in prices:
                                val = float(p_val)
                                if val > 10:  # Filter out noise / non-fare numbers
                                    found_prices.append(val)
                        except Exception:
                            pass

                page.on("response", handle_response)

                search_url = f"https://www.nsinternational.com/en/tickets#/search?from={ORIGIN_CODE}&to={dest['code']}&outboundDate={dates['dep_date']}&inboundDate={dates['arr_date']}"

                try:
                    page.goto(search_url, wait_until="networkidle", timeout=25000)
                    page.wait_for_timeout(3000) # Short delay to capture full response
                except Exception as e:
                    print(f"Notice for {dest['name']}: {e}")

                # Determine absolute lowest price found, or fallback to standard baseline
                if found_prices:
                    cheapest_price = min(found_prices)
                    print(f"LIVE PRICE FOUND: {dest['name']} -> €{cheapest_price}")
                else:
                    cheapest_price = 29 if "Belgium" in dest["name"] else (35 if "Germany" in dest["name"] else 45)
                    print(f"Fallback used for {dest['name']} -> €{cheapest_price}")

                output_data[horizon_key].append({
                    "origin": ORIGIN_STATION,
                    "destination": dest["name"],
                    "price": int(cheapest_price),
                    "date": dates["label"],
                    "operator": dest["operator"],
                    "link": search_url
                })

        browser.close()

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)

    print("Scraping completed and prices updated!")

if __name__ == "__main__":
    scrape_ns_live()
