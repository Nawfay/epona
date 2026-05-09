import httpx
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from src.config import GO_API_KEY, TIMEZONE

BASE_URL = "https://api.openmetrolinx.com/OpenDataAPI/api/V1"


@dataclass
class ServiceEntry:
    stop_code: str
    line_code: str
    direction_name: str
    scheduled_time: datetime
    computed_time: datetime
    trip_number: str
    trip_order: int


@dataclass
class GlanceTrip:
    trip_number: str
    line_code: str
    start_time: str   # "HH:MM" scheduled start
    end_time: str     # "HH:MM" scheduled end (arrival at last stop)
    direction_name: str
    first_stop: str
    last_stop: str
    delay_seconds: int
    is_in_motion: bool


async def _get(client: httpx.AsyncClient, path: str, **params) -> dict:
    response = await client.get(
        f"{BASE_URL}{path}",
        params={"key": GO_API_KEY, **params},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


async def get_next_services(stop_code: str) -> list[ServiceEntry]:
    """Upcoming departures at a stop (all lines). Response is a flat Lines list."""
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"/Stop/NextService/{stop_code}")

    entries: list[ServiceEntry] = []
    for item in data.get("NextService", {}).get("Lines", []):
        scheduled = _parse_dt(item.get("ScheduledDepartureTime"))
        computed = _parse_dt(item.get("ComputedDepartureTime"))
        if scheduled is None:
            continue
        entries.append(ServiceEntry(
            stop_code=stop_code,
            line_code=item.get("LineCode", ""),
            direction_name=item.get("DirectionName", ""),
            scheduled_time=scheduled,
            computed_time=computed or scheduled,
            trip_number=str(item.get("TripNumber", "")),
            trip_order=int(item.get("TripOrder", 0)),
        ))

    return sorted(entries, key=lambda e: e.computed_time)


async def get_glance_trips(line_code: Optional[str] = None) -> list[GlanceTrip]:
    """Real-time train positions and trip-level delay info."""
    async with httpx.AsyncClient() as client:
        data = await _get(client, "/ServiceataGlance/Trains/All")

    trips: list[GlanceTrip] = []
    for t in data.get("Trips", {}).get("Trip", []):
        if line_code and t.get("LineCode") != line_code:
            continue
        trips.append(GlanceTrip(
            trip_number=str(t.get("TripNumber", "")),
            line_code=t.get("LineCode", ""),
            start_time=t.get("StartTime", ""),
            end_time=t.get("EndTime", ""),
            direction_name=t.get("Display", ""),
            first_stop=t.get("FirstStopCode", ""),
            last_stop=t.get("LastStopCode", ""),
            delay_seconds=int(t.get("DelaySeconds", 0)),
            is_in_motion=bool(t.get("IsInMotion", False)),
        ))

    return trips


def parse_end_time(glance: GlanceTrip) -> Optional[datetime]:
    """Convert a GlanceTrip's HH:MM end_time to today's datetime, adjusted for delay if in motion."""
    dt = _parse_hhmm(glance.end_time)
    if dt is None:
        return None
    if glance.is_in_motion:
        dt = dt + timedelta(seconds=glance.delay_seconds)
    return dt


def glance_status(glance: GlanceTrip) -> str:
    if not glance.is_in_motion:
        return "scheduled"
    delay_min = glance.delay_seconds // 60
    if abs(delay_min) < 1:
        return "on time"
    if delay_min > 0:
        return f"delayed {delay_min} min"
    return f"early {abs(delay_min)} min"


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.year == 1900:
                today = datetime.now(TIMEZONE).date()
                dt = dt.replace(year=today.year, month=today.month, day=today.day)
            return dt.replace(tzinfo=TIMEZONE)
        except ValueError:
            continue
    return None


def _parse_hhmm(value: str) -> Optional[datetime]:
    """Parse "HH:MM" as today's datetime in TIMEZONE."""
    if not value:
        return None
    try:
        h, m = value.split(":")
        today = datetime.now(TIMEZONE).date()
        return datetime(today.year, today.month, today.day, int(h), int(m), tzinfo=TIMEZONE)
    except (ValueError, AttributeError):
        return None
