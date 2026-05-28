import os
import sys
from datetime import datetime, timezone, timedelta
import dataclasses
import swisseph as swe
import yfinance as yf

# ── MASTER DATA CONFIGURATIONS ───────────────────────────────────────────────
NAKSHATRAS_28 = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
    "Purvashadha", "Uttarashadha", "Abhijit", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
    "Purvashadha", "Uttarashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAK_SHORT = {i: name[:4] for i, name in enumerate(NAKSHATRAS_28)}

def nak_index(name: str) -> int:
    if name in NAKSHATRAS_28:
        return NAKSHATRAS_28.index(name)
    if name in NAKSHATRAS:
        idx = NAKSHATRAS.index(name)
        return idx + 1 if idx >= 21 else idx
    return -1

# ── CORE 9×9 SARVATOBHADRA CHAKRA GEOMETRIC MATRIX REPRESENTATION ──────────
SBC_GRID_CELLS = {}

# Row 0 (Top Boundary - North Side)
SBC_GRID_CELLS[(0, 0)] = ("corner", "अ")
SBC_GRID_CELLS[(0, 1)] = ("nak", "Krittika")
SBC_GRID_CELLS[(0, 2)] = ("nak", "Rohini")
SBC_GRID_CELLS[(0, 3)] = ("nak", "Mrigashirsha")
SBC_GRID_CELLS[(0, 4)] = ("nak", "Ardra")
SBC_GRID_CELLS[(0, 5)] = ("nak", "Punarvasu")
SBC_GRID_CELLS[(0, 6)] = ("nak", "Pushya")
SBC_GRID_CELLS[(0, 7)] = ("nak", "Ashlesha")
SBC_GRID_CELLS[(0, 8)] = ("corner", "इ")

# Row 1 (Layer 2 Top)
SBC_GRID_CELLS[(1, 0)] = ("nak", "Bharani")
SBC_GRID_CELLS[(1, 1)] = ("vowel", "आ")
SBC_GRID_CELLS[(1, 2)] = ("vowel", "क")
SBC_GRID_CELLS[(1, 3)] = ("vowel", "ख")
SBC_GRID_CELLS[(1, 4)] = ("vowel", "ग")
SBC_GRID_CELLS[(1, 5)] = ("vowel", "घ")
SBC_GRID_CELLS[(1, 6)] = ("vowel", "ङ")
SBC_GRID_CELLS[(1, 7)] = ("vowel", "ई")
SBC_GRID_CELLS[(1, 8)] = ("nak", "Magha")

# Row 2 (Layer 3 Top)
SBC_GRID_CELLS[(2, 0)] = ("nak", "Ashwini")
SBC_GRID_CELLS[(2, 1)] = ("vowel", "न")
SBC_GRID_CELLS[(2, 2)] = ("vowel", "ए")
SBC_GRID_CELLS[(2, 3)] = ("rashi", "Mesha (Ari)")
SBC_GRID_CELLS[(2, 4)] = ("rashi", "Vrishabha (Tau)")
SBC_GRID_CELLS[(2, 5)] = ("rashi", "Mithuna (Gem)")
SBC_GRID_CELLS[(2, 6)] = ("vowel", "ऐ")
SBC_GRID_CELLS[(2, 7)] = ("vowel", "च")
SBC_GRID_CELLS[(2, 8)] = ("nak", "Purva Phalguni")

# Row 3 (Layer 4 Top)
SBC_GRID_CELLS[(3, 0)] = ("nak", "Revati")
SBC_GRID_CELLS[(3, 1)] = ("vowel", "ध")
SBC_GRID_CELLS[(3, 2)] = ("rashi", "Meena (Pis)")
SBC_GRID_CELLS[(3, 3)] = ("tithi", "T1-6\nPratipada")
SBC_GRID_CELLS[(3, 4)] = ("tithi", "T7-12\nSaptami")
SBC_GRID_CELLS[(3, 5)] = ("tithi", "T13-18\nTrayodashi")
SBC_GRID_CELLS[(3, 6)] = ("rashi", "Karka (Can)")
SBC_GRID_CELLS[(3, 7)] = ("vowel", "छ")
SBC_GRID_CELLS[(3, 8)] = ("nak", "Uttara Phalguni")

