import time
import logging
import requests
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "ArealSectorIntelligence/2.0 research@arealintel.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

USER_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

class SECEdgarProvider:
    def __init__(self, user_agent: Optional[str] = None):
        self.headers = HEADERS.copy()
        if user_agent:
            self.headers["User-Agent"] = user_agent
        self._ticker_cik_map: Dict[str, str] = {}
        self.last_req_time = 0.0

    def _rate_limit(self, delay: float = 0.15):
        """Enforces SEC EDGAR limit of max 10 requests per second."""
        elapsed = time.time() - self.last_req_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_req_time = time.time()

    def get_ticker_cik_map(self) -> Dict[str, str]:
        """Fetch mapping of ticker symbols to CIK strings."""
        if self._ticker_cik_map:
            return self._ticker_cik_map

        self._rate_limit()
        try:
            req_headers = self.headers.copy()
            req_headers["Host"] = "www.sec.gov"
            resp = requests.get(USER_TICKERS_URL, headers=req_headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # data format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
                mapping = {}
                for item in data.values():
                    t = item["ticker"].upper()
                    cik = str(item["cik_str"]).zfill(10)
                    mapping[t] = cik
                self._ticker_cik_map = mapping
                logger.info(f"Loaded {len(mapping)} CIK mappings from SEC EDGAR.")
                return mapping
            else:
                logger.error(f"Failed to fetch SEC CIK map: HTTP {resp.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Exception fetching CIK map: {e}")
            return {}

    def fetch_company_facts(self, cik: str) -> Optional[Dict[str, Any]]:
        """Fetch raw XBRL company facts from SEC EDGAR data API."""
        cik_str = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json"

        self._rate_limit()
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                logger.warning(f"No XBRL facts found for CIK {cik_str}")
                return None
            else:
                logger.error(f"SEC EDGAR returned status {resp.status_code} for CIK {cik_str}")
                return None
        except Exception as e:
            logger.error(f"Error fetching facts for CIK {cik_str}: {e}")
            return None

    def extract_financial_line_items(self, facts_json: Dict[str, Any]) -> pd.DataFrame:
        """
        Parses US-GAAP XBRL facts into structured annual & quarterly financial line items.
        
        Tags Parsed:
          - Revenue: Revenues, RevenueFromContractWithCustomerExcludingAssessedTax, SalesRevenueNet
          - Operating Income: OperatingIncomeLoss
          - Net Income: NetIncomeLoss
          - Diluted EPS: EarningsPerShareDiluted
          - Capex: PaymentsToAcquirePropertyPlantAndEquipment
          - Cash: CashAndCashEquivalentsAtCarryingValue
          - Debt: LongTermDebtNoncurrent
        """
        if not facts_json or "facts" not in facts_json or "us-gaap" not in facts_json["facts"]:
            return pd.DataFrame()

        gaap = facts_json["facts"]["us-gaap"]
        records = []

        tag_mappings = {
            "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
            "operating_income": ["OperatingIncomeLoss"],
            "net_income": ["NetIncomeLoss"],
            "eps_diluted": ["EarningsPerShareDiluted"],
            "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
            "cash": ["CashAndCashEquivalentsAtCarryingValue"],
            "long_term_debt": ["LongTermDebtNoncurrent"]
        }

        extracted_by_date = {}

        for metric_name, possible_tags in tag_mappings.items():
            for tag in possible_tags:
                if tag in gaap and "units" in gaap[tag]:
                    units_dict = gaap[tag]["units"]
                    # Get USD or USD/shares unit list
                    unit_key = next((u for u in units_dict.keys() if "USD" in u or "shares" in u), list(units_dict.keys())[0])
                    units_data = units_dict[unit_key]

                    for fact in units_data:
                        form = fact.get("form", "")
                        # Filter 10-K (Annual) and 10-Q (Quarterly)
                        if form not in ["10-K", "10-Q", "10-K/A", "10-Q/A"]:
                            continue

                        val = fact.get("val")
                        end_date = fact.get("end")
                        fy = fact.get("fy")
                        fp = fact.get("fp")

                        if val is None or not end_date:
                            continue

                        key = (end_date, form, fy, fp)
                        if key not in extracted_by_date:
                            extracted_by_date[key] = {
                                "end_date": end_date,
                                "form": form,
                                "fy": fy,
                                "fp": fp
                            }
                        
                        if metric_name not in extracted_by_date[key]:
                            extracted_by_date[key][metric_name] = float(val)

        df = pd.DataFrame(list(extracted_by_date.values()))
        if not df.empty:
            df["end_date"] = pd.to_datetime(df["end_date"])
            df = df.sort_values("end_date").reset_index(drop=True)
        return df
