import streamlit as st
from datetime import datetime, timezone
from sbc_engine import analyse_symbol, print_report, SBCResult, NAKSHATRAS
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="SBC Analyser", page_icon="🔵", layout="wide")

st.title("🔵 Sarvatobhadra Chakra Analyser")
st.caption("Classical SBC analysis for stocks and indices")


def build_sbc_grid_html(stock_nak, front_nak, left_nak, right_nak, moon_nak):
    from sbc_engine import NAKSHATRAS, VEDHA_TABLE, NAKSHATRA_COMMODITIES

    # Map name → index
    def nak_idx(name):
        for i, n in enumerate(NAKSHATRAS):
            if n == name:
                return i
        return -1

    s = nak_idx(stock_nak)
    f = nak_idx(front_nak)
    l = nak_idx(left_nak)
    r = nak_idx(right_nak)
    m = nak_idx(moon_nak)

    # Perimeter layout: (row, col, nak_index)
    perimeter = [
        (0, 1, 21),
        (0, 2, 20),
        (0, 3, 19),
        (0, 4, 18),
        (0, 5, 17),
        (0, 6, 16),
        (0, 7, 15),
        (0, 8, 14),
        (1, 8, 13),
        (2, 8, 12),
        (3, 8, 11),
        (4, 8, 10),
        (5, 8, 9),
        (6, 8, 8),
        (7, 8, 7),
        (8, 8, 6),
        (8, 7, 5),
        (8, 6, 4),
        (8, 5, 3),
        (8, 4, 2),
        (8, 3, 1),
        (8, 2, 0),
        (8, 1, 26),
        (7, 0, 25),
        (6, 0, 24),
        (5, 0, 23),
        (4, 0, 22),
        (3, 0, 21),
        (2, 0, 20),
        (1, 0, 19),
    ]

    short = [
        "Ashwini",
        "Bharani",
        "Krittika",
        "Rohini",
        "Mrigshira",
        "Ardra",
        "Punarvasu",
        "Pushya",
        "Ashlesha",
        "Magha",
        "P.Phalguni",
        "U.Phalguni",
        "Hasta",
        "Chitra",
        "Swati",
        "Vishakha",
        "Anuradha",
        "Jyeshtha",
        "Moola",
        "P.Ashadha",
        "U.Ashadha",
        "Shravana",
        "Dhanishtha",
        "Shatabhisha",
        "P.Bhadra",
        "U.Bhadra",
        "Revati",
    ]

    cell_map = {(row, col): nak for row, col, nak in perimeter}

    zodiac = [
        ["", "Sg", "Sc", "Li", "Vi", "Le", "Ca", "Ge", ""],
        ["Cp", "", "", "", "", "", "", "", "Ta"],
        ["Aq", "", "", "", "", "", "", "", "Ar"],
        ["Pi", "", "", "", "", "", "", "", "Pi"],
        ["Ar", "", "", "", "", "", "", "", "Aq"],
        ["Ta", "", "", "", "", "", "", "", "Cp"],
        ["Ge", "", "", "", "", "", "", "", "Sg"],
        ["Ca", "", "", "", "", "", "", "", "Sc"],
        ["", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", ""],
    ]
    tithi_inner = {
        (4, 2): "Jaya",
        (4, 3): "Purna",
        (4, 4): "Nanda",
        (5, 2): "Bhadra",
        (5, 3): "Rikta",
    }
    corners = {(0, 0): "NW", (0, 8): "NE", (8, 0): "SW", (8, 8): "SE"}
    dir_labels = {"top": "NORTH", "bottom": "SOUTH", "left": "WEST", "right": "EAST"}

    def cell_style(row, col, nak_i):
        is_corner = (row in [0, 8]) and (col in [0, 8])
        if is_corner:
            return "background:#f1f1f1;color:#aaa;"
        if nak_i == s:
            return "background:#EEEDFE;border:2px solid #534AB7;color:#3C3489;font-weight:600;"
        if nak_i == f:
            return "background:#E6F1FB;border:1.5px solid #378ADD;color:#185FA5;"
        if nak_i == l:
            return "background:#EAF3DE;border:1.5px solid #639922;color:#3B6D11;"
        if nak_i == r:
            return "background:#FAEEDA;border:1.5px solid #BA7517;color:#854F0B;"
        if nak_i == m and m != -1:
            return "background:#FAECE7;border:1.5px solid #D85A30;color:#993C1D;"
        return "background:#f8f8f8;color:#333;"

    CELL = 64
    GAP = 2

    rows_html = ""
    for row in range(9):
        cells_html = ""
        for col in range(9):
            nak_i = cell_map.get((row, col), None)
            is_perimeter = nak_i is not None
            is_corner = (row in [0, 8]) and (col in [0, 8])

            style = f"width:{CELL}px;height:{CELL}px;display:inline-flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-radius:4px;border:0.5px solid #ddd;font-size:10px;vertical-align:top;margin:{GAP//2}px;box-sizing:border-box;padding:2px;"

            if is_corner:
                style += "background:#eee;color:#bbb;"
                text = corners.get((row, col), "")
                cells_html += f'<div style="{style}">{text}</div>'
            elif is_perimeter:
                style += cell_style(row, col, nak_i)
                badge = (
                    f'<div style="font-size:7px;background:#FAECE7;color:#993C1D;border-radius:2px;padding:1px 3px;margin-top:1px">Moon</div>'
                    if nak_i == m and m != -1
                    else ""
                )
                cells_html += f'<div style="{style}"><span style="font-weight:500">{short[nak_i]}</span>{badge}</div>'
            else:
                style += "background:#fff;color:#999;"
                t = tithi_inner.get((row, col), "")
                z = zodiac[row][col]
                content = t if t else z
                cells_html += f'<div style="{style}">{content}</div>'

        rows_html += f'<div style="white-space:nowrap">{cells_html}</div>'

    legend = """
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px;font-size:12px;color:#555">
      <span><span style="display:inline-block;width:12px;height:12px;background:#EEEDFE;border:1.5px solid #534AB7;border-radius:2px;vertical-align:middle;margin-right:4px"></span>Stock nakshatra</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#E6F1FB;border:1.5px solid #378ADD;border-radius:2px;vertical-align:middle;margin-right:4px"></span>Front vedha</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#EAF3DE;border:1.5px solid #639922;border-radius:2px;vertical-align:middle;margin-right:4px"></span>Left vedha</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#FAEEDA;border:1.5px solid #BA7517;border-radius:2px;vertical-align:middle;margin-right:4px"></span>Right vedha</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#FAECE7;border:1.5px solid #D85A30;border-radius:2px;vertical-align:middle;margin-right:4px"></span>Moon transit</span>
    </div>"""

    return f"""
    <div style="font-family:sans-serif;padding:8px">
      <div style="text-align:center;font-size:11px;color:#888;margin-bottom:4px">NORTH</div>
      <div style="display:flex;align-items:center;gap:4px">
        <div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:11px;color:#888">WEST</div>
        <div>{rows_html}</div>
        <div style="writing-mode:vertical-rl;font-size:11px;color:#888">EAST</div>
      </div>
      <div style="text-align:center;font-size:11px;color:#888;margin-top:4px">SOUTH</div>
      {legend}
    </div>"""


# ── Inputs ──────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Symbol (e.g. NIFTY, BANKNIFTY, RELIANCE)", value="NIFTY")
    sector = st.text_input(
        "Sector (e.g. Financial Services, Bank, IT, Pharma)", value="Financial Services"
    )

with col2:
    use_now = st.checkbox("Use current date & time", value=True)
    if not use_now:
        date_input = st.date_input("Select Date")
        time_input = st.time_input("Select Time (IST)")

    ephe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")

analyse = st.button("🔍 Run SBC Analysis", type="primary")

# ── Run ─────────────────────────────────────────────────────
if analyse and symbol:
    with st.spinner("Computing planetary positions and SBC..."):
        try:
            if use_now:
                dt = datetime.now(timezone.utc)
            else:
                from datetime import timedelta

                # Convert IST to UTC (IST = UTC+5:30)
                ist_naive = datetime.combine(date_input, time_input)
                dt = ist_naive.replace(tzinfo=timezone.utc) - timedelta(
                    hours=5, minutes=30
                )

            result = analyse_symbol(
                symbol=symbol.strip().upper(),
                sector=sector.strip(),
                ephe_path=ephe_path,
                dt=dt,
            )

            # ── Score card ──────────────────────────────────
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SBC Score", f"{result.sbc_score}/100")
            m2.metric("Signal", result.sbc_label)
            m3.metric("Stock Nakshatra", result.stock_nak)
            m4.metric("Tithi", f"{result.tithi} ({result.paksha})")

            # ── Vedha directions ────────────────────────────
            st.subheader("Vedha Directions for " + result.stock_nak)
            d1, d2, d3 = st.columns(3)
            d1.info(f"**FRONT** → {result.vedha_front_nak}")
            d2.info(f"**LEFT** → {result.vedha_left_nak}")
            d3.info(f"**RIGHT** → {result.vedha_right_nak}")

            if result.moon_malefic_paksha:
                st.warning("⚠️ Moon is acting as MALEFIC (Krishna Paksha rule active)")

            # ── Planet table ────────────────────────────────
            st.subheader("Planet-by-Planet Analysis")
            import pandas as pd

            rows = []
            for r in result.planet_results:
                rows.append(
                    {
                        "Planet": r.planet,
                        "Nakshatra": r.planet_nak,
                        "Pada": r.planet_pada,
                        "Directions": " + ".join(r.active_directions),
                        "Hits Stock": "✅ Yes" if r.hits else "—",
                        "Nature": "Benefic" if r.is_benefic else "Malefic",
                        "Strength": r.strength.capitalize(),
                        "Debilitated": "Yes" if r.is_debilitated else "—",
                        "Combust": "Yes" if r.is_combust else "—",
                        "Mutual Vedha": "Yes" if r.mutual_vedha else "—",
                        "Score": f"{r.raw_score:+.1f}",
                        "Notes": " | ".join(r.notes) if r.notes else "—",
                    }
                )
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            # ── SBC Grid ────────────────────────────────────────────────
            st.subheader("Sarvatobhadra Chakra Grid")

            # Build the grid HTML
            front_nak = result.vedha_front_nak
            left_nak = result.vedha_left_nak
            right_nak = result.vedha_right_nak
            stock_nak = result.stock_nak

            # Get Moon nakshatra from planet results
            moon_result = next(
                (r for r in result.planet_results if r.planet == "Moon"), None
            )
            moon_nak = moon_result.planet_nak if moon_result else ""

            st.components.v1.html(
                build_sbc_grid_html(
                    stock_nak, front_nak, left_nak, right_nak, moon_nak
                ),
                height=700,
                scrolling=False,
            )

            # ── Commodity relevance ─────────────────────────
            st.subheader("Commodity / Sector Relevance")
            st.write(
                f"**Stock Nakshatra ({result.stock_nak}) signifies:** {', '.join(result.stock_commodities)}"
            )
            if result.sector_commodity_matches:
                st.success(
                    f"✅ Sector match found: {', '.join(result.sector_commodity_matches)}"
                )
            else:
                st.info("No direct commodity match for this sector.")

        except Exception as e:
            st.error(f"Error: {e}")
            st.info(
                "Make sure the ephe/ folder is present in your repository with the .se1 files."
            )