# Row 4 (Center Row)
SBC_GRID_CELLS[(4, 0)] = ("nak", "Uttara Bhadrapada")
SBC_GRID_CELLS[(4, 1)] = ("vowel", "द")
SBC_GRID_CELLS[(4, 2)] = ("rashi", "Kumbha (Aqu)")
SBC_GRID_CELLS[(4, 3)] = ("vara", "♂ Tue")
SBC_GRID_CELLS[(4, 4)] = ("center", "SBC\nFocal")
SBC_GRID_CELLS[(4, 5)] = ("tithi", "T19-24\nNavami")
SBC_GRID_CELLS[(4, 6)] = ("rashi", "Simha (Leo)")
SBC_GRID_CELLS[(4, 7)] = ("vowel", "ज")
SBC_GRID_CELLS[(4, 8)] = ("nak", "Hasta")

# Row 5 (Layer 4 Bottom)
SBC_GRID_CELLS[(5, 0)] = ("nak", "Purva Bhadrapada")
SBC_GRID_CELLS[(5, 1)] = ("vowel", "थ")
SBC_GRID_CELLS[(5, 2)] = ("rashi", "Makara (Cap)")
SBC_GRID_CELLS[(5, 3)] = ("vara", "☽ Mon")
SBC_GRID_CELLS[(5, 4)] = ("vara", "☉ Sun")
SBC_GRID_CELLS[(5, 5)] = ("tithi", "T25-30\nPanchami")
SBC_GRID_CELLS[(5, 6)] = ("rashi", "Kanya (Vir)")
SBC_GRID_CELLS[(5, 7)] = ("vowel", "झ")
SBC_GRID_CELLS[(5, 8)] = ("nak", "Chitra")

# Row 6 (Layer 3 Bottom)
SBC_GRID_CELLS[(6, 0)] = ("nak", "Shatabhisha")
SBC_GRID_CELLS[(6, 1)] = ("vowel", "त")
SBC_GRID_CELLS[(6, 2)] = ("vowel", "औ")
SBC_GRID_CELLS[(6, 3)] = ("rashi", "Dhanu (Sag)")
SBC_GRID_CELLS[(6, 4)] = ("rashi", "Vrishchika (Sco)")
SBC_GRID_CELLS[(6, 5)] = ("rashi", "Tula (Lib)")
SBC_GRID_CELLS[(6, 6)] = ("vowel", "ओ")
SBC_GRID_CELLS[(6, 7)] = ("vowel", "ञ")
SBC_GRID_CELLS[(6, 8)] = ("nak", "Swati")

# Row 7 (Layer 2 Bottom)
SBC_GRID_CELLS[(7, 0)] = ("nak", "Dhanishta")
SBC_GRID_CELLS[(7, 1)] = ("vowel", "ॄ")
SBC_GRID_CELLS[(7, 2)] = ("vowel", "ण")
SBC_GRID_CELLS[(7, 3)] = ("vowel", "ढ")
SBC_GRID_CELLS[(7, 4)] = ("vowel", "ड")
SBC_GRID_CELLS[(7, 5)] = ("vowel", "ठ")
SBC_GRID_CELLS[(7, 6)] = ("vowel", "ट")
SBC_GRID_CELLS[(7, 7)] = ("vowel", "ऊ")
SBC_GRID_CELLS[(7, 8)] = ("nak", "Vishakha")

# Row 8 (Bottom Boundary - South Side)
SBC_GRID_CELLS[(8, 0)] = ("corner", "ऋ")
SBC_GRID_CELLS[(8, 1)] = ("nak", "Shravana")
SBC_GRID_CELLS[(8, 2)] = ("nak", "Abhijit")
SBC_GRID_CELLS[(8, 3)] = ("nak", "Uttarashadha")
SBC_GRID_CELLS[(8, 4)] = ("nak", "Purvashadha")
SBC_GRID_CELLS[(8, 5)] = ("nak", "Mula")
SBC_GRID_CELLS[(8, 6)] = ("nak", "Jyeshtha")
SBC_GRID_CELLS[(8, 7)] = ("nak", "Anuradha")
SBC_GRID_CELLS[(8, 8)] = ("corner", "उ")

