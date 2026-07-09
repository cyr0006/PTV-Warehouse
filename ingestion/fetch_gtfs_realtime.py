import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

FEEDS = {
    "trip_updates": os.getenv("GTFS_TRIP_UPDATES_URL"),
    "vehicle_positions": os.getenv("GTFS_VEHICLE_POSITIONS_URL"),
}

HEADERS = {
    "KeyID": os.getenv("GTFS_SUBSCRIPTION_KEY")
}

print(repr(os.getenv("GTFS_SUBSCRIPTION_KEY")))


def fetch_feed(name: str, url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()  #if key/url is wrong, raise error, stop script 

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = f"raw/{name}"
    os.makedirs(out_dir, exist_ok=True)

    out_path = f"{out_dir}/{name}_{timestamp}.pb"
    with open(out_path, "wb") as f:
        f.write(response.content)

    print(f"Saved {name}: {len(response.content)} bytes -> {out_path}")
    return out_path


if __name__ == "__main__":
    for feed_name, feed_url in FEEDS.items():
        if not feed_url:
            print(f"Skipping {feed_name}: no URL in .env")
            continue
        fetch_feed(feed_name, feed_url)