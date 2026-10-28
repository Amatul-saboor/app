"""Central configuration: market assumptions and data scope."""

from datetime import date, time
from pathlib import Path
from zoneinfo import ZoneInfo

UK_TZ = ZoneInfo("Europe/London")

# Purchase decisions in scope: every day of January 2026 (UK local dates).
# A decision on day D buys power for delivery day D+1, so deliveries span 2 Jan - 1 Feb.
FIRST_DECISION_DATE = date(2026, 1, 1)
LAST_DECISION_DATE = date(2026, 1, 31)

# Default decision cutoff = EPEX SPOT GB day-ahead auction gate closure (09:20 UK time).
# Nord Pool N2EX closes at 09:50; the API accepts any HH:MM so both can be explored.
DEFAULT_CUTOFF = time(9, 20)

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "elexon_jan2026.json"
