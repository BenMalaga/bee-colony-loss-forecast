"""Idempotent USDA NASS Quick Stats ingest for the Honey Bee Colonies survey.

Standard-library only (urllib) -- no third-party deps -- so data acquisition runs even before
the analysis venv exists (and on a tight disk).

INTEGRITY GUARD: the colony-loss values are OUTCOME data. Per ../PRE_REGISTRATION.md, do not run
the full pull until the pre-registration is committed; the script refuses without
--confirm-prereg-locked. (--discover-only lists field NAMES only and is always allowed.)

Usage:
    export QUICKSTATS_API_KEY=...                      # free: https://quickstats.nass.usda.gov/api
    python -m src.fetch_nass --discover-only           # tiny: writes data/raw/bee_colony_short_descs.txt
    python -m src.fetch_nass --confirm-prereg-locked   # full pull, one JSON per year
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://quickstats.nass.usda.gov/api"
RAW = Path("data/raw")
START_YEAR = 2015
DEFAULT_END_YEAR = 2025  # fixed for determinism; override with --end-year


def _api_key() -> str:
    key = os.environ.get("QUICKSTATS_API_KEY")
    if not key:
        env = Path(".env")
        if env.exists():
            for line in env.read_text().splitlines():
                if line.strip().startswith("QUICKSTATS_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        sys.exit("QUICKSTATS_API_KEY not set. Free key: https://quickstats.nass.usda.gov/api")
    return key


def _get(path: str, params: dict, retries: int = 4) -> dict:
    url = f"{API}/{path}/?" + urlencode(params)
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "bee-colony-loss-forecast"})
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** i)
                continue
            # NASS returns a JSON error body (often HTTP 400) for bad/empty queries.
            try:
                return json.loads(e.read().decode())
            except Exception:
                raise
        except URLError:
            time.sleep(2 ** i)
            continue
    raise RuntimeError(f"Failed GET {path} after {retries} tries")


def discover_short_descs(key: str) -> list[str]:
    vals = _get("get_param_values", {"key": key, "param": "short_desc", "commodity_desc": "HONEY"})
    if "short_desc" not in vals:
        sys.exit(f"Unexpected API response (check key?): {str(vals)[:300]}")
    bee = sorted(s for s in vals["short_desc"] if "BEE COLONIES" in s.upper())
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "bee_colony_short_descs.txt").write_text("\n".join(bee) + "\n")
    print(f"Discovered {len(bee)} BEE COLONIES short_descs -> {RAW/'bee_colony_short_descs.txt'}")
    for s in bee:
        print("   ", s)
    return bee


def fetch_year(key: str, year: int) -> None:
    out = RAW / f"nass_honey_{year}.json"
    if out.exists():
        print(f"[skip] {out} already exists")
        return
    base = {
        "key": key,
        "commodity_desc": "HONEY",
        "agg_level_desc": "STATE",
        "source_desc": "SURVEY",
        "year": str(year),
    }
    raw_count = _get("get_counts", base).get("count", 0)
    try:
        count = int(raw_count)
    except (TypeError, ValueError):
        count = 0
    if count == 0:
        print(f"[none] {year}: 0 records")
        return
    if count > 50000:
        sys.exit(f"{year}: {count} records exceeds the 50k API cap; add a finer split.")
    data = _get("api_GET", {**base, "format": "JSON"})
    out.write_text(json.dumps(data))
    print(f"[ok]  {year}: {len(data.get('data', []))} records -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--confirm-prereg-locked",
        action="store_true",
        help="Required for the full pull. Confirms PRE_REGISTRATION.md is committed first.",
    )
    ap.add_argument(
        "--discover-only",
        action="store_true",
        help="Only list field names (no outcome values). Always allowed.",
    )
    ap.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    args = ap.parse_args()

    key = _api_key()
    if args.discover_only:
        discover_short_descs(key)
        return
    if not args.confirm_prereg_locked:
        sys.exit(
            "Refusing the full fetch. Commit PRE_REGISTRATION.md, then re-run with "
            "--confirm-prereg-locked (or use --discover-only). Integrity gate; see PRE_REGISTRATION.md."
        )
    discover_short_descs(key)
    for year in range(START_YEAR, args.end_year + 1):
        fetch_year(key, year)
    print("Done. Next: python -m src.build_panel")


if __name__ == "__main__":
    main()