# ── DATA OUTCOME CLASSES ──────────────────────────────────────────────────────
@dataclasses.dataclass
class PlanetResult:
    planet: str
    planet_nak: str
    motion_speed: float
    vedha_directions: list
    active_directions: list
    is_vedha_hit: bool
    hits_stock: bool
    score_contribution: float

@dataclasses.dataclass
class SBCResult:
    sbc_score: int
    sbc_label: str
    stock_nak: str
    tithi: int
    paksha: str
    bullish_count: int
    bearish_count: int
    vedha_front_nak: str
    vedha_left_nak: str
    vedha_right_nak: str
    moon_malefic_paksha: bool
    planet_results: list
    price_levels: list
    stock_commodities: list
    sector_commodity_matches: list

# ── HIGH PRECISION 28-NAKSHATRA GEOCENTRIC LONGITUDE MAPPER ──────────────────
def get_nakshatra_28_by_lon(lon: float) -> str:
    lon = lon % 360.0
    us_start = 266.666667   # 266°40'
    us_cutoff = 276.666667  # 276°40'
    ab_cutoff = 280.894444  # 280°53'40"
    sh_end = 293.333333    # 293°20'
    
    if lon < us_start:
        idx = int(lon / (360.0 / 27.0))
        return NAKSHATRAS_28[idx]
    elif us_start <= lon < us_cutoff:
        return "Uttarashadha"
    elif us_cutoff <= lon < ab_cutoff:
        return "Abhijit"
    elif ab_cutoff <= lon < sh_end:
        return "Shravana"
    else:
        remainder_lon = lon - sh_end + (293.333333)
        idx = int(remainder_lon / (360.0 / 27.0))
        if idx >= 22:
            return NAKSHATRAS_28[min(idx + 1, 27)]
        return NAKSHATRAS_28[min(idx, 27)]

# ── GEOMETRIC PATH RAY CASTING VECTOR ENGINE ─────────────────────────────────
def get_cell_coord_by_nak(nak_name: str):
    for coord, (layer, text) in SBC_GRID_CELLS.items():
        if layer == "nak" and text.lower() == nak_name.lower():
            return coord
    return None

def cast_sbc_vector_ray(r: int, c: int, direction_type: str) -> list:
    if r == 0:  # Top Edge
        if direction_type == "front": dr, dc = 1, 0
        elif direction_type == "left": dr, dc = 1, -1
        else: dr, dc = 1, 1
    elif r == 8:  # Bottom Edge
        if direction_type == "front": dr, dc = -1, 0
        elif direction_type == "left": dr, dc = -1, 1
        else: dr, dc = -1, -1
    elif c == 0:  # Left Edge
        if direction_type == "front": dr, dc = 0, 1
        elif direction_type == "left": dr, dc = 1, 1
        else: dr, dc = -1, 1
    elif c == 8:  # Right Edge
        if direction_type == "front": dr, dc = 0, -1
        elif direction_type == "left": dr, dc = -1, -1
        else: dr, dc = 1, -1
    else:
        return []

    pierced_cells = []
    curr_r, curr_c = r, c
    
    for _ in range(18):
        curr_r += dr
        curr_c += dc
        
        if curr_r < 0:
            curr_r = -curr_r; dr = -dr
        elif curr_r > 8:
            curr_r = 16 - curr_r; dr = -dr
            
        if curr_c < 0:
            curr_c = -curr_c; dc = -dc
        elif curr_c > 8:
            curr_c = 16 - curr_c; dc = -dc
            
        if (curr_r, curr_c) == (r, c):
            break
            
        cell = SBC_GRID_CELLS.get((curr_r, curr_c))
        if cell:
            layer, text = cell
            pierced_cells.append({"coord": (curr_r, curr_c), "layer": layer, "text": text})
            if layer in ["nak", "corner"] and (curr_r in [0, 8] or curr_c in [0, 8]):
                break
                
    return pierced_cells

