"""
Weekly Firecrawl snapshots for ASEAN retail fuel pages.

- Scheduling: run once per week from cron, GitHub Actions, or EventBridge (this file does not schedule itself).
- Sources: set only `ASEAN_FIRECRAWL_URL_<CC>` env vars for countries you trust; unset = skipped.
- Legacy: `INDO` is still read as Indonesia if `ASEAN_FIRECRAWL_URL_ID` is unset.
- Next step: parse markdown → structured prices → upsert `asean_fuel_prices` (not implemented here).

Run from repo:  cd backend && python -m app.api.scrape
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from app.petron_pump import append_petron_ron100_if_configured

# Load backend/.env when cwd is backend/ (typical for uvicorn and scripts).
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

try:
    from firecrawl import Firecrawl
except ImportError as e:  # pragma: no cover
    print("Install Firecrawl: pip install firecrawl-py", file=sys.stderr)
    raise e

# ISO country code → env var holding full https URL to scrape (one page per country is enough to start).
FIRECRAWL_URL_ENV: dict[str, str] = {
    "MY": "ASEAN_FIRECRAWL_URL_MY",
    "SG": "ASEAN_FIRECRAWL_URL_SG",
    "TH": "ASEAN_FIRECRAWL_URL_TH",
    "ID": "ASEAN_FIRECRAWL_URL_ID",
    "BN": "ASEAN_FIRECRAWL_URL_BN",
    "PH": "ASEAN_FIRECRAWL_URL_PH",
}

# ms; ~7 days — ASEAN weekly snapshots can reuse Firecrawl cache briefly.
MAX_AGE_MS_WEEKLY = 7 * 24 * 60 * 60 * 1000
# ms; 48h — pump listing pages (e.g. motorist.my) change more often; matches common Firecrawl scrape example.
PUMP_MAX_AGE_MS_DEFAULT = 172800000


def _urls_from_env() -> dict[str, str]:
    from app.safe_url import assert_safe_url

    out: dict[str, str] = {}
    for cc, env_name in FIRECRAWL_URL_ENV.items():
        raw = os.getenv(env_name, "").strip()
        if not raw:
            continue
        if not raw.startswith("http"):
            raw = "https://" + raw.lstrip("/")
        try:
            assert_safe_url(raw)
        except ValueError as e:
            print(f"[scrape] Skipping {env_name}: {e}", file=sys.stderr)
            continue
        out[cc] = raw
    # Back-compat with existing .env
    legacy = os.getenv("INDO", "").strip()
    if legacy and "ID" not in out:
        if not legacy.startswith("http"):
            legacy = "https://" + legacy.lstrip("/")
        try:
            assert_safe_url(legacy)
            out["ID"] = legacy
        except ValueError as e:
            print(f"[scrape] Skipping INDO: {e}", file=sys.stderr)
    return out


def scrape_one(client: Firecrawl, url: str, *, max_age_ms: int | None = None) -> object:
    """Same parameters as Firecrawl `scrape()` for HTML→markdown tables; `max_age_ms` defaults to weekly cache."""
    age = MAX_AGE_MS_WEEKLY if max_age_ms is None else max_age_ms
    return client.scrape(
        url,
        only_main_content=False,
        max_age=age,
        parsers=["pdf"],
        formats=["markdown"],
    )


def _parse_price_number(raw: str) -> float | None:
    """
    Parse mixed currency text into a number.
    Handles examples: "RM 2.05", "Rp 10.000", "14,500", "4.62".
    """
    s = (raw or "").strip()
    if not s:
        return None
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s:
        return None

    # Indonesian-style thousands: 10.000 / 14.500
    if "," not in s and "." in s:
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3:
            s = "".join(parts)

    # Fallback thousands with comma: 14,500
    if "," in s and "." not in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            s = "".join(parts)
        else:
            s = s.replace(",", ".")

    # If both are present, assume commas are thousands separators.
    if "," in s and "." in s:
        s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return None


def _table_blocks(markdown: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in markdown.splitlines():
        if line.strip().startswith("|"):
            cur.append(line)
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks


def _split_row(line: str) -> list[str]:
    cells = [c.strip() for c in line.strip().split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def _pump_row_shell(
    *,
    station: str,
    location: str | None = None,
    ron95_budi: float | None = None,
    ron95: float | None = None,
    ron97: float | None = None,
    vpower: float | None = None,
    ron100: float | None = None,
    diesel: float | None = None,
    diesel_b7: float | None = None,
) -> dict[str, Any]:
    return {
        "station": station,
        "location": location,
        "ron95_budi": ron95_budi,
        "ron95": ron95,
        "ron97": ron97,
        "vpower": vpower,
        "ron100": ron100,
        "diesel": diesel,
        "diesel_b7": diesel_b7,
    }


def _pump_row_for_slot(*, station: str, location: str | None, slot: str, price: float) -> dict[str, Any]:
    d: dict[str, Any] = {
        "station": station,
        "location": location,
        "ron95_budi": None,
        "ron95": None,
        "ron97": None,
        "vpower": None,
        "ron100": None,
        "diesel": None,
        "diesel_b7": None,
    }
    if slot not in (
        "ron95_budi",
        "ron95",
        "ron97",
        "vpower",
        "ron100",
        "diesel",
        "diesel_b7",
    ):
        d["ron95"] = price
    else:
        d[slot] = price
    return d


def _motorist_rows_from_grade(grade: str, price: float) -> list[dict[str, Any]]:
    """Map grade + RM/L into UI rows. Skips RON 100. *East* in the label → Sabah + Sarawak (never *East Malaysia*)."""
    g = grade.lower().strip()
    if "ron 100" in g or "ron100" in g:
        return []
    east = "east" in g

    def emit(station: str, slot: str) -> list[dict[str, Any]]:
        if east:
            return [
                _pump_row_for_slot(station=station, location="Sabah", slot=slot, price=price),
                _pump_row_for_slot(station=station, location="Sarawak", slot=slot, price=price),
            ]
        return [_pump_row_for_slot(station=station, location=None, slot=slot, price=price)]

    if "diesel" in g:
        if "b7" in g:
            return emit("Diesel B7", "diesel_b7")
        return emit("Diesel B10/B20", "diesel")
    if "v-power" in g or "vpower" in g or "v power" in g or "racing" in g:
        return emit("V-Power", "vpower")
    if "ron 97" in g or "ron97" in g:
        return emit("RON 97", "ron97")
    if "budi" in g or "(budi)" in g:
        return emit("RON 95 Budi", "ron95_budi")
    if "ron 95" in g or "ron95" in g:
        return emit("RON 95", "ron95")
    return emit(grade.strip(), "ron95")


def _shell_product_to_rows(product: str, price: float) -> list[dict[str, Any]]:
    """Map Shell HTML table product cell + price (same rules as motorist markdown)."""
    return _motorist_rows_from_grade(product, price)


def _shell_xlsx_station_and_slot(product: str) -> tuple[str, str] | None:
    """Map Shell XLSX *Fuel Product* labels to display name + price field (RON 100 omitted)."""
    p = product.lower().strip()
    if "ron 100" in p or "ron100" in p:
        return None
    if "budi" in p or "subsidi" in p or "subsid" in p:
        return ("RON 95 Budi", "ron95_budi")
    if "diesel" in p and "b7" in p:
        return ("Diesel B7", "diesel_b7")
    if "diesel" in p:
        return ("Diesel B10/B20", "diesel")
    if "v-power" in p or "vpower" in p or "v power" in p:
        if "racing" in p:
            return ("V-Power", "vpower")
        return ("RON 97", "ron97")
    if "95" in p:
        return ("RON 95", "ron95")
    return None


def _find_shell_xlsx_url_in_json(obj: Any) -> str | None:
    if isinstance(obj, dict):
        v = obj.get("value")
        if isinstance(v, str) and v.lower().endswith(".xlsx"):
            return v
        for x in obj.values():
            u = _find_shell_xlsx_url_in_json(x)
            if u:
                return u
    elif isinstance(obj, list):
        for item in obj:
            u = _find_shell_xlsx_url_in_json(item)
            if u:
                return u
    return None


def _shell_model_json_url(fuelprice_page_url: str) -> str:
    base = fuelprice_page_url.split("#")[0].strip()
    lower = base.lower()
    if lower.endswith(".html"):
        return base[:-5] + ".model.json"
    if lower.endswith(".model.json"):
        return base
    return base.rstrip("/") + ".model.json"


def parse_shell_fuelprice_xlsx(content: bytes) -> list[dict[str, Any]]:
    """
    Parse Shell's ``fuel-price-update-malaysia.xlsx``: Peninsular + regional column.
    Shell names the second column *East Malaysia*; we only expose **Sabah** and **Sarawak**
    rows (same value each), never *East* in the API payload labels.
    """
    try:
        df = pd.read_excel(io.BytesIO(content), header=0)
    except Exception:
        return []
    if df.shape[0] == 0:
        return []
    df.columns = [str(c).strip() for c in df.columns]
    col_product = col_pen = col_east = None
    for c in df.columns:
        cl = c.lower()
        if "fuel" in cl and "product" in cl:
            col_product = c
        elif "peninsular" in cl:
            col_pen = c
        elif "east" in cl and "malaysia" in cl:
            col_east = c  # source column name only; not shown to users
    if not col_product or col_pen is None:
        return []

    out: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        product = str(row[col_product]).strip()
        if not product or product.lower() in ("nan", "fuel product"):
            continue
        raw_p = row[col_pen]
        pen = None if pd.isna(raw_p) else _parse_price_number(str(raw_p))
        east: float | None = None
        if col_east:
            raw_e = row[col_east]
            if not pd.isna(raw_e):
                east = _parse_price_number(str(raw_e))
        spec = _shell_xlsx_station_and_slot(product)
        if not spec:
            continue
        station, slot = spec
        if pen is not None:
            out.append(
                _pump_row_for_slot(
                    station=station,
                    location="Peninsular Malaysia",
                    slot=slot,
                    price=pen,
                )
            )
        if east is not None:
            out.append(_pump_row_for_slot(station=station, location="Sabah", slot=slot, price=east))
            out.append(_pump_row_for_slot(station=station, location="Sarawak", slot=slot, price=east))
    return out


def expand_east_malaysia_to_sabah_sarawak(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Legacy cache rows only: split old *East Malaysia* / *(East)* into Sabah + Sarawak."""
    out: list[dict[str, Any]] = []
    for r in rows:
        loc = (r.get("location") or "").strip()
        st = str(r.get("station") or "")
        is_east = loc == "East Malaysia" or re.search(r"\(East\)", st, re.I) is not None
        if not is_east:
            out.append(r)
            continue
        base = re.sub(r"\s*\(East\)", "", st, flags=re.I).strip()
        for place in ("Sabah", "Sarawak"):
            out.append({**r, "station": base, "location": place})
    return out


