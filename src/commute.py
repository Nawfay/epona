from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.go_api import (
    get_next_services, get_glance_trips,
    parse_end_time, glance_status, ServiceEntry,
)
from src.config import HOME_STATION, WORK_STATION, LINE, TIMEZONE, MIN_DEPARTURE_BUFFER_MINUTES

STATION_NAMES = {
    "MR": "Markham GO",
    "UN": "Union Station",
}


@dataclass
class Trip:
    departure_at: datetime
    arrival_at: Optional[datetime]
    trip_id: str
    status: str
    origin_name: str
    destination_name: str


class NoTrainsError(Exception):
    pass


async def next_to_work() -> Trip:
    """Next train from Markham GO to Union Station."""
    now = datetime.now(TIMEZONE)
    cutoff = now + timedelta(minutes=MIN_DEPARTURE_BUFFER_MINUTES)

    services = await get_next_services(HOME_STATION)
    candidates = [
        s for s in services
        if s.line_code == LINE
        and "Union" in s.direction_name
        and s.computed_time >= cutoff
    ]

    if not candidates:
        raise NoTrainsError(f"No upcoming trains from {_name(HOME_STATION)} to {_name(WORK_STATION)}")

    dep = candidates[0]

    # Get arrival at Union and delay status from ServiceataGlance
    glance_trips = await get_glance_trips(LINE)
    glance_by_trip = {t.trip_number: t for t in glance_trips}
    glance = glance_by_trip.get(dep.trip_number)

    arrival_at = parse_end_time(glance) if glance else None
    status = glance_status(glance) if glance else "scheduled"

    return Trip(
        departure_at=dep.computed_time,
        arrival_at=arrival_at,
        trip_id=dep.trip_number,
        status=status,
        origin_name=_name(HOME_STATION),
        destination_name=_name(WORK_STATION),
    )


async def next_to_home() -> Trip:
    """Next train from Union Station to Markham GO."""
    now = datetime.now(TIMEZONE)
    cutoff = now + timedelta(minutes=MIN_DEPARTURE_BUFFER_MINUTES)

    # All ST trains at Union go northbound through Markham
    un_services = await get_next_services(WORK_STATION)
    candidates = [
        s for s in un_services
        if s.line_code == LINE
        and s.computed_time >= cutoff
    ]

    if not candidates:
        raise NoTrainsError(f"No upcoming trains from {_name(WORK_STATION)} to {_name(HOME_STATION)}")

    dep = candidates[0]

    # Cross-reference the same TripNumber in Markham's NextService to get arrival time at Markham
    mr_services = await get_next_services(HOME_STATION)
    mr_by_trip = {s.trip_number: s for s in mr_services}
    mr_entry = mr_by_trip.get(dep.trip_number)
    arrival_at = mr_entry.computed_time if mr_entry else None

    # Delay status from ServiceataGlance
    glance_trips = await get_glance_trips(LINE)
    glance_by_trip = {t.trip_number: t for t in glance_trips}
    glance = glance_by_trip.get(dep.trip_number)

    status = glance_status(glance) if glance else "scheduled"
    if arrival_at and glance and glance.is_in_motion:
        arrival_at = arrival_at + timedelta(seconds=glance.delay_seconds)

    return Trip(
        departure_at=dep.computed_time,
        arrival_at=arrival_at,
        trip_id=dep.trip_number,
        status=status,
        origin_name=_name(WORK_STATION),
        destination_name=_name(HOME_STATION),
    )


def _name(code: str) -> str:
    return STATION_NAMES.get(code.upper(), code)
