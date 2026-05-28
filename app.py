import streamlit as st
from datetime import datetime, timezone, timedelta
import os
import sys

# Ensure local sbc_engine directory takes resolution precedence
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sbc_engine import (
    analyse_symbol,
    SBCResult,
    NAKSHATRAS,
    NAKSHATRAS_28,
    SBC_GRID_CELLS,
    NAK_SHORT,
    nak_index,
)

st.set_page_config(page_title="SBC Analyser", page_icon="🔵", layout="wide")

st.title("🔵 Sarvatobhadra Chakra Analyser")
st.caption("Classical SBC analysis — complete 9×9 grid with all 5 Panchaka layers")


# ─────────────────────────────────────────────────────────────────────────────
# COMPLETE 9×9 SBC GRID RENDERER (FIXED)
# ─────────────────────────────────────────────────────────────────────────────
def build_sbc_grid_html(
    stock_nak: str,
    front_nak: str,
    left_nak: str,
    right_nak: str,
    moon_nak: str,
    tithi: int,
    paksha: str,
    vara_today: str,
    planetary_transits: dict = None,
) -> str:
    if planetary_transits is None:
        planetary_transits = {}

    def _nak_idx(name: str) -> int:
        try:
            return nak_index(name)
        except Exception:
            return -1

    s = _nak_idx(stock_nak)
    f = _nak_idx(front_nak)
    l = _nak_idx(left_nak)
    r = _nak_idx(right_nak)
    m = _nak_idx(moon_nak)

    def _cell_nak_idx(cell_name: str) -> int:
        return _nak_idx(cell_name)

    tithi_group_map = {
        "T1-6\nPratipada": range(1, 7),
        "T7-12\nSaptami": range(7, 13),
        "T13-18\nTrayodashi": range(13, 19),
        "T19-24\nNavami": range(19, 25),
        "T25-30\nPanchami": range(25, 31),
    }
    active_tithi_cell = None
    for label, trange in tithi_group_map.items():
        if tithi in trange:
            active_tithi_cell = label
            break

    clean_vara_labels = {
        "Sunday": "☉ Sun",
        "Monday": "☽ Mon",
        "Tuesday": "♂ Tue",
        "Wednesday": "☿ Wed",
        "Thursday": "♃ Thu",
        "Friday": "♀ Fri",
        "Saturday": "♄ Sat",
    }
    active_vara_cell = clean_vara_labels.get(vara_today, "")

    cells_html = []
    CELL = 62  # Pixel height/width square metric

    for row in range(9):
        for col in range(9):
            cell = SBC_GRID_CELLS.get((row, col))
            if cell is None:
                cells_html.append(
                    f'<div style="width:{CELL}px;height:{CELL}px;'
                    f'background:#f0f0f0;border:1px solid #e0e0e0;border-radius:3px;"></div>'
                )
                continue

            layer, text = cell
            display_text = text

            base_style = (
                f"width:{CELL}px;height:{CELL}px;"
                "display:flex;flex-direction:column;align-items:center;"
                "justify-content:center;text-align:center;"
                "border-radius:4px;font-size:8px;position:relative;"
                "white-space:pre-line;line-height:1.2;"
            )

            moon_badge = ""
            planet_badges = ""

            if layer == "nak":
                ni = _cell_nak_idx(text)

                if text in planetary_transits:
                    planets_here = planetary_transits[text]
                    if planets_here:
                        planet_badges = f'<div style="background:#4B5563;color:#fff;padding:1px 3px;border-radius:3px;font-size:7px;margin-top:2px;font-weight:bold;">{" ".join(planets_here)}</div>'

                if ni == s:
                    style = base_style + "background:#EEEDFE;border:3px solid #534AB7;color:#3C3489;font-weight:700;"
                elif ni == f:
                    style = base_style + "background:#E6F1FB;border:3px solid #378ADD;color:#185FA5;font-weight:600;"
                elif ni == l:
                    style = base_style + "background:#EAF3DE;border:3px solid #639922;color:#3B6D11;font-weight:600;"
                elif ni == r:
                    style = base_style + "background:#FAEEDA;border:3px solid #BA7517;color:#854F0B;font-weight:600;"
                else:
                    style = base_style + "background:#fafafa;border:1px solid #ddd;color:#444;"

                if ni == m and m != -1:
                    moon_badge = '<div style="position:absolute;top:2px;right:3px;font-size:9px;">🌕</div>'

                display_name = NAK_SHORT.get(ni, text[:8])
                cells_html.append(
                    f'<div style="{style}">'
                    f'<span style="font-size:7px;color:#888;font-weight:400;">#{ni+1 if ni < 27 else "Ab"}</span>'
                    f'<span style="font-size:8px;font-weight:600;">{display_name}</span>'
                    f"{planet_badges}"
                    f"{moon_badge}</div>"
                )

            elif layer == "corner":
                style = base_style + "background:#F0E6FF;border:2px solid #9B7FD4;color:#5B2D8E;font-weight:700;font-size:10px;"
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "vowel":
                style = base_style + "background:#FFF8E7;border:1px solid #DDB850;color:#7A5C00;font-size:9px;"
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "rashi":
                style = base_style + "background:#E8F4FD;border:1px solid #7AB8E8;color:#1A4F7A;font-size:8px;font-weight:600;"
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "tithi":
                is_active = display_text == active_tithi_cell
                if is_active:
                    style = base_style + "background:#FFF3C4;border:2px solid #F59E0B;color:#92400E;font-weight:700;box-shadow:0 0 6px #F59E0B60;"
                else:
                    style = base_style + "background:#FDF6E3;border:1px solid #E8C96A;color:#7A5C00;font-size:7px;"
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "vara":
                is_active = (display_text == active_vara_cell)
                if is_active:
                    style = base_style + "background:#D1FAE5;border:2px solid #059669;color:#065F46;font-weight:700;box-shadow:0 0 6px #05966960;"
                else:
                    style = base_style + "background:#F0FDF4;border:1px solid #6EE7B7;color:#065F46;font-size:9px;"
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "center":
                style = base_style + "background:linear-gradient(135deg,#FAECE7,#FDE8D8);border:2px solid #C87941;color:#7C2D12;font-weight:700;font-size:9px;"
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            else:
                style = base_style + "background:#f5f5f5;color:#777;border:1px solid #ddd;"
                cells_html.append(f'<div style="{style}">{display_text}</div>')

    legend = f"""
    <div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:10px;justify-content:center;font-size:11px;">
      <span style="background:#EEEDFE;border:2px solid #534AB7;color:#3C3489;padding:3px 8px;border-radius:4px;font-weight:600;">■ Stock Nak: {stock_nak}</span>
      <span style="background:#E6F1FB;border:2px solid #378ADD;color:#185FA5;padding:3px 8px;border-radius:4px;">■ Front: {front_nak}</span>
      <span style="background:#EAF3DE;border:2px solid #639922;color:#3B6D11;padding:3px 8px;border-radius:4px;">■ Left: {left_nak}</span>
      <span style="background:#FAEEDA;border:2px solid #BA7517;color:#854F0B;padding:3px 8px;border-radius:4px;">■ Right: {right_nak}</span>
      <span style="padding:3px 8px;border-radius:4px;background:#f0f0f0;color:#555;">🌕 Moon: {moon_nak}</span>
      <span style="padding:3px 8px;border-radius:4px;background:#FFF3C4;border:1px solid #F59E0B;color:#92400E;">★ Tithi {tithi} ({paksha})</span>
      <span style="padding:3px 8px;border-radius:4px;background:#D1FAE5;border:1px solid #059669;color:#065F46;">▶ {vara_today}</span>
    </div>
    """

    return f"""
    <div style="padding:16px;background:#f7f7f7;border:1px solid #ccc;border-radius:10px;text-align:center;font-family:'Segoe UI',sans-serif;">
      <div style="margin-bottom:10px;font-weight:700;color:#2d2d2d;font-size:15px;letter-spacing:1px;">SARVATOBHADRA CHAKRA — 9×9 MATRIX</div>
      <div style="display:flex;align-items:center;justify-content:center;gap:10px;">
        <div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:10px;color:#888;letter-spacing:2px;">WEST ◄</div>
        <div>
          <div style="font-size:10px;color:#888;margin-bottom:4px;letter-spacing:2px;">▲ NORTH</div>
          <div style="display:grid;grid-template-columns:repeat(9,{CELL}px);grid-template-rows:repeat(9,{CELL}px);gap:2px;background:#ccc;padding:2px;border-radius:6px;">
            {"".join(cells_html)}
          </div>
          <div style="font-size:10px;color:#888;margin-top:4px;letter-spacing:2px;">▼ SOUTH</div>
        </div>
        <div style="writing-mode:vertical-rl;font-size:10px;color:#888;letter-spacing:2px;">► EAST</div>
      </div>
      {legend}
    </div>
    """


