import streamlit as st
from datetime import datetime, timezone, timedelta
import os
import sys

# ── Path setup — ensure local sbc_engine is imported ──────────────────────────
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
# COMPLETE 9×9 SBC GRID RENDERER
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
    """
    Renders the full classical 9×9 Sarvatobhadra Chakra grid with:
      • Outer ring: 28 Nakshatras + 4 Corner Vowels
      • 2nd ring:   Sanskrit consonant groups (Aksharas)
      • 3rd ring:   12 Rashis
      • Inner ring: Tithi groups + Varas
      • Centre:     SBC focal point
    """
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
        "Sunday": "Sun Vara",
        "Monday": "Mon Vara",
        "Tuesday": "Tue Vara",
        "Wednesday": "Wed Vara",
        "Thursday": "Thu Vara",
        "Friday": "Fri Vara",
        "Saturday": "Sat Vara",
    }
    active_vara_cell = clean_vara_labels.get(vara_today, "")

    cells_html = []
    CELL = 62  # px per cell

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

            if layer == "vara":
                raw_to_clean = {
                    "☉ Sun": "Sun Vara",
                    "☽ Mon": "Mon Vara",
                    "♂ Tue": "Tue Vara",
                    "☿ Wed": "Wed Vara",
                    "♃ Thu": "Thu Vara",
                    "♀ Fri": "Fri Vara",
                    "♄ Sat": "Sat Vara",
                }
                display_text = raw_to_clean.get(text, text)

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
                    style = (
                        base_style
                        + "background:#EEEDFE;border:3px solid #534AB7;color:#3C3489;font-weight:700;"
                    )
                elif ni == f:
                    style = (
                        base_style
                        + "background:#E6F1FB;border:3px solid #378ADD;color:#185FA5;font-weight:600;"
                    )
                elif ni == l:
                    style = (
                        base_style
                        + "background:#EAF3DE;border:3px solid #639922;color:#3B6D11;font-weight:600;"
                    )
                elif ni == r:
                    style = (
                        base_style
                        + "background:#FAEEDA;border:3px solid #BA7517;color:#854F0B;font-weight:600;"
                    )
                else:
                    style = (
                        base_style
                        + "background:#fafafa;border:1px solid #ddd;color:#444;"
                    )

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
                style = (
                    base_style
                    + "background:#F0E6FF;border:2px solid #9B7FD4;color:#5B2D8E;font-weight:700;font-size:10px;"
                )
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "vowel":
                style = (
                    base_style
                    + "background:#FFF8E7;border:1px solid #DDB850;color:#7A5C00;font-size:9px;"
                )
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "rashi":
                style = (
                    base_style
                    + "background:#E8F4FD;border:1px solid #7AB8E8;color:#1A4F7A;font-size:8px;font-weight:600;"
                )
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "tithi":
                is_active = display_text == active_tithi_cell
                if is_active:
                    style = (
                        base_style
                        + "background:#FFF3C4;border:2px solid #F59E0B;color:#92400E;font-weight:700;box-shadow:0 0 6px #F59E0B60;"
                    )
                else:
                    style = (
                        base_style
                        + "background:#FDF6E3;border:1px solid #E8C96A;color:#7A5C00;font-size:7px;"
                    )
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "vara":
                is_active = display_text == active_vara_cell
                if is_active:
                    style = (
                        base_style
                        + "background:#D1FAE5;border:2px solid #059669;color:#065F46;font-weight:700;box-shadow:0 0 6px #05966960;"
                    )
                else:
                    style = (
                        base_style
                        + "background:#F0FDF4;border:1px solid #6EE7B7;color:#065F46;font-size:9px;"
                    )
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            elif layer == "center":
                style = (
                    base_style
                    + "background:linear-gradient(135deg,#FAECE7,#FDE8D8);border:2px solid #C87941;color:#7C2D12;font-weight:700;font-size:9px;"
                )
                cells_html.append(f'<div style="{style}">{display_text}</div>')

            else:
                style = (
                    base_style + "background:#f5f5f5;color:#777;border:1px solid #ddd;"
                )
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
    <div style="padding:16px;background:#f7f7f7;border:1px solid #ccc;
                border-radius:10px;text-align:center;font-family:'Segoe UI',sans-serif;">
      <div style="margin-bottom:10px;font-weight:700;color:#2d2d2d;font-size:15px;
                  letter-spacing:1px;">SARVATOBHADRA CHAKRA — 9×9</div>
      <div style="display:flex;align-items:center;justify-content:center;gap:10px;">
        <div style="writing-mode:vertical-rl;transform:rotate(180deg);
                    font-size:10px;color:#888;letter-spacing:2px;">WEST ◄</div>
        <div>
          <div style="font-size:10px;color:#888;margin-bottom:4px;letter-spacing:2px;">▲ NORTH</div>
          <div style="display:grid;grid-template-columns:repeat(9,{CELL}px);
                      grid-template-rows:repeat(9,{CELL}px);gap:2px;
                      background:#ccc;padding:2px;border-radius:6px;">
            {"".join(cells_html)}
          </div>
          <div style="font-size:10px;color:#888;margin-top:4px;letter-spacing:2px;">▼ SOUTH</div>
        </div>
        <div style="writing-mode:vertical-rl;font-size:10px;color:#888;
                    letter-spacing:2px;">► EAST</div>
      </div>
      {legend}
      <div style="margin-top:10px;font-size:10px;color:#aaa;">
        5 Panchaka layers: Nakshatra · Akshara (consonants) · Rashi · Tithi · Vara
      </div>
    </div>
    """


# ── Inputs ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Symbol (e.g. NIFTY, BANKNIFTY, RELIANCE)", value="NIFTY")
    sector = st.text_input(
        "Sector (e.g. Financial Services, Bank, IT, Pharma)", value="Financial Services"
    )

    nak_method = st.selectbox(
        "Stock Nakshatra Derivation Method",
        options=["phonetic", "listing_date", "manual"],
        format_func=lambda x: (
            "Phonetic (Name Vibration)"
            if x == "phonetic"
            else (
                "Historical Listing Date (Ephemeris)"
                if x == "listing_date"
                else "Manual Input"
            )
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


# ── Run ───────────────────────────────────────────────────────────────────────
if analyse_btn and symbol:
    with st.spinner("Computing planetary positions and SBC..."):
        try:
            if use_now:
                dt = datetime.now(timezone.utc)
            else:
                ist_naive = datetime.combine(date_input, time_input)
                dt = ist_naive.replace(tzinfo=timezone.utc) - timedelta(
                    hours=5, minutes=30
                )

            result = analyse_symbol(
                symbol=symbol.strip().upper(),
                sector=sector.strip(),
                ephe_path=ephe_path,
                dt=dt,
                nak_method=nak_method,
                manual_nak=manual_nak,
            )

            st.markdown("---")

            # ── Metrics ───────────────────────────────────────────────────────
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Stock Symbol", result.symbol)
            m_col2.metric("Calculated Nakshatra", result.stock_nak)
            m_col3.metric("Panchang Tithi", f"{result.tithi} ({result.paksha})")
            m_col4.metric("SBC Sentiment Score", f"{result.sbc_score:+.1f}")

            # ── Content Layout ────────────────────────────────────────────────
            left_pane, right_pane = st.columns([1.1, 0.9])

            with left_pane:
                # ── SBC Grid ──────────────────────────────────────────────────
                st.subheader("Sarvatobhadra Chakra — Full Classical 9×9 Grid")

                moon_nak = ""
                if hasattr(result, "planet_results") and result.planet_results:
                    for pr in result.planet_results:
                        p_name = getattr(pr, "planet", "")
                        if p_name == "Moon":
                            moon_nak = getattr(pr, "planet_nak", "")
                            break

                # Today's weekday in IST
                ist_now = dt + timedelta(hours=5, minutes=30)
                vara_today = ist_now.strftime("%A")

                # Build a dictionary mapping Nakshatras to their active transiting planets safely
                transits_dict = {}
                if hasattr(result, "planet_results") and result.planet_results:
                    for pr in result.planet_results:
                        nak_name = getattr(pr, "planet_nak", None)
                        p_label = getattr(pr, "planet", None)

                        if not nak_name or not p_label:
                            continue

                        # Convert raw names to standard Vedic glyph formats for the perimeter view
                        if p_label == "Sun":
                            p_label = "☉ Sun"
                        elif p_label == "Moon":
                            p_label = "☽ Mon"
                        elif p_label == "Mars":
                            p_label = "♂ Tue"
                        elif p_label == "Mercury":
                            p_label = "☿ Wed"
                        elif p_label == "Jupiter":
                            p_label = "♃ Thu"
                        elif p_label == "Venus":
                            p_label = "♀ Fri"
                        elif p_label == "Saturn":
                            p_label = "♄ Sat"
                        elif p_label == "Rahu":
                            p_label = "Rahu"
                        elif p_label == "Ketu":
                            p_label = "Ketu"

                        if nak_name not in transits_dict:
                            transits_dict[nak_name] = []
                        transits_dict[nak_name].append(p_label)

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
                    height=760,
                    scrolling=False,
                )

            with right_pane:
                # ── Planet Table ──────────────────────────────────────────────
                st.subheader("🪐 Planet-by-Planet Vedha Analysis")

                table_data = []
                if hasattr(result, "planet_results") and result.planet_results:
                    for pr in result.planet_results:
                        # SAFELY look up properties so it never crashes if names change
                        p_name = getattr(pr, "planet", "Unknown")
                        p_nak = getattr(pr, "planet_nak", "Unknown")
                        p_speed = getattr(pr, "speed", 0.0)
                        p_dirs = getattr(pr, "vedha_directions", [])

                        is_hit = getattr(pr, "is_vedha_hit", False) or getattr(
                            pr, "hits_stock", False
                        )
                        hits_stock_str = "🎯 YES" if is_hit else "no"

                        score_contrib = getattr(pr, "score_contribution", 0.0)

                        table_data.append(
                            {
                                "Planet": p_name,
                                "Current Nakshatra": p_nak,
                                "Motion Speed": f"{p_speed:.2f}°/d",
                                "Vedha Directions": "+".join(p_dirs),
                                "Hits Stock?": hits_stock_str,
                                "SBC Weight": f"{score_contrib:+.1f}",
                            }
                        )
                st.table(table_data)

            # ── Price Levels ──────────────────────────────────────────────────
            if hasattr(result, "price_levels") and result.price_levels:
                st.subheader("🎯 SBC Algorithmic Support & Resistance Levels")
                level_rows = []
                for lv in result.price_levels:
                    icon = (
                        "🔴 Resistance"
                        if lv["type"] == "resistance"
                        else "🟢 Support" if lv["type"] == "support" else "🔵 Pivot/CMP"
                    )
                    level_rows.append(
                        {
                            "Type": icon,
                            "Price Level": f"₹ {lv['price']:,.2f}",
                            "Chakra Assignment": lv["label"],
                            "Strength": lv["strength"].capitalize(),
                            "Transiting Planets": (
                                ", ".join(lv["planets"]) if lv["planets"] else "None"
                            ),
                            "Technical Note": lv["note"],
                        }
                    )
                st.table(level_rows)

            # ── Classical rules explainer ──────────────────────────────────────
            with st.expander("📖 How to read this analysis"):
                st.markdown("""