def parse_shell_fuelprice_html(html: str) -> list[dict[str, Any]]:
    """First HTML table on shell.com.my/fuelprice-style pages → grade rows (BS4 + stdlib parser)."""
    out: list[dict[str, Any]] = []
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        if len(trs) < 2:
            continue
        start = 0
        hdr_cells = [c.get_text(strip=True).lower() for c in trs[0].find_all(["th", "td"])]
        if hdr_cells and any("product" in h or "fuel" in h or "grade" in h for h in hdr_cells):
            if any("price" in h or "rm" in h or "harga" in h for h in hdr_cells):
                start = 1
        for tr in trs[start:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            product = cells[0].get_text(strip=True)
            price_text = cells[-1].get_text(strip=True)
            if not product or product.lower() in ("product", "fuel", "grade", "items", "nan"):
                continue
            p = _parse_price_number(price_text)
            if p is None:
                continue
            out.extend(_shell_product_to_rows(product, p))
        if out:
            break
    return out


def fetch_shell_my_pump_prices(url: str) -> dict[str, Any]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
    }
    rows: list[dict[str, Any]] = []
    try:
        model_url = _shell_model_json_url(url)
        mr = requests.get(model_url, headers=headers, timeout=45)
        mr.raise_for_status()
        xlsx_url = _find_shell_xlsx_url_in_json(mr.json())
        if xlsx_url:
            xr = requests.get(xlsx_url, headers=headers, timeout=45)
            xr.raise_for_status()
            rows = parse_shell_fuelprice_xlsx(xr.content)
    except Exception:
        rows = []
    if not rows:
        resp = requests.get(url, headers=headers, timeout=45)
        resp.raise_for_status()
        rows = parse_shell_fuelprice_html(resp.text)
    rows = expand_east_malaysia_to_sabah_sarawak(rows)
    rows = append_petron_ron100_if_configured(rows)
    return {
        "rows": rows,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
    }


