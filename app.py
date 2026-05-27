import streamlit as st
from datetime import datetime, timezone
from sbc_engine import analyse_symbol, print_report, SBCResult, NAKSHATRAS
import os

st.set_page_config(page_title="SBC Analyser", page_icon="🔵", layout="wide")

st.title("🔵 Sarvatobhadra Chakra Analyser")
st.caption("Classical SBC analysis for stocks and indices")

# ── Inputs ──────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Symbol (e.g. NIFTY, BANKNIFTY, RELIANCE)", value="NIFTY")
    sector = st.text_input("Sector (e.g. Financial Services, Bank, IT, Pharma)", value="Financial Services")

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
                dt = ist_naive.replace(tzinfo=timezone.utc) - timedelta(hours=5, minutes=30)

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
                rows.append({
                    "Planet":     r.planet,
                    "Nakshatra":  r.planet_nak,
                    "Pada":       r.planet_pada,
                    "Directions": " + ".join(r.active_directions),
                    "Hits Stock": "✅ Yes" if r.hits else "—",
                    "Nature":     "Benefic" if r.is_benefic else "Malefic",
                    "Strength":   r.strength.capitalize(),
                    "Debilitated":"Yes" if r.is_debilitated else "—",
                    "Combust":    "Yes" if r.is_combust else "—",
                    "Mutual Vedha":"Yes" if r.mutual_vedha else "—",
                    "Score":      f"{r.raw_score:+.1f}",
                    "Notes":      " | ".join(r.notes) if r.notes else "—",
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            # ── Commodity relevance ─────────────────────────
            st.subheader("Commodity / Sector Relevance")
            st.write(f"**Stock Nakshatra ({result.stock_nak}) signifies:** {', '.join(result.stock_commodities)}")
            if result.sector_commodity_matches:
                st.success(f"✅ Sector match found: {', '.join(result.sector_commodity_matches)}")
            else:
                st.info("No direct commodity match for this sector.")

        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Make sure the ephe/ folder is present in your repository with the .se1 files.")
