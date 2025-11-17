"""Static constants for the data pipeline."""

from datetime import datetime
from typing import Final, List

SCHEME_URLS: Final[List[dict]] = [
    {
        "scheme": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "category": "ELSS",
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    },
    {
        "scheme": "HDFC Flexi Cap Fund Direct Plan Growth",
        "category": "Flexi Cap",
        # Groww uses the legacy equity-fund slug for this flexi-cap scheme
        "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    },
    {
        "scheme": "HDFC Large and Mid Cap Fund Direct Growth",
        "category": "Large & Mid Cap",
        # Groww slug omits the "plan" segment for this scheme
        "url": "https://groww.in/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth",
    },
    {
        "scheme": "HDFC Small Cap Fund Direct Growth",
        "category": "Small Cap",
        # Groww slug omits the "plan" segment for this scheme
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    },
    {
        "scheme": "HDFC Multi Cap Fund Direct Growth",
        "category": "Multi Cap",
        # Groww slug omits the "plan" segment for this scheme
        "url": "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth",
    },
    {
        "scheme": "Groww Capital Gains Statement Guide",
        "category": "Help Center",
        "url": "https://groww.in/blog/how-to-get-capital-gains-statement-for-mutual-fund-investments",
    },
]

LAST_VERIFIED: Final[str] = datetime.utcnow().strftime("%Y-%m-%d")