def _is_shell_fuelprice_url(url: str) -> bool:
    u = url.lower()
    return "shell.com.my" in u and "fuelprice" in u


# motorist.my petrol-prices: block between Grade/Price and the next section heading.
_MOTORIST_GRADE_BLOCK_PATTERNS: tuple[str, ...] = (
    r"Grade\n\nPrice\n\n(.*?)\n\n## Fuel Prices Trend",
    r"Grade\s*\n+\s*Price\s*\n+\s*(.*?)(?=\n\s*##\s+Fuel\s+Prices\s+Trend)",
)


def _parse_motorist_grade_block_regex(markdown: str) -> list[dict[str, Any]]:
    """Extract Grade / RM pairs from the fenced block (same idea as get_fuel_table on Firecrawl markdown)."""
    for pat in _MOTORIST_GRADE_BLOCK_PATTERNS:
        match = re.search(pat, markdown, re.DOTALL)
        if not match:
            continue
        raw = match.group(1)
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        out: list[dict[str, Any]] = []
        for i in range(0, len(lines), 2):
            if i + 1 >= len(lines):
                break
            grade, price_line = lines[i], lines[i + 1]
            if not grade or grade.lower() in ("grade", "price"):
                continue
            p = _parse_price_number(price_line)
            if p is None or len(grade) > 120:
                continue
            out.extend(_motorist_rows_from_grade(grade, p))
        if out:
            return out
    return []


