from datetime import datetime
from src.commute import Trip
from src.config import TIMEZONE


def render(trip: Trip, flavor: str) -> str:
    """Render a Trip as a human-readable string.

    flavor: "discord" (standard markdown) or "slack" (mrkdwn)
    """
    b = ("**", "**") if flavor == "discord" else ("*", "*")
    depart_str = _fmt_time(trip.departure_at)
    countdown = _fmt_countdown(trip.departure_at)

    lines = [
        f"🚆 {b[0]}Next to {trip.destination_name}{b[1]}",
        f"Departs {trip.origin_name} at {depart_str} (in {countdown})",
    ]

    if trip.arrival_at:
        lines.append(f"Arrives {trip.destination_name} at {_fmt_time(trip.arrival_at)}")

    lines.append(f"Trip {trip.trip_id} · {trip.status}")

    return "\n".join(lines)


def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%-I:%M %p")


def _fmt_countdown(dt: datetime) -> str:
    delta = dt - datetime.now(TIMEZONE)
    total = int(delta.total_seconds())
    if total <= 0:
        return "now"
    minutes = total // 60
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60}h {minutes % 60:02d}m"
