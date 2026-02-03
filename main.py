import asyncio
from pyicloud import PyiCloudService
from datetime import datetime, timedelta, timezone
import json
import os
import requests
from dotenv import load_dotenv

# Load env variables
ICLOUD_EMAIL = os.environ["ICLOUD_EMAIL"]
ICLOUD_PASSWORD = os.environ["ICLOUD_PASSWORD"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
CHECK_INTERVAL = 60  # seconden
DATA_FILE = 'sent_events.json'

# iCloud login
api = PyiCloudService(ICLOUD_EMAIL, ICLOUD_PASSWORD)

# Load sent events
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        sent_events = set(json.load(f))
else:
    sent_events = set()

def send_webhook(message):
    data = {"content": message}
    requests.post(DISCORD_WEBHOOK, json=data)

async def save_sent_events():
    with open(DATA_FILE, 'w') as f:
        json.dump(list(sent_events), f)

async def check_calendar():
    while True:
        now = datetime.now(timezone.utc)
        # Haal alle afspraken voor de komende 24 uur
        events = api.calendar.events(now, now + timedelta(days=1))
        for event in events:
            event_time = event['startDate'].astimezone(timezone.utc)
            reminder_time = event_time - timedelta(hours=1)
            guid = event['guid']

            # Check of het tijd is voor de melding
            if reminder_time <= now < reminder_time + timedelta(seconds=CHECK_INTERVAL):
                if guid not in sent_events:
                    send_webhook(f"⏰ Over 1 uur: **{event['title']}**\n📅 {event_time.astimezone().strftime('%H:%M %d-%m-%Y')}")
                    sent_events.add(guid)
                    await save_sent_events()
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    print("SheduleBot is gestart!")
    await check_calendar()

asyncio.run(main())
