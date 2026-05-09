"""
Run this FIRST to explore the GO Transit API and confirm:
  - Exact stop codes for Markham GO and Union Station
  - Stouffville line code
  - JSON structure of next-service and trip-stops responses

Usage:
    python scripts/probe_go.py

Saves raw JSON to samples/ so you can inspect offline without hammering the API.
After running, update HOME_STATION / WORK_STATION / LINE in .env if the codes differ.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GO_API_KEY")
if not API_KEY:
    sys.exit("GO_API_KEY not set — copy .env.example to .env and fill it in")

BASE_URL = "https://api.openmetrolinx.com/OpenDataAPI/api/V1"
SAMPLES = Path("samples")
SAMPLES.mkdir(exist_ok=True)


async def get(client: httpx.AsyncClient, path: str, **params) -> dict:
    url = f"{BASE_URL}{path}"
    r = await client.get(url, params={"key": API_KEY, **params}, timeout=10.0)
    print(f"GET {path}  →  {r.status_code}")
    r.raise_for_status()
    return r.json()


def save(name: str, data: dict):
    path = SAMPLES / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print(f"   saved → {path}")


async def main():
    async with httpx.AsyncClient() as client:

        # 1. All stops — find Markham GO and Union codes
        print("\n=== Stops (searching for Markham / Union) ===")
        stops_data = await get(client, "/Stop/All")
        save("stops", stops_data)
        stop_list = (
            stops_data.get("Stops", {}).get("Stop")
            or stops_data.get("Stop")
            or []
        )
        for stop in stop_list:
            name = stop.get("StopName") or stop.get("Name") or ""
            if any(k in name.upper() for k in ("MARKHAM", "UNION")):
                print(f"   {stop}")

        # 2. All lines — find Stouffville line code
        print("\n=== Lines (searching for Stouffville) ===")
        lines_data = await get(client, "/Line/All")
        save("lines", lines_data)
        line_list = (
            lines_data.get("Lines", {}).get("Line")
            or lines_data.get("Line")
            or []
        )
        for line in line_list:
            name = line.get("LineName") or line.get("Name") or ""
            if "STOUFFVILLE" in name.upper():
                print(f"   {line}")

        # 3. Next services at Markham GO (adjust code MA if the stops list shows something different)
        print("\n=== Next Service at MA (Markham GO) ===")
        next_ma = await get(client, "/Stop/NextService/MA")
        save("next_service_MA", next_ma)
        print(json.dumps(next_ma, indent=2)[:3000])

        # 4. Next services at Union
        print("\n=== Next Service at UN (Union Station) ===")
        next_un = await get(client, "/Stop/NextService/UN")
        save("next_service_UN", next_un)
        print(json.dumps(next_un, indent=2)[:3000])

        # 5. If we found a trip number in step 3, probe its stop list
        trips = (
            next_ma.get("NextService", {})
            .get("Line", [{}])[0]
            .get("Direction", [{}])[0]
            .get("Trips", [])
        )
        if trips:
            trip_number = trips[0].get("TripNumber")
            if trip_number:
                print(f"\n=== Stops for Trip {trip_number} ===")
                trip_stops = await get(client, f"/Trip/{trip_number}/Stops")
                save(f"trip_stops_{trip_number}", trip_stops)
                print(json.dumps(trip_stops, indent=2)[:3000])


asyncio.run(main())