def _parse_motorist_walk_lines_fallback(markdown: str) -> list[dict[str, Any]]:
    """If regex block shape changes, walk lines after '## Latest Pump Prices' and pair grade + RM line."""
    lines = [ln.strip() for ln in markdown.splitlines()]
    start = 0
    for i, ln in enumerate(lines):
        if "latest pump" in ln.lower() and ("#" in ln or ln.strip().lower().startswith("latest")):
            start = i + 1
            break
    out: list[dict[str, Any]] = []
    i = start
    while i < len(lines):
        grade = lines[i]
        if grade.startswith("##"):
            break
        if not grade or grade.lower() in ("grade", "price", "by", "---"):
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not lines[j]:
            j += 1
        if j >= len(lines):
            break
        nxt = lines[j]
        if nxt.upper().startswith("RM"):
            p = _parse_price_number(nxt)
            if p is not None and len(grade) < 120:
                out.extend(_motorist_rows_from_grade(grade, p))
            i = j + 1
            continue
        i += 1
    return out


def parse_motorist_latest_pump_markdown(markdown: str) -> list[dict[str, Any]]:
    """
    motorist.my-style markdown: Grade/Price block then alternating lines
    (see https://www.motorist.my/petrol-prices).
    """
    rows = _parse_motorist_grade_block_regex(markdown)
    if rows:
        return rows
    return _parse_motorist_walk_lines_fallback(markdown)


def parse_my_pump_prices(markdown: str) -> list[dict[str, Any]]:
    """
    Try to extract station/city rows with RON95/RON97/Diesel-ish columns from markdown tables.
    Returns normalised rows for frontend display.
    """
    out: list[dict[str, Any]] = []
    for block in _table_blocks(markdown):
        rows = [_split_row(l) for l in block]
        if len(rows) < 3:
            continue
        header = [c.lower() for c in rows[0]]
        if not any("city" in h or "station" in h or "brand" in h or "operator" in h for h in header):
            continue

        def idx(pred: str) -> int | None:
            for i, h in enumerate(header):
                if re.search(pred, h):
                    return i
            return None

        i_station = idx(r"city|station|brand|operator|lokasi|location") or 0
        i_ron95 = idx(r"ron\s*95|pertalite|regular|95")
        i_ron97 = idx(r"ron\s*97|pertamax|premium|97|98|turbo")
        i_diesel = idx(r"diesel|dexlite|solar|bio")

        for r in rows[2:]:
            if len(r) <= i_station:
                continue
            station = (r[i_station] or "").strip()
            if not station or station == "---":
                continue
            rec: dict[str, Any] = {"station": station}
            if i_ron95 is not None and i_ron95 < len(r):
                rec["ron95"] = _parse_price_number(r[i_ron95])
            if i_ron97 is not None and i_ron97 < len(r):
                rec["ron97"] = _parse_price_number(r[i_ron97])
            if i_diesel is not None and i_diesel < len(r):
                rec["diesel"] = _parse_price_number(r[i_diesel])
            if any(v is not None for k, v in rec.items() if k != "station"):
                out.append(rec)
    if out:
        return out
    return parse_motorist_latest_pump_markdown(markdown)