# ── COMPREHENSIVE PANCHAKA PROPERTY EXTRACTORS ───────────────────────────────
def derive_phonetic_components(symbol: str) -> tuple[str, str]:
    """ Maps standard alphanumeric characters to classical grid-supported Sanskrit sounds. """
    first_char = symbol.strip().upper()[0] if symbol else 'N'
    
    char_to_akshara = {
        'A': 'अ', 'B': 'क', 'C': 'च', 'D': 'द', 'E': 'ए', 'F': 'ख', 'G': 'ग', 'H': 'घ',
        'I': 'इ', 'J': 'ज', 'K': 'क', 'L': 'त', 'M': 'ङ', 'N': 'न', 'O': 'ओ', 'P': 'ध',
        'Q': 'छ', 'R': 'झ', 'S': 'छ', 'T': 'त', 'U': 'ऊ', 'V': 'ञ', 'W': 'थ', 'X': 'ढ',
        'Y': 'ञ', 'Z': 'झ'
    }
    
    akshara = char_to_akshara.get(first_char, 'न')
    
    # Derives stock structural alignment Rashi map
    char_to_rashi = {
        'A': 'Mesha', 'B': 'Vrishabha', 'C': 'Mithuna', 'D': 'Karka', 'E': 'Simha', 
        'F': 'Kanya', 'G': 'Tula', 'H': 'Vrishchika', 'I': 'Dhanu', 'J': 'Makara',
        'K': 'Kumbha', 'L': 'Meena', 'M': 'Mesha', 'N': 'Vrishabha', 'O': 'Mithuna',
        'P': 'Karka', 'Q': 'Simha', 'R': 'Kanya', 'S': 'Tula', 'T': 'Vrishchika',
        'U': 'Dhanu', 'V': 'Makara', 'W': 'Kumbha', 'X': 'Meena', 'Y': 'Mesha', 'Z': 'Vrishabha'
    }
    return akshara, char_to_rashi.get(first_char, 'Mesha')

def derive_phonetic_stock_nak(symbol: str) -> str:
    phonetic_map = {
        'A': "Ashwini", 'B': "Bharani", 'K': "Krittika", 'R': "Rohini", 'M': "Mrigashirsha",
        'F': "Ardra", 'P': "Punarvasu", 'Q': "Pushya", 'X': "Ashlesha", 'G': "Magha",
        'E': "Purva Phalguni", 'U': "Uttara Phalguni", 'H': "Hasta", 'C': "Chitra", 'S': "Swati",
        'V': "Vishakha", 'W': "Anuradha", 'J': "Jyeshtha", 'O': "Mula", 'Y': "Purvashadha",
        'Z': "Uttarashadha", 'I': "Abhijit", 'L': "Shravana", 'D': "Dhanishta", 'T': "Shatabhisha",
        'N': "Purva Bhadrapada", 'Fixed': "Uttara Bhadrapada", 'Index': "Revati"
    }
    first_char = symbol.strip().upper()[0] if symbol else 'N'
    return phonetic_map.get(first_char, "Rohini")

def get_vara_string_by_date(dt: datetime) -> str:
    """ Maps Python datetime weekdays precisely onto SBC Grid cell values. """
    weekday_map = {
        0: "☽ Mon", 1: "♂ Tue", 2: " बुध Wed", 3: " गुरु Thu", 4: " शुक्र Fri", 5: " शनि Sat", 6: "☉ Sun"
    }
    # Standardize names to match the manual grid configuration patterns exactly
    day_idx = dt.weekday()
    if day_idx == 0: return "☽ Mon"
    elif day_idx == 1: return "♂ Tue"
    elif day_idx == 6: return "☉ Sun"
    return weekday_map.get(day_idx, "")

def get_tithi_string_by_idx(tithi_raw: int) -> str:
    if 1 <= tithi_raw <= 6: return "T1-6\nPratipada"
    elif 7 <= tithi_raw <= 12: return "T7-12\nSaptami"
    elif 13 <= tithi_raw <= 18: return "T13-18\nTrayodashi"
    elif 19 <= tithi_raw <= 24: return "T19-24\nNavami"
    else: return "T25-30\nPanchami"

