import time
import json
import os
import requests
import traceback
from playwright.sync_api import sync_playwright
import ua_generator
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set")
    raise Exception("BOT_TOKEN environment variable not set")

CHANNEL_ID = "@nvidia_fe"
DEBUG_CHANNEL_ID = "@nvidia_fe_debug"

gpu_cards = [
    {"name": "5090", "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT590"},
    {"name": "5080", "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT580"},
    {"name": "5070T", "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT570T"},
    {"name": "5070", "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT570"},
    {"name": "4090", "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT490"},
    {"name": "4080S", "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT480S"},
    {"name": "4070S", "api_url": "https://api.store.nvidia.com/partner/v1/feinventory?skus=NVGFT470S"}
]

locales = ["sv-se", "es-es"]
last_status = {card["name"]: False for card in gpu_cards}

def send_telegram_message(message, chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    r = requests.post(url, params=params)
    if not r.ok:
        logger.error(f"Failed to send message to Telegram: {r.text}")

def fetch_json_in_browser(context, url):
    with context.new_page() as page:
        response = page.goto(url, wait_until="networkidle")
        if response is None or not response.ok:
            raise Exception(f"Failed to load URL: {url}")
        page_text = page.inner_text("pre")
    return json.loads(page_text)

def check_cards(context):
    for card in gpu_cards:
        card_available = False
        result_data = None
        for locale in locales:
            full_url = f"{card['api_url']}&locale={locale}"
            try:
                data = fetch_json_in_browser(context, full_url)
                logger.info(f"Fetched Data for {card['name']} in {locale}: {data}")
                result_data = data
                if "listMap" in data and isinstance(data["listMap"], list):
                    if any(item.get("is_active") == "true" for item in data["listMap"]):
                        card_available = True
                        break
            except Exception as e:
                logger.error(f"Error checking {card['name']} for locale {locale}: {str(e)}")
                send_telegram_message(f"Error checking {card['name']} for locale {locale}: {str(e)}", DEBUG_CHANNEL_ID)
        if card_available and not last_status[card["name"]]:
            logger.info(f"{card['name']} is now available! {result_data}")
            send_telegram_message(f"{card['name']} is now available! {result_data}", CHANNEL_ID)
        last_status[card["name"]] = card_available

def main():
    send_telegram_message("Bot started", DEBUG_CHANNEL_ID)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        try:
            while True:
                context = browser.new_context(
                    user_agent=str(ua_generator.generate()),
                    locale="en-US"
                )
                try:
                    check_cards(context)
                except Exception as e:
                    send_telegram_message(f"Error in check loop: {str(e)}\n{traceback.format_exc()}", DEBUG_CHANNEL_ID)
                finally:
                    context.close()
                time.sleep(60)
        except KeyboardInterrupt:
            send_telegram_message("Bot stopped by user", DEBUG_CHANNEL_ID)
        except Exception as e:
            send_telegram_message(f"Error in main loop: {str(e)}\n{traceback.format_exc()}", DEBUG_CHANNEL_ID)
            raise e

if __name__ == "__main__":
    logger.info("Starting bot")
    main()
