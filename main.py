import time
import json
import random
import requests
from playwright.sync_api import sync_playwright
import os
import random_user_agent


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@nvidia_fe"

gpu_cards = [
    {
        "name": "5090",
        "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT590"
    },
    {
        "name": "5080",
        "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT580"
    },
    {
        "name": "5070T",
        "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT570T"
    },
    {
        "name": "5070",
        "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT570"
    },
    {
        "name": "4090",
        "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT490"
    },
    {
        "name": "4080S",
        "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT480S"
    },
    {
        "name": "4070S",
        "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT470S"
    }
]

locales = ["sv-se", "es-es", "nb-no"]
last_status = {card["name"]: False for card in gpu_cards}

def send_telegram_message(message, chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message
    }
    requests.post(url, params=params)

def check_cards(context):
    for card in gpu_cards:
        for locale in ["sv-se", "en-us"]:
            url = f"{card['api_url']}&locale={locale}"
            try:
                data = fetch_json_in_browser(context, url)
                print(f"Checked card: {card['name']} - Result: {data}")
                if "listMap" in data and isinstance(data["listMap"], list):
                    is_active = any(item.get("is_active") == "true" for item in data["listMap"])
                    if is_active and not last_status[card["name"]]:
                        send_telegram_message(f"{card['name']} is now available! {data}", CHANNEL_ID)
                    last_status[card["name"]] = is_active
            except Exception as e:
                print(f"{card['name']} - Error: {e}")

def fetch_json_in_browser(context, url):
    page = context.new_page()
    page.goto(url)
    page_text = page.inner_text("pre")
    page.close()
    return json.loads(page_text)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=random_user_agent.get_user_agent()
        )
        while True:
            check_cards(context)
            time.sleep(60)

if __name__ == "__main__":
    main()