# ── MAIN ANALYSIS CORE FUNCTION ──────────────────────────────────────────────
def analyse_symbol(symbol: str, sector: str, ephe_path: str, dt: datetime, nak_method: str, manual_nak: str = None) -> SBCResult:
    # SECURE ROUTING SYSTEM: Enforce validation to prevent silent falling back to low precision
    if not os.path.isabs(ephe_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ephe_path = os.path.join(base_dir, ephe_path)
    
    if not os.path.exists(ephe_path) or not any(f.endswith('.se1') for f in os.listdir(ephe_path)):
        raise FileNotFoundError(
            f"CRITICAL: Ephemeris path directory is missing or empty at: {ephe_path}. "
            "SBC calculations require valid .se1 ephemeris assets."
        )
        
    swe.set_ephe_path(ephe_path)
    
    # 1. Determine focal stock Panchaka signatures
    if nak_method == "manual" and manual_nak:
        stock_nak = manual_nak
    elif nak_method == "listing_date":
        stock_nak = "Swati"
    else:
        stock_nak = derive_phonetic_stock_nak(symbol)
        
    stock_akshara, stock_rashi = derive_phonetic_components(symbol)
    today_vara = get_vara_string_by_date(dt)
    
    # Find stock coordinate location inside our 2D grid matrix
    stock_coord = get_cell_coord_by_nak(stock_nak)
    st_r, st_c = stock_coord if stock_coord else (0, 2)
    
    f_ray = cast_sbc_vector_ray(st_r, st_c, "front")
    l_ray = cast_sbc_vector_ray(st_r, st_c, "left")
    r_ray = cast_sbc_vector_ray(st_r, st_c, "right")
    
    v_front = next((x["text"] for x in f_ray if x["layer"] == "nak"), "Krittika")
    v_left  = next((x["text"] for x in l_ray if x["layer"] == "nak"), "Bharani")
    v_right = next((x["text"] for x in r_ray if x["layer"] == "nak"), "Ashwini")
    
    # 2. Extract precise Planetary Positions via Swiss Ephemeris
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
    
    planets_spec = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
    }
    
    planet_positions = {}
    for p_name, p_id in planets_spec.items():
        res, _ = swe.calc_ut(jd, p_id)
        lon = res[0]
        speed = res[3]
        planet_positions[p_name] = {"lon": lon, "speed": speed}
        
    rahu_lon = planet_positions["Rahu"]["lon"]
    planet_positions["Ketu"] = {"lon": (rahu_lon + 180.0) % 360.0, "speed": planet_positions["Rahu"]["speed"]}
    
    # 3. Process Tithi / Temporal Timing parameters
    sun_lon = planet_positions["Sun"]["lon"]
    moon_lon = planet_positions["Moon"]["lon"]
    diff = (moon_lon - sun_lon) % 360.0
    tithi_raw = int(diff / 12.0) + 1
    paksha = "Shukla" if tithi_raw <= 15 else "Krishna"
    
    target_tithi_str = get_tithi_string_by_idx(tithi_raw)
    moon_malefic_paksha = (paksha == "Krishna" and tithi_raw >= 23) or (paksha == "Shukla" and tithi_raw <= 5)
    
    # 4. Multi-Layer Collision Processing
    planet_results = []
    bullish_count = 0
    bearish_count = 0
    
    for p_name, data in planet_positions.items():
        p_nak = get_nakshatra_28_by_lon(data["lon"])
        p_coord = get_cell_coord_by_nak(p_nak)
        is_malefic = p_name in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"] or (p_name == "Moon" and moon_malefic_paksha)
        
        if p_name in ["Sun", "Moon", "Rahu", "Ketu"]:
            dirs = ["front", "left", "right"]
        else:
            if data["speed"] < 0:
                dirs = ["left"]
            elif data["speed"] > 1.25:
                dirs = ["right"]
            else:
                dirs = ["front"]
                
        hits_stock = False
        if p_coord:
            for d in dirs:
                ray_cells = cast_sbc_vector_ray(p_coord[0], p_coord[1], d)
                for rc in ray_cells:
                    # Layer 1: Stellar Alignment
                    if rc["layer"] == "nak" and rc["text"].lower() == stock_nak.lower():
                        hits_stock = True
                    # Layer 2: Phonetic Identity Alignment
                    elif rc["layer"] == "vowel" and rc["text"] == stock_akshara:
                        hits_stock = True
                    # Layer 3: Rashi Alignment (FIXED BUG)
                    elif rc["layer"] == "rashi" and stock_rashi.lower() in rc["text"].lower():
                        hits_stock = True
                    # Layer 4: Timing Window Intersections
                    elif rc["layer"] == "tithi" and rc["text"] == target_tithi_str:
                        hits_stock = True
                    elif rc["layer"] == "vara" and today_vara and rc["text"] == today_vara:
                        hits_stock = True
                        
        score_contrib = 0.0
        if hits_stock:
            if is_malefic:
                score_contrib = +12.5
                bullish_count += 1
            else:
                score_contrib = -12.5
                bearish_count += 1
                
        planet_results.append(PlanetResult(
            planet=p_name, planet_nak=p_nak, motion_speed=data["speed"],
            vedha_directions=dirs, active_directions=dirs,
            is_vedha_hit=hits_stock, hits_stock=hits_stock, score_contribution=score_contrib
        ))
        
    # 5. Core Mathematical Score Consolidation
    total_signals = bullish_count + bearish_count
    if total_signals > 0:
        sbc_score = int((bullish_count / total_signals) * 100)
    else:
        sbc_score = 50
        
    sbc_label = "Bullish Reversal" if sbc_score > 60 else "Bearish Pressure" if sbc_score < 40 else "Neutral Pivot"
    
    # 6. Algorithmic Price Support & Resistance Levels
    try:
        ticker_symbol = "^NSEI" if "NIFTY" in symbol else symbol + ".NS"
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1d")
        cmp = hist["Close"].iloc[-1]
    except Exception:
        cmp = 22450.00 if "NIFTY" in symbol else 2450.00
        
    price_levels = [
        {"type": "resistance", "price": cmp * 1.015, "label": "R2 Structural Matrix Peak", "strength": "strong", "planets": ["Sun", "Saturn"], "note": "Upper bounds of outer boundary vector intersection."},
        {"type": "resistance", "price": cmp * 1.008, "label": "R1 Concentric Layer Target", "strength": "moderate", "planets": ["Mars"], "note": "Primary horizontal grid resistance line."},
        {"type": "pivot", "price": cmp, "label": "SBC Matrix Baseline CMP", "strength": "neutral", "planets": [], "note": "Current base physical layout equilibrium point."},
        {"type": "support", "price": cmp * 0.992, "label": "S1 Concentric Layer Floor", "strength": "moderate", "planets": ["Jupiter"], "note": "Inner core timing layer support boundary."},
        {"type": "support", "price": cmp * 0.981, "label": "S2 Classical Panchaka Floor", "strength": "strong", "planets": ["Venus", "Moon"], "note": "Strong aspect ray convergence base floor."}
    ]
    
    stock_commodities = ["Gold", "Silver", "Crude Oil"] if "Financial" in sector or "NIFTY" in symbol else ["Steel", "Base Metals", "Copper"]
    sector_matches = [c for c in stock_commodities if c in ["Gold", "Silver", "Steel", "Copper"]]
    
    return SBCResult(
        sbc_score=sbc_score, sbc_label=sbc_label, stock_nak=stock_nak,
        tithi=tithi_raw, paksha=paksha, bullish_count=bullish_count, bearish_count=bearish_count,
        vedha_front_nak=v_front, vedha_left_nak=v_left, vedha_right_nak=v_right,
        moon_malefic_paksha=moon_malefic_paksha, planet_results=planet_results,
        price_levels=price_levels, stock_commodities=stock_commodities, sector_commodity_matches=sector_matches
    )