**Sarvatobhadra Chakra** is a classical 9×9 Vedic matrix with 5 identity layers (Panchaka):

| Ring | Layer | Classical Meaning |
|------|-------|------------------|
| Outer (32 sq) | 28 Nakshatras + 4 Corner Vowels | Macro-cosmic stellar influences |
| 2nd (24 sq) | Sanskrit Consonant Groups (Aksharas) | Phonetic/name vibration |
| 3rd (16 sq) | 12 Rashis (Zodiac Signs) | Physical manifestation / houses |
| Inner (8 sq) | 5 Tithi groups + 7 Varas | Temporal timing |
| Centre (1 sq) | Focal point | The core of the reading |

**Vedha (Piercing) Directions:**
- **Front (Agra)** — used by planets in normal direct motion
- **Left (Vaama)** — used by retrograde planets & those just turned direct (grace period)
- **Right (Dakshina)** — used by fast/Atichari planets

**Sun/Moon/Rahu/Ketu** always cast Vedha on all 3 sides simultaneously.

**Benefic Vedha** (Jupiter, Venus, bright Moon, unafflicted Mercury) → bearish pressure
**Malefic Vedha** (Sun, Mars, Saturn, Rahu, Ketu) → bullish/reversal signal
                """)

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback

            st.code(traceback.format_exc())
