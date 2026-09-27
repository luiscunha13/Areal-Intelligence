import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import datetime
from ..core.config import settings


logger = logging.getLogger(__name__)


class FredClient:
    BASE = "https://api.stlouisfed.org/fred"
    ALFRED_BASE = "https://api.stlouisfed.org/alfred"

    def __init__(self, api_key: str | None = None, retries: int = 3, backoff_factor: float = 0.3):
        self.api_key = api_key or settings.fred_api_key
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=backoff_factor,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get(self, endpoint: str, params: dict) -> dict:
        params = params.copy()
        if self.api_key:
            params["api_key"] = self.api_key
        params.setdefault("file_type", "json")
        url = f"{endpoint}"
        logger.debug("FRED GET %s params=%s", url, params)
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_series(self, series_id: str) -> dict:
        """Get series metadata."""
        endpoint = f"{self.BASE}/series"
        resp = self._get(endpoint, {"series_id": series_id})
        return resp.get("seriess") or {}

    def get_series_observations(self, series_id: str, realtime_start: str | None = None, realtime_end: str | None = None, use_alfred: bool = False) -> dict:
        """Return dict with series metadata and list of observations.

        Each observation is normalized to:
          {date: 'YYYY-MM-DD', value: float|None, realtime_start: 'YYYY-MM-DD', realtime_end: 'YYYY-MM-DD'}
        """
        base = self.ALFRED_BASE if use_alfred else self.BASE
        endpoint = f"{base}/series/observations"
        params = {"series_id": series_id}
        if realtime_start:
            params["realtime_start"] = realtime_start
        if realtime_end:
            params["realtime_end"] = realtime_end

        data = self._get(endpoint, params)
        observations_raw = data.get("observations") or []
        observations = []
        for o in observations_raw:
            date = o.get("date")
            value_raw = o.get("value")
            rt_start = o.get("realtime_start")
            rt_end = o.get("realtime_end")
            # Normalize value: '.' indicates missing in FRED
            if value_raw in (".", None, ""):
                value = None
            else:
                try:
                    value = float(value_raw)
                    # Domain validation rules per Section 31
                    if series_id in ("VIXCLS", "UNRATE") and value < 0:
                        logger.warning("Invalid negative value for %s at %s: %s", series_id, date, value)
                        value = None
                except Exception:
                    value = None

            # Validate dates
            try:
                datetime.date.fromisoformat(date)
            except Exception:
                logger.debug("Skipping observation with invalid date: %s", date)
                continue

            # choose vintage date as realtime_start when available
            vintage_date = None
            try:
                vintage_date = datetime.date.fromisoformat(rt_start) if rt_start else None
            except Exception:
                vintage_date = None

            observations.append(
                {
                    "date": date,
                    "value": value,
                    "realtime_start": rt_start,
                    "realtime_end": rt_end,
                    "vintage_date": vintage_date.isoformat() if vintage_date else None,
                }
            )

        return {"series": data.get("seriess") or {}, "observations": observations}

    def get_series_release_dates(self, series_id: str) -> dict:
        """Fetch release schedule dates for a series from FRED API."""
        try:
            rel_resp = self._get(f"{self.BASE}/series/release", {"series_id": series_id})
            releases = rel_resp.get("releases") or []
            if not releases:
                return {}
            release = releases[0]
            rel_id = release.get("id")
            rel_name = release.get("name")

            dates_resp = self._get(f"{self.BASE}/release/dates", {
                "release_id": rel_id,
                "include_release_dates_with_no_data": "true",
                "sort_order": "desc",
                "limit": 30
            })
            dates_list = dates_resp.get("release_dates") or []
            
            today = datetime.date.today()
            last_release = None
            next_release = None

            for d in dates_list:
                d_str = d.get("date")
                try:
                    d_obj = datetime.date.fromisoformat(d_str)
                    if d_obj <= today and last_release is None:
                        last_release = d_obj
                    elif d_obj > today:
                        next_release = d_obj
                except Exception:
                    continue

            days_until = (next_release - today).days if next_release else None

            return {
                "release_id": rel_id,
                "release_name": rel_name,
                "last_release": last_release.isoformat() if last_release else None,
                "next_release": next_release.isoformat() if next_release else None,
                "days_until": days_until,
            }
        except Exception as e:
            logger.warning("Failed to fetch release dates for %s: %s", series_id, e)
            return {}



