import streamlit as st
from datetime import datetime, timezone
from sbc_engine import analyse_symbol, print_report, SBCResult, NAKSHATRAS
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="SBC Analyser", page_icon="🔵", layout="wide")

st.title("🔵 Sarvatobhadra Chakra Analyser")
st.caption("Classical SBC analysis for stocks and indices")

def build_sbc_grid_html(stock_nak, front_nak, left_nak, right_nak, moon_nak):
    """Phase 1 - Full classical 9×9 SBC grid with all layers"""
    from sbc_engine import NAKSHATRAS, SBC_GRID_CELLS, NAK_SHORT

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

    grid_cells = []
    for row in range(9):
        for col in range(9):
            cell = SBC_GRID_CELLS.get((row, col), ("inner", "•"))
            layer, text = cell

            if layer == "nak":
                nak_i = nak_idx(text)
                style = "width:68px;height:68px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-radius:4px;font-size:9px;position:relative;font-weight:600;"
                if nak_i == s:
                    style += "background:#EEEDFE;border:3px solid #534AB7;color:#3C3489;"
                elif nak_i == f:
                    style += "background:#E6F1FB;border:3px solid #378ADD;color:#185FA5;"
                elif nak_i == l:
                    style += "background:#EAF3DE;border:3px solid #639922;color:#3B6D11;"
                elif nak_i == r:
                    style += "background:#FAEEDA;border:3px solid #BA7517;color:#854F0B;"
                else:
                    style += "background:#f8f8f8;color:#333;border:1px solid #ddd;"
                moon_badge = '<div style="position:absolute;top:4px;right:4px;font-size:10px;">🌕</div>' if nak_i == m and m != -1 else ''
                grid_cells.append(f'<div style="{style}"><span>{NAK_SHORT.get(nak_i, text)}</span>{moon_badge}</div>')
            else:
                # Inner layers
                grid_cells.append(f'<div style="background:#f0f0f0;color:#777;border:1px solid #ddd;width:68px;height:68px;display:flex;align-items:center;justify-content:center;font-size:9px;">{text}</div>')

    return f"""
    <div style="padding:20px;background:#f8f8f8;border:1px solid #ddd;border-radius:8px;text-align:center">
        <div style="margin-bottom:10px;font-weight:bold;color:#333;font-size:15px">SARVATOBHADRA CHAKRA</div>
        <div style="display:flex;align-items:center;justify-content:center;gap:10px">
            <div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:11px;color:#666">WEST</div>
            <div style="display:grid;grid-template-columns:repeat(9,68px);grid-template-rows:repeat(9,68px);gap:2px;background:#ddd;padding:2px;border-radius:6px">
                {"".join(grid_cells)}
            </div>
            <div style="writing-mode:vertical-rl;font-size:11px;color:#666">EAST</div>
        </div>
        <div style="text-align:center;margin-top:10px;font-size:11px;color:#666">SOUTH</div>
    </div>
    """
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
