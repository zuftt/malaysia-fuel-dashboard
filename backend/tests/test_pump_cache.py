"""Pump station disk cache: Thursday MY refresh cadence."""

from datetime import datetime, timezone

from unittest.mock import MagicMock, patch

from app.petron_pump import fetch_petron_ron100_row
from app.pump_station_cache import needs_live_scrape

_MY = "Asia/Kuala_Lumpur"


def _dt(iso_local: str) -> datetime:
    """Parse naive local MY wall time as UTC-aware (for tests)."""
    from zoneinfo import ZoneInfo

    z = ZoneInfo(_MY)
    return datetime.fromisoformat(iso_local).replace(tzinfo=z).astimezone(timezone.utc)


def test_wednesday_never_schedules_refresh_even_if_stale():
    last = _dt("2026-04-16 10:00")  # Thursday before
    now = _dt("2026-04-22 12:00")  # Wednesday MY
    assert needs_live_scrape(last, now=now) is False


def test_thursday_same_day_no_rescrape():
    last = _dt("2026-04-23 09:00")  # Thursday MY
    now = _dt("2026-04-23 18:00")
    assert needs_live_scrape(last, now=now) is False


def test_thursday_after_prior_thursday_scrapes():
    last = _dt("2026-04-16 10:00")  # prior Thursday
    now = _dt("2026-04-23 10:00")  # next Thursday
    assert needs_live_scrape(last, now=now) is True


def test_thursday_after_wednesday_scrapes():
    last = _dt("2026-04-22 12:00")  # Wednesday MY
    now = _dt("2026-04-23 12:00")  # Thursday MY
    assert needs_live_scrape(last, now=now) is True


def test_friday_uses_no_schedule_refresh():
    last = _dt("2026-04-23 10:00")  # Thursday
    now = _dt("2026-04-24 10:00")  # Friday
    assert needs_live_scrape(last, now=now) is False


def test_petron_parser_finds_blaze100_in_td():
    html = "<html><body><table><tr><td>PETRON BLAZE 100 EURO 4M: RM7.20</td></tr></table></body></html>"
    mock = MagicMock()
    mock.text = html
    mock.raise_for_status = MagicMock()
    with patch("app.petron_pump.requests.get", return_value=mock):
        row = fetch_petron_ron100_row("https://www.petron.com.my/")
    assert row is not None
    assert row["ron100"] == 7.2
    assert "Petron" in row["station"]