# ── INPUT DASHBOARD VIEW CONFIGURATION ───────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Symbol (e.g. NIFTY, BANKNIFTY, RELIANCE)", value="NIFTY")
    sector = st.text_input("Sector (e.g. Financial Services, Bank, IT, Pharma)", value="Financial Services")

    nak_method = st.selectbox(
        "Stock Nakshatra Derivation Method",
        options=["phonetic", "listing_date", "manual"],
        format_func=lambda x: (
            "Phonetic (Name Vibration)"
            if x == "phonetic"
            else ("Historical Listing Date (Ephemeris)" if x == "listing_date" else "Manual Input")
        ),
    )

    if nak_method == "manual":
        manual_nak = st.selectbox("Select Nakshatra", options=NAKSHATRAS_28)
    else:
        manual_nak = None

with col2:
    use_now = st.checkbox("Use current date & time (UTC)", value=True)
    if not use_now:
        date_input = st.date_input("Select Date")
        time_input = st.time_input("Select Time (IST)")

    ephe_path = os.path.join(os.getcwd(), "ephe")

analyse_btn = st.button("🔍 Run SBC Analysis", type="primary")


# ── EXECUTION DEPLOYMENT LAYER ────────────────────────────────────────────────
if analyse_btn and symbol:
    with st.spinner("Computing planetary positions and geometric vectors..."):
        try:
            if use_now:
                dt = datetime.now(timezone.utc)
            else:
                ist_naive = datetime.combine(date_input, time_input)
                dt = ist_naive.replace(tzinfo=timezone.utc) - timedelta(hours=5, minutes=30)

            result = analyse_symbol(
                symbol=symbol.strip().upper(),
                sector=sector.strip(),
                ephe_path=ephe_path,
                dt=dt,
                nak_method=nak_method,
                manual_nak=manual_nak,
            )

            st.markdown("---")

            # Metrics Panel Layout
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("SBC Score", f"{result.sbc_score}/100")
            m2.metric("Signal", result.sbc_label)
            m3.metric("Stock Nakshatra", result.stock_nak)
            m4.metric("Tithi", f"{result.tithi} ({result.paksha})")
            m5.metric("Bullish/Bearish", f"{result.bullish_count}↑ / {result.bearish_count}↓")

            # Aspect Rays Overview
            st.subheader(f"Vedha Directions for {result.stock_nak}")
            d1, d2, d3 = st.columns(3)
            d1.info(f"**FRONT (Agra)** → {result.vedha_front_nak}")
            d2.info(f"**LEFT (Vaama)** → {result.vedha_left_nak}")
            d3.info(f"**RIGHT (Dakshina)** → {result.vedha_right_nak}")

            if result.moon_malefic_paksha:
                st.warning("⚠️ Moon is acting as MALEFIC (Krishna Paksha rule active — Tithi 23–30 or 1–5)")

            # Detailed Planetary Table
            st.subheader("Planet-by-Planet Vedha Analysis")
            import pandas as pd

            rows = []
            for pr in result.planet_results:
                rows.append(
                    {
                        "Planet": pr.planet,
                        "Current Nakshatra": pr.planet_nak,
                        "Motion Speed": f"{pr.motion_speed:.4f}°/d",
                        "Vedha Directions": " + ".join([x.capitalize() for x in pr.active_directions]),
                        "Hits Stock Elements?": "Yes" if pr.hits_stock else "No",
                        "SBC Weight": f"{pr.score_contribution:+.1f}",
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            # Core Geometric Layout Grid Component
            st.subheader("Sarvatobhadra Chakra — Full Classical 9×9 Grid Layout")

            moon_result = next((pr for pr in result.planet_results if pr.planet == "Moon"), None)
            moon_nak = moon_result.planet_nak if moon_result else ""

            ist_now = dt + timedelta(hours=5, minutes=30)
            vara_today = ist_now.strftime("%A")

            transits_dict = {}
            glyph_map = {
                "Gamma": "☉", "Sun": "☉ Sun", "Moon": "☽ Mon", "Mars": "♂ Mars",
                "Mercury": "☿ Mer", "Jupiter": "♃ Jup", "Venus": "♀ Ven", "Saturn": "♄ Sat"
            }
            for pr in result.planet_results:
                lbl = glyph_map.get(pr.planet, pr.planet)
                transits_dict.setdefault(pr.planet_nak, []).append(lbl)

            st.components.v1.html(
                build_sbc_grid_html(
                    stock_nak=result.stock_nak,
                    front_nak=result.vedha_front_nak,
                    left_nak=result.vedha_left_nak,
                    right_nak=result.vedha_right_nak,
                    moon_nak=moon_nak,
                    tithi=result.tithi,
                    paksha=result.paksha,
                    vara_today=vara_today,
                    planetary_transits=transits_dict,
                ),
                height=780,
                scrolling=False,
            )

            # Algorithmic Support & Resistance Interface Dashboard
            if result.price_levels:
                st.subheader("🎯 SBC Algorithmic Support & Resistance Levels")
                level_rows = []
                for lv in result.price_levels:
                    icon = "🔴 Resistance" if lv["type"] == "resistance" else "🟢 Support" if lv["type"] == "support" else "🔵 Baseline CMP"
                    level_rows.append(
                        {
                            "Type": icon,
                            "Price Level": f"₹ {lv['price']:,.2f}",
                            "Chakra Assignment": lv["label"],
                            "Strength": lv["strength"].capitalize(),
                            "Transiting Planets": ", ".join(lv["planets"]) if lv["planets"] else "None",
                            "Technical Note": lv["note"],
                        }
                    )
                st.table(level_rows)

            # Sector Commodity Signifiers
            st.subheader("Commodity / Sector Relevance")
            st.write(f"**Stock Nakshatra ({result.stock_nak}) signifies:** {', '.join(result.stock_commodities)}")
            if result.sector_commodity_matches:
                st.success(f"✅ Sector match found: {', '.join(result.sector_commodity_matches)}")
            else:
                st.info("No direct commodity match for this sector.")

        except Exception as e:
            st.error(f"Execution Error: {e}")
            import traceback
            st.code(traceback.format_exc())
