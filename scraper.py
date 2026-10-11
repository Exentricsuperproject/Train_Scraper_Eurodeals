import json
import random
from datetime import datetime

print(f"Starting price update at {datetime.now()}...")

# In a real script, Playwright would scrape live pages here.
# For now, we simulate dynamic price fluctuations to prove the automation works!
updated_deals = [
    {
        "destination": "Antwerp, Belgium",
        "price": random.randint(22, 40), # Randomly updates price to test sorting
        "duration": "1h 15m",
        "link": "https://www.thetrainline.com"
    },
    {
        "destination": "Düsseldorf, Germany",
        "price": random.randint(25, 45),
        "duration": "2h 15m",
        "link": "https://www.thetrainline.com"
    },
    {
        "destination": "Brussels, Belgium",
        "price": random.randint(30, 55),
        "duration": "1h 50m",
        "link": "https://www.thetrainline.com"
    },
    {
        "destination": "Paris, France",
        "price": random.randint(45, 90),
        "duration": "3h 20m",
        "link": "https://www.thetrainline.com"
    }
]

# Save the fresh prices back into prices.json
with open("prices.json", "w", encoding="utf-8") as f:
    json.dump(updated_deals, f, indent=4)

print("prices.json successfully updated with latest data!")
