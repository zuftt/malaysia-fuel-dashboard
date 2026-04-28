"""Motorist-style markdown parsing for MY_PUMP_PRICES / Firecrawl / Shell HTML."""

import io

import pandas as pd

from app.api.scrape import (
    expand_east_malaysia_to_sabah_sarawak,
    parse_motorist_latest_pump_markdown,
    parse_my_pump_prices,
    parse_shell_fuelprice_html,
    parse_shell_fuelprice_xlsx,
)

SAMPLE = """
## Latest Pump Prices

Grade

Price

RON 95 (Budi)

RM 1.99

RON 97

RM 4.85

Diesel Euro 5 B10

RM 5.12

## Fuel Prices Trend
"""


def test_parse_motorist_pairs():
    rows = parse_motorist_latest_pump_markdown(SAMPLE)
    assert len(rows) == 3
    labels = {r["station"] for r in rows}
    assert "RON 95 Budi" in labels
    assert rows[0]["ron95_budi"] == 1.99
    assert any(r.get("ron97") == 4.85 for r in rows)
    assert any(r.get("diesel") == 5.12 for r in rows)


def test_parse_motorist_skips_ron100():
    md = """
## Latest Pump Prices
Grade
Price
RON 100
RM 7.45
RON 97
RM 5.10
## Fuel Prices Trend
"""
    rows = parse_motorist_latest_pump_markdown(md)
    assert len(rows) == 1
    assert rows[0]["ron97"] == 5.10


def test_motorist_grade_east_becomes_sabah_sarawak():
    md = """
## Latest Pump Prices
Grade
Price
Diesel Euro 5 B7 (East)
RM 2.35
## Fuel Prices Trend
"""
    rows = parse_motorist_latest_pump_markdown(md)
    assert len(rows) == 2
    assert {r["location"] for r in rows} == {"Sabah", "Sarawak"}
    assert all(r["station"] == "Diesel B7" for r in rows)
    assert rows[0]["diesel_b7"] == 2.35


def test_expand_east_to_sabah_sarawak():
    rows = expand_east_malaysia_to_sabah_sarawak(
        [
            {
                "station": "Diesel B7 (East)",
                "location": "East Malaysia",
                "diesel_b7": 2.35,
            }
        ]
    )
    assert len(rows) == 2
    assert {r["location"] for r in rows} == {"Sabah", "Sarawak"}
    assert all(r["station"] == "Diesel B7" for r in rows)


def test_parse_shell_xlsx_peninsular_sabah_sarawak():
    buf = io.BytesIO()
    pd.DataFrame(
        {
            "Fuel Product": ["Shell FuelSave 95", "Shell FuelSave Diesel Euro 5 B7"],
            "Peninsular Malaysia Pump Price": ["RM 3.87", "RM 5.32"],
            "East Malaysia Pump Price": ["RM 3.87", "RM 2.35"],
        }
    ).to_excel(buf, index=False)
    rows = parse_shell_fuelprice_xlsx(buf.getvalue())
    assert len(rows) == 6
    locs = [r["location"] for r in rows]
    assert locs.count("Peninsular Malaysia") == 2
    assert locs.count("Sabah") == 2
    assert locs.count("Sarawak") == 2
    sabah_b7 = next(r for r in rows if r["location"] == "Sabah" and r.get("diesel_b7"))
    assert sabah_b7["diesel_b7"] == 2.35


def test_parse_shell_html_skips_ron100_and_maps_grades():
    html = """
    <table>
    <tr><th>Product</th><th>Price</th></tr>
    <tr><td>RON 95 (Budi)</td><td>1.99</td></tr>
    <tr><td>RON 100</td><td>7.45</td></tr>
    <tr><td>V-Power Racing</td><td>8.43</td></tr>
    </table>
    """
    rows = parse_shell_fuelprice_html(html)
    assert len(rows) == 2
    assert rows[0]["ron95_budi"] == 1.99
    assert rows[1]["vpower"] == 8.43
    assert all("ron 100" not in str(r.get("station") or "").lower() for r in rows)


def test_parse_my_pump_falls_back_to_motorist_when_no_pipe_table():
    assert parse_my_pump_prices(SAMPLE) == parse_motorist_latest_pump_markdown(SAMPLE)