def fetch_my_pump_prices_from_env() -> dict[str, Any]:
    """
    Scrape pump grades using backend env ``MY_PUMP_PRICES`` (URL).

    - Shell Malaysia ``fuelprice.html``: xlsx from ``fuelprice.model.json``, then optional HTML.
    - Other URLs: Firecrawl markdown (needs ``FIRECRAWL_API_KEY``).
    - Optional ``MY_PUMP_PRICES2``: Petron RON 100 (see ``append_petron_ron100_if_configured``).
    All external fetches are invoked only when the API does a *live* pump refresh (cached weekly;
    see ``pump_station_cache.needs_live_scrape``), not on every client reload.
    """
    from app.safe_url import assert_safe_url

    url = os.getenv("MY_PUMP_PRICES", "").strip()
    if not url:
        raise ValueError("Missing MY_PUMP_PRICES URL")
    if not url.startswith("http"):
        url = "https://" + url.lstrip("/")
    assert_safe_url(url)

    if _is_shell_fuelprice_url(url):
        return fetch_shell_my_pump_prices(url)

    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing FIRECRAWL_API_KEY")

    raw_max = os.getenv("MY_PUMP_MAX_AGE_MS", "").strip()
    try:
        pump_max_age = int(raw_max) if raw_max else PUMP_MAX_AGE_MS_DEFAULT
    except ValueError:
        pump_max_age = PUMP_MAX_AGE_MS_DEFAULT

    client = Firecrawl(api_key=api_key)
    raw = scrape_one(client, url, max_age_ms=pump_max_age)
    serial = _serialize_firecrawl_result(raw)
    markdown = serial.get("markdown", "")
    if not isinstance(markdown, str):
        markdown = ""

    rows = parse_my_pump_prices(markdown)
    rows = expand_east_malaysia_to_sabah_sarawak(rows)
    rows = append_petron_ron100_if_configured(rows)
    return {
        "rows": rows,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
    }


def _serialize_firecrawl_result(raw: object) -> dict[str, object]:
    """Stable JSON shape: markdown + a thin metadata slice (avoid dumping huge objects)."""
    out: dict[str, object] = {}
    md = getattr(raw, "markdown", None)
    if isinstance(md, str) and md.strip():
        out["markdown"] = md[:500_000]
    meta = getattr(raw, "metadata", None)
    if meta is not None:
        if hasattr(meta, "model_dump"):
            meta_d = meta.model_dump()
        elif isinstance(meta, dict):
            meta_d = meta
        else:
            meta_d = {}
        out["metadata"] = {
            k: meta_d.get(k)
            for k in ("title", "description", "url", "language", "status_code", "source_url", "published_time")
            if meta_d.get(k) is not None
        }
    if not out:
        out["note"] = "No markdown/metadata on response; inspect Firecrawl SDK return type."
        out["repr"] = str(raw)[:80_000]
    return out


def main() -> int:
    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        print("Set FIRECRAWL_API_KEY in backend/.env", file=sys.stderr)
        return 1

    targets = _urls_from_env()
    if not targets:
        print(
            "No scrape URLs configured. Set one or more:\n"
            + "\n".join(f"  {name}=https://..." for name in FIRECRAWL_URL_ENV.values())
            + "\n  (or legacy INDO=https://... for Indonesia)",
            file=sys.stderr,
        )
        return 1

    client = Firecrawl(api_key=api_key)
    results: dict[str, object] = {}
    for cc, url in sorted(targets.items()):
        try:
            raw = scrape_one(client, url)
            results[cc] = {"url": url, "data": _serialize_firecrawl_result(raw)}
        except Exception as err:  # pragma: no cover - network
            results[cc] = {"url": url, "error": str(err)}

    print(json.dumps(results, indent=2, ensure_ascii=False)[:500_000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
