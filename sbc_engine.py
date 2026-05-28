from __future__ import annotations
import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# 1.  NAKSHATRA MASTER LIST
# ─────────────────────────────────────────────────────────────────────────────
NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Moola",
    "Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati",
]
ABHIJIT_IDX = 27
NAKSHATRAS_28 = NAKSHATRAS + ["Abhijit"]

NAK_SHORT = {
    0:"Ashwini",1:"Bharani",2:"Krittika",3:"Rohini",4:"Mrigshira",
    5:"Ardra",6:"Punarvasu",7:"Pushya",8:"Ashlesha",9:"Magha",
    10:"P.Phalg",11:"U.Phalg",12:"Hasta",13:"Chitra",14:"Swati",
    15:"Vishakha",16:"Anuradha",17:"Jyeshtha",18:"Moola",
    19:"P.Ashada",20:"U.Ashada",21:"Shravana",22:"Dhanishtha",
    23:"Shatabhisha",24:"P.Bhadra",25:"U.Bhadra",26:"Revati",27:"Abhijit",
}

_NAK_ALIASES = {
    "ashwini":0,"aswini":0,
    "bharani":1,"bharni":1,
    "krittika":2,"kritika":2,"krit":2,
    "rohini":3,"roh":3,
    "mrigashira":4,"mrigshira":4,"mrigsira":4,"mrig":4,
    "ardra":5,
    "punarvasu":6,"puna":6,
    "pushya":7,"push":7,
    "ashlesha":8,"ashl":8,
    "magha":9,"magh":9,
    "purva phalguni":10,"p. phalguni":10,"p.phalguni":10,
    "uttara phalguni":11,"u. phalguni":11,"u.phalguni":11,"uttara falguni":11,
    "hasta":12,"hast":12,
    "chitra":13,"chit":13,
    "swati":14,"swat":14,
    "vishakha":15,"visaka":15,"vishaka":15,"vish":15,
    "anuradha":16,"anu":16,
    "jyeshtha":17,"jyestha":17,"jyes":17,
    "moola":18,"mool":18,"mula":18,
    "purva ashadha":19,"purva shada":19,"p. shada":19,
    "uttara ashadha":20,"uttra shada":20,"u. shada":20,"uttara shada":20,
    "shravana":21,"shravan":21,"srav":21,
    "dhanishtha":22,"dhanistha":22,"dhan":22,
    "shatabhisha":23,"shatbhisha":23,"satabhisha":23,"shata":23,
    "purva bhadrapada":24,"purva bhadrapad":24,"p. bhadrapada":24,
    "uttara bhadrapada":25,"uttara bhadrapad":25,"u. bhadrapada":25,
    "revati":26,"reva":26,
    "abhijit":27,"abhijeet":27,
}


def nak_index(name: str) -> int:
    key = name.strip().lower()
    if key in _NAK_ALIASES:
        return _NAK_ALIASES[key]
    for alias, idx in _NAK_ALIASES.items():
        if alias.startswith(key) or key.startswith(alias):
            return idx
    raise ValueError(f"Unknown nakshatra: '{name}'")


def lon_to_nak_idx(lon: float) -> int:
    return int((lon % 360) / (360 / 27))


def lon_to_nak(lon: float) -> tuple:
    idx = lon_to_nak_idx(lon)
    return idx, NAKSHATRAS[idx]


def lon_to_pada(lon: float) -> int:
    nak_span = 360 / 27
    return int(((lon % 360) % nak_span) / (nak_span / 4)) + 1


def lon_intra_degree(lon: float) -> float:
    return (lon % 360) % (360 / 27)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  PHONETIC AKSHARA → NAKSHATRA MAPPING  (classical pada system)
#     Each nakshatra has 4 padas, each pada maps to one Sanskrit syllable.
#     The first syllable of a name determines its phonetic nakshatra.
# ─────────────────────────────────────────────────────────────────────────────
# Format: phonetic sound → (nakshatra_index, pada)
PHONETIC_MAP: dict[str, tuple[int, int]] = {
    # Ashwini (0)
    "chu":  (0,1), "che":  (0,1),
    "cho":  (0,2),
    "la":   (0,3),
    "li":   (0,4),
    # Bharani (1)
    "lu":   (1,1),
    "le":   (1,2),
    "lo":   (1,3),
    "a":    (1,4),
    # Krittika (2)
    "i":    (2,1),
    "u":    (2,2),
    "e":    (2,3),
    "o":    (2,4),
    # Rohini (3)
    "o":    (3,1),
    "va":   (3,1), "ba":  (3,1),
    "vi":   (3,2), "bi":  (3,2),
    "vu":   (3,3), "bu":  (3,3),
    "ve":   (3,4), "be":  (3,4),
    # Mrigashira (4)
    "vo":   (4,1), "bo":  (4,1),
    "ka":   (4,2),
    "ki":   (4,3),
    "ku":   (4,4),
    # Ardra (5)
    "ge":  (5,1), "ku": (5,1),
    "ko":  (5,2),
    "ha":  (5,3),
    "hi":  (5,4),
    # Punarvasu (6)
    "hu":  (6,1),
    "he":  (6,2),
    "ho":  (6,3),
    "da":  (6,4),
    # Pushya (7)
    "di":  (7,1),
    "du":  (7,2),
    "de":  (7,3),
    "do":  (7,4),
    # Ashlesha (8)
    "di":  (8,1),
    "du":  (8,2),
    "de":  (8,3),
    "do":  (8,4),
    # Magha (9)
    "ma":  (9,1),
    "mi":  (9,2),
    "mu":  (9,3),
    "me":  (9,4),
    # Purva Phalguni (10)
    "mo":  (10,1),
    "ta":  (10,2),
    "ti":  (10,3),
    "tu":  (10,4),
    # Uttara Phalguni (11)
    "te":  (11,1),
    "to":  (11,2),
    "pa":  (11,3),
    "pi":  (11,4),
    # Hasta (12)
    "pu":  (12,1),
    "sh":  (12,2),
    "na":  (12,3),
    "ni":  (12,4),
    # Chitra (13)
    "pe":  (13,1),
    "po":  (13,2),
    "ra":  (13,3),
    "ri":  (13,4),
    # Swati (14)
    "ru":  (14,1),
    "re":  (14,2),
    "ro":  (14,3),
    "ta":  (14,4),
    # Vishakha (15)
    "ti":  (15,1),
    "tu":  (15,2),
    "te":  (15,3),
    "to":  (15,4),
    # Anuradha (16)
    "na":  (16,1),
    "ni":  (16,2),
    "nu":  (16,3),
    "ne":  (16,4),
    # Jyeshtha (17)
    "no":  (17,1),
    "ya":  (17,2),
    "yi":  (17,3),
    "yu":  (17,4),
    # Moola (18)
    "ye":  (18,1),
    "yo":  (18,2),
    "bha": (18,3),
    "bhi": (18,4),
    # Purva Ashadha (19)
    "bhu": (19,1),
    "dha": (19,2),
    "pha": (19,3),
    "dha": (19,4),
    # Uttara Ashadha (20)
    "bhe": (20,1),
    "bho": (20,2),
    "ja":  (20,3),
    "ji":  (20,4),
    # Shravana (21)
    "ju":  (21,1),
    "je":  (21,2),
    "jo":  (21,3),
    "sha": (21,4),
    # Dhanishtha (22)
    "ga":  (22,1),
    "gi":  (22,2),
    "gu":  (22,3),
    "ge":  (22,4),
    # Shatabhisha (23)
    "go":  (23,1),
    "sa":  (23,2),
    "si":  (23,3),
    "su":  (23,4),
    # Purva Bhadrapada (24)
    "se":  (24,1),
    "so":  (24,2),
    "da":  (24,3),
    "di":  (24,4),
    # Uttara Bhadrapada (25)
    "du":  (25,1),
    "tha": (25,2),
    "jha": (25,3),
    "na":  (25,4),
    # Revati (26)
    "de":  (26,1),
    "do":  (26,2),
    "cha": (26,3),
    "chi": (26,4),
}

# Comprehensive first-letter fallback (when 2-char match fails)
_LETTER_TO_NAK: dict[str, int] = {
    "a":1,"b":3,"c":2,"d":7,"e":2,"f":10,"g":22,"h":5,
    "i":2,"j":20,"k":4,"l":0,"m":9,"n":12,"o":3,"p":10,
    "q":23,"r":13,"s":21,"t":10,"u":2,"v":3,"w":14,"x":23,
    "y":17,"z":23,
}


def name_to_nakshatra(name: str) -> tuple[int, int, str]:
    """
    Derive nakshatra from name phonetics.
    Returns (nak_idx, pada, method_note).
    Tries 3-char, 2-char, then 1-char matching.
    """
    clean = name.strip().lower().replace(" ","").replace(".","").replace("&","")
    # Try 3-char prefix
    for length in (3, 2):
        prefix = clean[:length]
        if prefix in PHONETIC_MAP:
            idx, pada = PHONETIC_MAP[prefix]
            return idx, pada, f"Phonetic match on '{prefix}'"
    # 1-char fallback
    first = clean[0] if clean else "n"
    idx = _LETTER_TO_NAK.get(first, 0)
    return idx, 1, f"First-letter fallback on '{first}'"


# ─────────────────────────────────────────────────────────────────────────────
# 3.  LISTING DATE → NAKSHATRA
# ─────────────────────────────────────────────────────────────────────────────
# Well-known listing dates for common Indian indices and stocks
KNOWN_LISTING_DATES: dict[str, str] = {
    # Indices (use inception/base date)
    "NIFTY":     "1996-07-04",
    "NIFTY50":   "1996-07-04",
    "BANKNIFTY": "2000-09-15",
    "NIFTYBANK": "2000-09-15",
    "SENSEX":    "1986-01-02",
    "NIFTYMIDCAP": "2004-08-11",
    "FINNIFTY":  "2021-01-11",
    # Large caps
    "RELIANCE":  "1977-11-08",
    "TCS":       "2004-08-25",
    "INFY":      "1993-02-19",
    "INFOSYS":   "1993-02-19",
    "HDFCBANK":  "1995-05-19",
    "HDFC":      "1995-05-19",
    "ICICIBANK": "1998-09-17",
    "KOTAKBANK": "1985-11-21",
    "SBIN":      "1955-10-02",
    "WIPRO":     "1946-12-29",
    "BHARTIARTL":"2002-02-18",
    "ITC":       "1954-07-29",
    "HINDUNILVR":"1956-07-05",
    "LT":        "1950-12-07",
    "MARUTI":    "2003-06-09",
    "BAJFINANCE":"1987-04-09",
    "ASIANPAINT":"1982-05-07",
    "SUNPHARMA": "1994-11-08",
    "TITAN":     "1984-07-13",
    "ULTRACEMCO":"2004-07-30",
    "TECHM":     "2006-08-28",
    "AXISBANK":  "1998-11-03",
    "POWERGRID": "2007-10-05",
    "NTPC":      "2004-11-05",
    "ONGC":      "1995-02-13",
    "COALINDIA": "2010-11-04",
    "ADANIPORTS":"2008-11-27",
    "JSWSTEEL":  "2002-03-27",
    "TATASTEEL": "1907-08-26",
    "HINDALCO":  "1958-12-15",
    "DRREDDY":   "1986-03-04",
    "CIPLA":     "1935-08-17",
    "DIVISLAB":  "2003-03-04",
    "APOLLOHOSP":"1979-08-07",
    "BAJAJFINSV":"2008-05-26",
    "HCLTECH":   "1999-11-12",
    "NESTLEIND": "1959-07-15",
    "BRITANNIA": "1897-05-07",
    "HEROMOTOCO":"2001-07-02",
    "EICHERMOT": "1982-03-29",
    "INDUSINDBK":"1994-01-26",
    "GRASIM":    "1947-08-11",
    "TATACONSUM":"1998-10-22",
    "BPCL":      "1977-08-24",
    "PIDILITIND":"1969-09-12",
    "LTIM":      "2022-11-10",
    "TATAMOTORS":"2002-07-17",
    "M&M":       "1945-10-02",
}


def listing_date_to_nakshatra(date_str: str, ephe_path: Optional[str] = None) -> tuple[int, int, str]:
    """
    Compute Moon's nakshatra on listing date at market open (09:15 IST).
    Returns (nak_idx, pada, note).
    Falls back to Sun nakshatra if swisseph unavailable.
    """
    try:
        import swisseph as swe
        import os
        if ephe_path is None:
            ephe_path = os.path.join(os.getcwd(), "ephe")
        swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        # Parse date and convert IST 09:15 → UTC
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt_utc = dt.replace(hour=3, minute=45)  # 09:15 IST = 03:45 UTC
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                        dt_utc.hour + dt_utc.minute/60)
        moon = swe.calc_ut(jd, swe.MOON, FLAGS)
        moon_lon = moon[0][0] % 360
        idx = lon_to_nak_idx(moon_lon)
        pada = lon_to_pada(moon_lon)
        return idx, pada, f"Moon nakshatra on listing date {date_str}"
    except Exception as e:
        # Try Sun as fallback
        try:
            sun = swe.calc_ut(jd, swe.SUN, FLAGS)
            sun_lon = sun[0][0] % 360
            idx = lon_to_nak_idx(sun_lon)
            pada = lon_to_pada(sun_lon)
            return idx, pada, f"Sun nakshatra on listing date {date_str} (Moon unavailable)"
        except:
            pass
        return 0, 1, f"Fallback — swisseph error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# 4.  CMP FETCH VIA YFINANCE
# ─────────────────────────────────────────────────────────────────────────────
# Mapping of common Indian symbols to yfinance tickers
_YF_SYMBOL_MAP: dict[str, str] = {
    "NIFTY": "^NSEI", "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK", "NIFTYBANK": "^NSEBANK",
    "SENSEX": "^BSESN",
    "NIFTYMIDCAP": "^NSEMDCP50",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
}


def fetch_cmp(symbol: str) -> Optional[float]:
    """
    Fetch current market price via yfinance.
    Handles NSE indices, NSE stocks (.NS suffix), BSE stocks (.BO suffix).
    Returns None if unavailable.
    """
    try:
        import yfinance as yf
        sym_upper = symbol.upper().replace(" ", "").replace("&", "AND")

        # Direct mapping first
        yf_sym = _YF_SYMBOL_MAP.get(sym_upper)
        if yf_sym is None:
            # Already has suffix
            if "." in sym_upper:
                yf_sym = sym_upper
            else:
                yf_sym = sym_upper + ".NS"  # default NSE

        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period="2d")
        if hist.empty:
            # Try BSE
            ticker = yf.Ticker(sym_upper + ".BO")
            hist = ticker.history(period="2d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 5.  COMPLETE SBC 9×9 GRID
# ─────────────────────────────────────────────────────────────────────────────
SBC_GRID_CELLS: dict[tuple, tuple] = {}

# Corners
SBC_GRID_CELLS[(0,0)] = ("corner", "अं\nAm")
SBC_GRID_CELLS[(0,8)] = ("corner", "अः\nAh")
SBC_GRID_CELLS[(8,0)] = ("corner", "आ\nAaa")
SBC_GRID_CELLS[(8,8)] = ("corner", "ई\nEee")

# Top row (North) — col 1-7
for _c, _n in enumerate(["Shravana","Uttara Ashadha","Purva Ashadha","Moola",
                          "Jyeshtha","Anuradha","Vishakha"], 1):
    SBC_GRID_CELLS[(0,_c)] = ("nak", _n)

# Right col (East) — row 1-7
for _r, _n in enumerate(["Swati","Chitra","Hasta","Uttara Phalguni",
                          "Purva Phalguni","Magha","Ashlesha"], 1):
    SBC_GRID_CELLS[(_r,8)] = ("nak", _n)

# Bottom row (South) — col 7→1 (East to West)
for _i, _n in enumerate(["Pushya","Punarvasu","Ardra","Mrigashira",
                          "Rohini","Krittika","Bharani"]):
    SBC_GRID_CELLS[(8, 7-_i)] = ("nak", _n)

# Left col (West) — row 7→2 (bottom to top)
for _i, _n in enumerate(["Revati","Uttara Bhadrapada","Purva Bhadrapada",
                          "Shatabhisha","Dhanishtha","Abhijit"]):
    SBC_GRID_CELLS[(7-_i, 0)] = ("nak", _n)
SBC_GRID_CELLS[(1,0)] = ("nak", "Ashwini")

# Second ring — Sanskrit consonant groups (24 cells)
for _c, _v in enumerate(["क Ka","ख Kha","ग Ga","घ Gha","ङ Ṅa","च Ca","छ Cha"], 1):
    SBC_GRID_CELLS[(1,_c)] = ("vowel", _v)
for _r, _v in enumerate(["ज Ja","झ Jha","ट Ṭa","ठ Ṭha","ड Ḍa"], 2):
    SBC_GRID_CELLS[(_r,7)] = ("vowel", _v)
for _i, _v in enumerate(["ढ Ḍha","ण Ṇa","त Ta","थ Tha","द Da","ध Dha","न Na"]):
    SBC_GRID_CELLS[(7, 7-_i)] = ("vowel", _v)
for _i, _v in enumerate(["प Pa","फ Pha","ब Ba","भ Bha","म Ma"]):
    SBC_GRID_CELLS[(6-_i, 1)] = ("vowel", _v)

# Third ring — 12 Rashis (16 cells)
for _c, _r in enumerate(["Sagittarius","Capricorn","Aquarius","Pisces","Aries"], 2):
    SBC_GRID_CELLS[(2,_c)] = ("rashi", _r)
for _r, _rashi in enumerate(["Taurus","Gemini","Cancer"], 3):
    SBC_GRID_CELLS[(_r,6)] = ("rashi", _rashi)
for _i, _r in enumerate(["Leo","Virgo","Libra","Scorpio","Sagittarius"]):
    SBC_GRID_CELLS[(6, 6-_i)] = ("rashi", _r)
for _i, _r in enumerate(["Capricorn","Aquarius","Pisces"]):
    SBC_GRID_CELLS[(5-_i, 2)] = ("rashi", _r)

# Inner ring — Tithis (5 groups) + Varas (7)
SBC_GRID_CELLS[(4,4)] = ("center", "SBC\nCENTRE")
SBC_GRID_CELLS[(3,3)] = ("tithi", "T1-6\nPratipada")
SBC_GRID_CELLS[(3,4)] = ("tithi", "T7-12\nSaptami")
SBC_GRID_CELLS[(3,5)] = ("tithi", "T13-18\nTrayodashi")
SBC_GRID_CELLS[(4,3)] = ("tithi", "T19-24\nNavami")
SBC_GRID_CELLS[(4,5)] = ("tithi", "T25-30\nPanchami")
SBC_GRID_CELLS[(5,3)] = ("vara", "☉ Sun")
SBC_GRID_CELLS[(5,4)] = ("vara", "☽ Mon")
SBC_GRID_CELLS[(5,5)] = ("vara", "♂ Tue")
SBC_GRID_CELLS[(2,3)] = ("vara", "☿ Wed")
SBC_GRID_CELLS[(2,4)] = ("vara", "♃ Thu")
SBC_GRID_CELLS[(2,5)] = ("vara", "♀ Fri")
SBC_GRID_CELLS[(2,2)] = ("vara", "♄ Sat")


# ─────────────────────────────────────────────────────────────────────────────
# 6.  VEDHA TABLE
# ─────────────────────────────────────────────────────────────────────────────
_VEDHA_RAW = {
    "Ashwini":           {"front":"Purva Phalguni",    "left":"Rohini",             "right":"Jyeshtha"},
    "Bharani":           {"front":"Magha",              "left":"Shravana",           "right":"Dhanishtha"},
    "Krittika":          {"front":"Shravana",           "left":"Vishakha",           "right":"Anuradha"},
    "Rohini":            {"front":"Magha",              "left":"Abhijit",            "right":"Purva Bhadrapada"},
    "Mrigashira":        {"front":"Shravana",           "left":"Vishakha",           "right":"Anuradha"},
    "Ardra":             {"front":"Magha",              "left":"Shravana",           "right":"Dhanishtha"},
    "Punarvasu":         {"front":"Uttara Ashadha",     "left":"Uttara Phalguni",    "right":"Uttara Bhadrapada"},
    "Pushya":            {"front":"Purva Ashadha",      "left":"Uttara Phalguni",    "right":"Uttara Ashadha"},
    "Ashlesha":          {"front":"Anuradha",           "left":"Magha",              "right":"Dhanishtha"},
    "Magha":             {"front":"Bharani",            "left":"Shravana",           "right":"Ashlesha"},
    "Purva Phalguni":    {"front":"Ashwini",            "left":"Abhijit",            "right":"Pushya"},
    "Uttara Phalguni":   {"front":"Revati",             "left":"Uttara Ashadha",     "right":"Punarvasu"},
    "Hasta":             {"front":"Uttara Bhadrapada",  "left":"Purva Ashadha",      "right":"Ardra"},
    "Chitra":            {"front":"Purva Bhadrapada",   "left":"Moola",              "right":"Mrigashira"},
    "Swati":             {"front":"Shatabhisha",        "left":"Jyeshtha",           "right":"Rohini"},
    "Vishakha":          {"front":"Dhanishtha",         "left":"Anuradha",           "right":"Krittika"},
    "Anuradha":          {"front":"Ashlesha",           "left":"Bharani",            "right":"Vishakha"},
    "Jyeshtha":          {"front":"Pushya",             "left":"Ashwini",            "right":"Swati"},
    "Moola":             {"front":"Punarvasu",          "left":"Revati",             "right":"Chitra"},
    "Purva Ashadha":     {"front":"Ardra",              "left":"Uttara Bhadrapada",  "right":"Hasta"},
    "Uttara Ashadha":    {"front":"Mrigashira",         "left":"Purva Bhadrapada",   "right":"Uttara Phalguni"},
    "Shravana":          {"front":"Krittika",           "left":"Dhanishtha",         "right":"Magha"},
    "Dhanishtha":        {"front":"Vishakha",           "left":"Ashlesha",           "right":"Shravana"},
    "Shatabhisha":       {"front":"Swati",              "left":"Pushya",             "right":"Abhijit"},
    "Purva Bhadrapada":  {"front":"Chitra",             "left":"Punarvasu",          "right":"Uttara Ashadha"},
    "Uttara Bhadrapada": {"front":"Hasta",              "left":"Ardra",              "right":"Purva Ashadha"},
    "Revati":            {"front":"Uttara Phalguni",    "left":"Mrigashira",         "right":"Moola"},
}

VEDHA_TABLE: dict[int, dict[str,int]] = {}
for _nn, _dd in _VEDHA_RAW.items():
    _si = nak_index(_nn)
    VEDHA_TABLE[_si] = {k: nak_index(v) for k,v in _dd.items()}


def get_vedha_directions(nak_idx: int) -> dict:
    if nak_idx in VEDHA_TABLE:
        return VEDHA_TABLE[nak_idx]
    return {"front":(nak_idx+7)%27,"left":(nak_idx+14)%27,"right":(nak_idx+21)%27}


# ─────────────────────────────────────────────────────────────────────────────
# 7.  ACTIVE DIRECTIONS  (corrected per classical texts)
# ─────────────────────────────────────────────────────────────────────────────
ALL_SIDES_PLANETS = {"Sun","Moon","Rahu","Ketu"}
RETRO_GRACE_DAYS  = {"Mars":4,"Mercury":3,"Jupiter":8,"Saturn":20,"Venus":5}
ATICHARI_SPEED    = {"Mercury":1.8,"Venus":1.2,"Mars":0.7,"Jupiter":0.15,"Saturn":0.10}


def get_active_directions(planet_name: str, speed: float,
                           days_since_direct: Optional[float]) -> list:
    base = planet_name.split()[0]
    if base in ALL_SIDES_PLANETS:
        return ["front","left","right"]
    if days_since_direct is not None and base in RETRO_GRACE_DAYS:
        if days_since_direct <= RETRO_GRACE_DAYS[base]:
            return ["left"]
    if speed < 0:
        return ["left"]   # Retrograde → Vaama (Left)
    if base in ATICHARI_SPEED and speed > ATICHARI_SPEED[base]:
        return ["right"]  # Atichari → Dakshina (Right)
    return ["front"]      # Normal direct → Agra (Front)


# ─────────────────────────────────────────────────────────────────────────────
# 8.  STRENGTH / DEBILITATION / COMBUSTION
# ─────────────────────────────────────────────────────────────────────────────
DEBILITATION = {
    "Sun":(190,220),"Moon":(220,250),"Mars":(100,130),
    "Mercury":(340,10),"Jupiter":(280,310),"Venus":(160,190),"Saturn":(10,40),
}


def is_debilitated(planet_name: str, lon: float) -> bool:
    base = planet_name.split()[0]
    if base not in DEBILITATION: return False
    lo, hi = DEBILITATION[base]
    ln = lon % 360
    return (ln >= lo or ln <= hi) if lo > hi else (lo <= ln <= hi)


def is_combust(planet_name: str, planet_lon: float, sun_lon: float) -> bool:
    base = planet_name.split()[0]
    if base in ("Sun","Rahu","Ketu"): return False
    diff = min(abs(planet_lon - sun_lon), 360 - abs(planet_lon - sun_lon))
    orbs = {"Moon":12,"Mars":17,"Mercury":14,"Jupiter":11,"Venus":10,"Saturn":15}
    return diff < orbs.get(base, 12)


def vedha_strength(planet_name: str, planet_lon: float, sun_lon: float,
                   moon_intra: float, mutual: bool) -> str:
    if mutual: return "strong"
    base = planet_name.split()[0]
    if base == "Moon" and (moon_intra < 8.0 or moon_intra > 22.0): return "weak"
    if is_combust(planet_name, planet_lon, sun_lon): return "weak"
    if is_debilitated(planet_name, planet_lon): return "weak"
    return "normal"


# ─────────────────────────────────────────────────────────────────────────────
# 9.  BENEFIC / MALEFIC
# ─────────────────────────────────────────────────────────────────────────────
NATURAL_BENEFICS = {"Moon","Mercury","Jupiter","Venus"}
NATURAL_MALEFICS = {"Sun","Mars","Saturn","Rahu","Ketu"}


def get_tithi(moon_lon: float, sun_lon: float) -> int:
    return int(((moon_lon - sun_lon) % 360) / 12) + 1


def moon_is_malefic_paksha(moon_lon: float, sun_lon: float) -> bool:
    t = get_tithi(moon_lon, sun_lon)
    return t >= 23 or t <= 5


def is_benefic(planet_name: str, moon_lon: float, sun_lon: float,
               planet_lon: float, all_lons: dict) -> bool:
    base = planet_name.split()[0]
    if base == "Moon":
        if moon_is_malefic_paksha(moon_lon, sun_lon): return False
        mp, mn = lon_to_pada(moon_lon), lon_to_nak_idx(moon_lon)
        for on, ol in all_lons.items():
            if on.split()[0] in NATURAL_MALEFICS:
                if lon_to_nak_idx(ol)==mn and lon_to_pada(ol)==mp: return False
        return True
    if base == "Mercury":
        mp, mn = lon_to_pada(planet_lon), lon_to_nak_idx(planet_lon)
        for on, ol in all_lons.items():
            if on.split()[0] in NATURAL_MALEFICS:
                if lon_to_nak_idx(ol)==mn and lon_to_pada(ol)==mp: return False
        return True
    return base in NATURAL_BENEFICS


# ─────────────────────────────────────────────────────────────────────────────
# 10.  NAKSHATRA COMMODITIES
# ─────────────────────────────────────────────────────────────────────────────
NAKSHATRA_COMMODITIES = {
    0:["rice","ghee","clothes","minerals"],
    1:["chillies","millets","wheat","rice","juar"],
    2:["rice","oats","metals","til","gems","diamonds","grams","oils","gold","silver"],
    3:["grains","woolen blankets","metals","liquids"],
    4:["yellow grain","resins","buildings","animals","gems"],
    5:["oils","salt","liquids","sandal","scents"],
    6:["cotton","threads","til"],
    7:["silver","gold","ghee","rice","sambhar salt","heeng","sarso","oil"],
    8:["gur","khand","sonth","masoor","wheat","chillies","rice"],
    9:["oil","til","ghee","moong","gram","gur","alsi"],
    10:["woolen clothes","blankets","wool","til","oil","silver"],
    11:["urad","moong","rice","salt"],
    12:["sandal","camphor"],
    13:["gold","gems","gur","urad","moong","animals"],
    14:["chillies","oil","heeng"],
    15:["rice","wheat","moong","masoor","moth"],
    16:["arhar","pulses","grains","rice","moth","gram"],
    17:["gur","clothes","camphor","heeng"],
    18:["cotton","liquid things","grains","salt"],
    19:["grains","ghee","fruits"],
    20:["animals","steel","brass","copper"],
    21:["sugar","bettlenuts","dry fruits"],
    22:["gold","silver","gems","pearls","diamonds"],
    23:["oil","wines"],
    24:["metals","grains","medicines"],
    25:["gur","sugar","khand","til","sarso","oils"],
    26:["pearl","gem","bettlenuts"],
}

SECTOR_COMMODITY_MAP = {
    "financial services":["gold","silver","metals"],
    "bank":["gold","silver","metals"],
    "it":["gems","diamonds"],"technology":["gems","diamonds"],
    "fmcg":["ghee","oil","grains","rice","wheat","sugar"],
    "consumer":["ghee","oil","grains","rice","wheat","sugar"],
    "pharma":["medicines","oils","sandal"],"healthcare":["medicines"],
    "energy":["oil","oils"],"oil":["oil","oils"],
    "metal":["metals","steel","brass","copper","gold","silver"],
    "mining":["metals","minerals","gems","diamonds"],
    "textile":["cotton","clothes","woolen","threads"],
    "auto":["metals","steel","brass","copper"],
    "realty":["buildings"],
    "agriculture":["grains","rice","wheat","grams","pulses"],
}


def get_sector_keywords(sector: str) -> list:
    sl = sector.lower()
    for k, v in SECTOR_COMMODITY_MAP.items():
        if k in sl: return v
    return []


def commodity_relevance(nak_idx: int, sector: str) -> tuple:
    kws = get_sector_keywords(sector)
    if not kws: return False, []
    comms = NAKSHATRA_COMMODITIES.get(nak_idx, [])
    m = [c for c in comms if any(k in c for k in kws)]
    return bool(m), m


# ─────────────────────────────────────────────────────────────────────────────
# 11.  PRICE LEVEL ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
# Classical SBC price-level method:
# 1. The stock nakshatra defines the "centre of gravity" price zone.
# 2. The 3 vedha nakshatras (front/left/right) define key S/R price bands.
# 3. We use the nakshatra's position in the 360° zodiac to derive
#    percentage offsets from CMP that map to classical grid lines.
# 4. Malefic vedha on a level = resistance. Benefic vedha = support.

def compute_price_levels(
    cmp: float,
    stock_nak_idx: int,
    front_idx: int,
    left_idx: int,
    right_idx: int,
    planet_results: list,
    total_raw: float,
) -> list[dict]:
    """
    Derive key SBC price levels from CMP using nakshatra geometry.

    The 27 nakshatras divide 360° into equal 13.33° spans.
    The angular distance between nakshatras translates to a price % move.
    Base unit: 1 nakshatra step ≈ 1/27 of annual range.
    Empirically calibrated to ~0.5–1.5% per nakshatra step for indices.

    Returns list of level dicts with keys:
        price, label, type (support/resistance/pivot), strength, planets_involved
    """
    if cmp <= 0:
        return []

    levels = []

    # Nakshatra angular positions (degrees) — used to compute relative distance
    nak_deg = 360 / 27  # 13.333°

    def nak_distance(a: int, b: int) -> float:
        """Signed shortest angular distance a→b in nakshatra units."""
        d = (b - a) % 27
        if d > 13: d -= 27
        return d

    # Base step: each nakshatra unit = ~0.618% of CMP (golden ratio calibration)
    # This is adjustable — for high-beta stocks use 1.0%, for indices 0.5%
    step_pct = 0.618 / 100

    def price_at_distance(dist_naks: float) -> float:
        return round(cmp * (1 + dist_naks * step_pct), 2)

    # Determine benefic/malefic pressure on each vedha direction from planets
    direction_pressure: dict[str, float] = {"front": 0.0, "left": 0.0, "right": 0.0}
    for pr in planet_results:
        for hit in pr.hits:
            if hit in ("front", "front_vedha"):
                direction_pressure["front"] += pr.raw_score
            elif hit in ("left", "left_vedha"):
                direction_pressure["left"] += pr.raw_score
            elif hit in ("right", "right_vedha"):
                direction_pressure["right"] += pr.raw_score

    def planets_on_direction(direction_nak_idx: int) -> list[str]:
        names = []
        for pr in planet_results:
            if pr.planet_nak_idx == direction_nak_idx:
                names.append(pr.planet)
            for hit in pr.hits:
                if hit in (direction_nak_idx,): pass
        for pr in planet_results:
            if pr.planet_nak_idx == direction_nak_idx and pr.hits:
                names.append(pr.planet)
        return list(dict.fromkeys(names))

    def planets_near_nak(target_nak: int) -> list[str]:
        return [pr.planet for pr in planet_results
                if pr.planet_nak_idx == target_nak]

    def level_type_from_pressure(pressure: float) -> str:
        if pressure > 5:   return "resistance"
        if pressure < -5:  return "support"
        return "pivot"

    # ── Stock nakshatra itself = current pivot / consolidation zone ───────
    levels.append({
        "price": cmp,
        "label": f"CMP — {NAKSHATRAS[stock_nak_idx]} (Stock Nak)",
        "type": "current",
        "strength": "pivot",
        "planets": planets_near_nak(stock_nak_idx),
        "note": "Current market price anchored to stock's natal nakshatra",
    })

    # ── Front Vedha level ─────────────────────────────────────────────────
    dist_front = nak_distance(stock_nak_idx, front_idx)
    price_front = price_at_distance(dist_front)
    p_front = direction_pressure["front"]
    planets_front = planets_near_nak(front_idx)
    # Planets transiting front nakshatra directly
    planets_hitting_front = [pr.planet for pr in planet_results
                              if pr.planet_nak_idx == front_idx or
                              any(h in ["front","front_vedha"] for h in pr.hits)]
    levels.append({
        "price": price_front,
        "label": f"Front Vedha — {NAKSHATRAS[front_idx] if front_idx < 27 else 'Abhijit'}",
        "type": level_type_from_pressure(p_front),
        "strength": "strong" if abs(p_front) > 15 else "normal",
        "planets": list(dict.fromkeys(planets_hitting_front)),
        "note": f"Agra Vedha line. Net pressure: {p_front:+.1f}",
    })

    # ── Left Vedha level ──────────────────────────────────────────────────
    dist_left = nak_distance(stock_nak_idx, left_idx)
    price_left = price_at_distance(dist_left)
    p_left = direction_pressure["left"]
    planets_hitting_left = [pr.planet for pr in planet_results
                             if pr.planet_nak_idx == left_idx or
                             any(h in ["left","left_vedha"] for h in pr.hits)]
    levels.append({
        "price": price_left,
        "label": f"Left Vedha — {NAKSHATRAS[left_idx] if left_idx < 27 else 'Abhijit'}",
        "type": level_type_from_pressure(p_left),
        "strength": "strong" if abs(p_left) > 15 else "normal",
        "planets": list(dict.fromkeys(planets_hitting_left)),
        "note": f"Vaama Vedha line. Net pressure: {p_left:+.1f}",
    })

    # ── Right Vedha level ─────────────────────────────────────────────────
    dist_right = nak_distance(stock_nak_idx, right_idx)
    price_right = price_at_distance(dist_right)
    p_right = direction_pressure["right"]
    planets_hitting_right = [pr.planet for pr in planet_results
                              if pr.planet_nak_idx == right_idx or
                              any(h in ["right","right_vedha"] for h in pr.hits)]
    levels.append({
        "price": price_right,
        "label": f"Right Vedha — {NAKSHATRAS[right_idx] if right_idx < 27 else 'Abhijit'}",
        "type": level_type_from_pressure(p_right),
        "strength": "strong" if abs(p_right) > 15 else "normal",
        "planets": list(dict.fromkeys(planets_hitting_right)),
        "note": f"Dakshina Vedha line. Net pressure: {p_right:+.1f}",
    })

    # ── Extended levels: ±1, ±2 nakshatra steps from CMP ────────────────
    for offset, tag in [(-2,"S2 — 2nd Support"),(-1,"S1 — 1st Support"),
                         (1,"R1 — 1st Resistance"),(2,"R2 — 2nd Resistance")]:
        nak_at = (stock_nak_idx + offset) % 27
        price_at = price_at_distance(offset)
        # Any planet transiting nearby?
        nearby = planets_near_nak(nak_at)
        ltype = "support" if offset < 0 else "resistance"
        levels.append({
            "price": price_at,
            "label": f"{tag} — {NAKSHATRAS[nak_at]}",
            "type": ltype,
            "strength": "strong" if nearby else "normal",
            "planets": nearby,
            "note": f"{offset:+d} nakshatra step from stock nak" +
                    (f". {', '.join(nearby)} transiting nearby" if nearby else ""),
        })

    # Sort by price ascending
    levels.sort(key=lambda x: x["price"])
    return levels


# ─────────────────────────────────────────────────────────────────────────────
# 12.  DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class PlanetState:
    name: str
    lon: float
    speed: float
    days_since_direct: Optional[float] = None


@dataclass
class PlanetVedhaResult:
    planet: str
    planet_lon: float
    planet_nak: str
    planet_nak_idx: int
    planet_pada: int
    active_directions: list
    hits: list
    is_benefic: bool
    strength: str
    is_debilitated: bool
    is_combust: bool
    mutual_vedha: bool
    commodity_relevant: bool
    matched_commodities: list
    raw_score: float
    notes: list


@dataclass
class SBCResult:
    symbol: str
    stock_nak: str
    stock_nak_idx: int
    stock_pada: Optional[int]
    nak_method: str               # how nakshatra was derived
    vedha_front_nak: str
    vedha_left_nak: str
    vedha_right_nak: str
    planet_results: list
    tithi: int
    paksha: str
    moon_malefic_paksha: bool
    raw_score: float
    sbc_score: int
    sbc_label: str
    sbc_color: str
    bullish_count: int
    bearish_count: int
    neutral_count: int
    stock_commodities: list
    sector: str
    sector_commodity_matches: list
    analysis_time: str
    cmp: Optional[float] = None
    price_levels: list = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 13.  MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
def analyse_sbc(
    symbol: str,
    planets: list,
    sector: str = "Unknown",
    stock_lon: Optional[float] = None,
    analysis_datetime: Optional[datetime] = None,
    nak_method: str = "phonetic",       # "phonetic" | "listing_date" | "manual"
    manual_nak: Optional[str] = None,
    listing_date: Optional[str] = None,
    ephe_path: Optional[str] = None,
    cmp: Optional[float] = None,
) -> SBCResult:

    if analysis_datetime is None:
        analysis_datetime = datetime.now(timezone.utc)

    # ── Derive stock nakshatra ────────────────────────────────────────────
    method_note = ""
    if stock_lon is not None:
        stock_nak_idx, stock_nak = lon_to_nak(stock_lon)
        stock_pada = lon_to_pada(stock_lon)
        method_note = "Exact longitude"
    elif nak_method == "manual" and manual_nak:
        stock_nak_idx = nak_index(manual_nak)
        stock_nak = NAKSHATRAS[stock_nak_idx] if stock_nak_idx < 27 else "Abhijit"
        stock_pada = None
        method_note = f"Manual: {manual_nak}"
    elif nak_method == "listing_date":
        # Try known dates first, then supplied date
        date_str = listing_date or KNOWN_LISTING_DATES.get(symbol.upper())
        if date_str:
            stock_nak_idx, stock_pada, method_note = listing_date_to_nakshatra(date_str, ephe_path)
            stock_nak = NAKSHATRAS[stock_nak_idx] if stock_nak_idx < 27 else "Abhijit"
        else:
            # Fall through to phonetic
            stock_nak_idx, stock_pada, method_note = name_to_nakshatra(symbol)
            stock_nak = NAKSHATRAS[stock_nak_idx] if stock_nak_idx < 27 else "Abhijit"
            method_note += " (no listing date known)"
    else:  # phonetic (default)
        stock_nak_idx, stock_pada, method_note = name_to_nakshatra(symbol)
        stock_nak = NAKSHATRAS[stock_nak_idx] if stock_nak_idx < 27 else "Abhijit"

    # ── Vedha directions ──────────────────────────────────────────────────
    dirs = get_vedha_directions(stock_nak_idx)
    front_idx = dirs["front"]
    left_idx  = dirs["left"]
    right_idx = dirs["right"]

    all_lons = {p.name: p.lon for p in planets}

    sun_state  = next((p for p in planets if p.name=="Sun"),  None)
    moon_state = next((p for p in planets if p.name=="Moon"), None)
    sun_lon  = sun_state.lon  if sun_state  else 0.0
    moon_lon = moon_state.lon if moon_state else 0.0
    sun_nak_idx = lon_to_nak_idx(sun_lon)

    tithi        = get_tithi(moon_lon, sun_lon)
    paksha       = "Shukla" if tithi <= 15 else "Krishna"
    moon_malefic = moon_is_malefic_paksha(moon_lon, sun_lon)
    moon_intra   = lon_intra_degree(moon_lon)

    # Sun's vedha targets (for weak-vedha detection)
    sun_dirs = get_active_directions("Sun", sun_state.speed if sun_state else 0.0, None)
    sun_hits: set = set()
    if sun_state:
        sv = get_vedha_directions(sun_nak_idx)
        for d in sun_dirs: sun_hits.add(sv.get(d,-1))
        sun_hits.add(sun_nak_idx)

    planet_nak_indices = {p.name: lon_to_nak_idx(p.lon) for p in planets}

    # Mutual vedha detection
    def mutual_vedha(pa: PlanetState, pb: PlanetState) -> bool:
        pa_d = get_active_directions(pa.name, pa.speed, pa.days_since_direct)
        pb_d = get_active_directions(pb.name, pb.speed, pb.days_since_direct)
        pa_v = get_vedha_directions(planet_nak_indices[pa.name])
        pb_v = get_vedha_directions(planet_nak_indices[pb.name])
        pa_t = {planet_nak_indices[pa.name]} | {pa_v[d] for d in pa_d if d in pa_v}
        pb_t = {planet_nak_indices[pb.name]} | {pb_v[d] for d in pb_d if d in pb_v}
        return (planet_nak_indices[pb.name] in pa_t) and (planet_nak_indices[pa.name] in pb_t)

    mutual_pairs: set = set()
    for i, pa in enumerate(planets):
        for pb in planets[i+1:]:
            if mutual_vedha(pa, pb):
                mutual_pairs.add(frozenset({pa.name, pb.name}))

    planet_results = []
    total_raw = 0.0

    for p in planets:
        ni = planet_nak_indices[p.name]
        _, nak_name = lon_to_nak(p.lon)
        pada = lon_to_pada(p.lon)
        active_dirs = get_active_directions(p.name, p.speed, p.days_since_direct)
        nv = get_vedha_directions(ni)
        activated = {ni} | {nv[d] for d in active_dirs if d in nv}

        hits = []
        if stock_nak_idx in activated: hits.append("direct")
        for d in active_dirs:
            t = nv.get(d)
            if t == stock_nak_idx and d not in hits: hits.append(d)
        if ni == front_idx and "front" in active_dirs and "front_vedha" not in hits:
            hits.append("front_vedha")
        if ni == left_idx  and "left"  in active_dirs and "left_vedha"  not in hits:
            hits.append("left_vedha")
        if ni == right_idx and "right" in active_dirs and "right_vedha" not in hits:
            hits.append("right_vedha")
        hits = list(dict.fromkeys(hits))

        sun_wk   = p.name != "Sun" and ni in sun_hits
        bene     = is_benefic(p.name, moon_lon, sun_lon, p.lon, all_lons)
        is_m     = any(p.name in pair for pair in mutual_pairs)
        strength = "weak" if sun_wk else vedha_strength(p.name, p.lon, sun_lon, moon_intra, is_m)
        cr, cm   = commodity_relevance(ni, sector)

        raw = 0.0
        notes = []
        if hits:
            base = 25.0 if strength=="strong" else 15.0 if strength=="normal" else 5.0
            if not bene:
                raw += base; nature_str = "Malefic (Bullish)"
            else:
                raw -= base; nature_str = "Benefic (Bearish)"
            if any(d in ["front","direct","front_vedha"] for d in hits):
                raw *= 1.5; notes.append("FRONT/DIRECT hit → 1.5×")
            if is_m:
                b2 = 12.0 if not bene else -12.0
                raw += b2; notes.append(f"Mutual Vedha → {b2:+.0f}")
            if cr:
                cb = 10.0 if not bene else -10.0
                raw += cb; notes.append(f"Commodity match → {cb:+.0f}")
            notes.append(f"Vedha hit — {nature_str}, {strength} → {raw:+.1f}")
        if sun_wk:
            notes.append("Sun Vedha-ing this planet — weakened")

        debit = is_debilitated(p.name, p.lon)
        comb  = is_combust(p.name, p.lon, sun_lon)
        total_raw += raw

        planet_results.append(PlanetVedhaResult(
            planet=p.name, planet_lon=p.lon, planet_nak=nak_name,
            planet_nak_idx=ni, planet_pada=pada, active_directions=active_dirs,
            hits=hits, is_benefic=bene, strength=strength,
            is_debilitated=debit, is_combust=comb, mutual_vedha=is_m,
            commodity_relevant=cr, matched_commodities=cm,
            raw_score=raw, notes=notes,
        ))

    bullish_count = sum(1 for r in planet_results if r.raw_score > 0)
    bearish_count = sum(1 for r in planet_results if r.raw_score < 0)
    neutral_count = sum(1 for r in planet_results if r.raw_score == 0)

    stock_comms = NAKSHATRA_COMMODITIES.get(stock_nak_idx, [])
    sec_kws     = get_sector_keywords(sector)
    sec_matches = [c for c in stock_comms if any(k in c for k in sec_kws)]

    sbc_score = max(5, min(95, int(50 + (total_raw / 90.0) * 45)))
    if   sbc_score >= 72: sbc_label,sbc_color = "Strongly Bullish","#00ff88"
    elif sbc_score >= 58: sbc_label,sbc_color = "Bullish","#10b981"
    elif sbc_score >= 42: sbc_label,sbc_color = "Neutral","#f59e0b"
    elif sbc_score >= 28: sbc_label,sbc_color = "Bearish","#ef4444"
    else:                 sbc_label,sbc_color = "Strongly Bearish","#991b1b"

    # Price levels
    price_levels = []
    if cmp and cmp > 0:
        price_levels = compute_price_levels(
            cmp, stock_nak_idx, front_idx, left_idx, right_idx,
            planet_results, total_raw
        )

    return SBCResult(
        symbol=symbol, stock_nak=stock_nak, stock_nak_idx=stock_nak_idx,
        stock_pada=stock_pada, nak_method=method_note,
        vedha_front_nak=NAKSHATRAS[front_idx] if front_idx<27 else "Abhijit",
        vedha_left_nak =NAKSHATRAS[left_idx]  if left_idx <27 else "Abhijit",
        vedha_right_nak=NAKSHATRAS[right_idx] if right_idx<27 else "Abhijit",
        planet_results=planet_results, tithi=tithi, paksha=paksha,
        moon_malefic_paksha=moon_malefic, raw_score=total_raw,
        sbc_score=sbc_score, sbc_label=sbc_label, sbc_color=sbc_color,
        bullish_count=bullish_count, bearish_count=bearish_count,
        neutral_count=neutral_count, stock_commodities=stock_comms,
        sector=sector, sector_commodity_matches=sec_matches,
        analysis_time=analysis_datetime.strftime("%Y-%m-%d %H:%M UTC"),
        cmp=cmp, price_levels=price_levels,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 14.  SWISSEPH FETCH
# ─────────────────────────────────────────────────────────────────────────────
def fetch_planet_states(dt: Optional[datetime]=None,
                         ephe_path: Optional[str]=None,
                         retro_history_days: int=30) -> list:
    try:
        import swisseph as swe
    except ImportError:
        raise ImportError("Install pyswisseph: pip install pyswisseph")
    import os
    if ephe_path is None:
        ephe_path = os.path.join(os.getcwd(), "ephe")
    swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
    if dt is None: dt = datetime.now(timezone.utc)
    jd = swe.julday(dt.year,dt.month,dt.day,dt.hour+dt.minute/60+dt.second/3600)
    planet_ids = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,
                  "Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,
                  "Venus":swe.VENUS,"Saturn":swe.SATURN}
    states = []
    for name, pid in planet_ids.items():
        res = swe.calc_ut(jd, pid, FLAGS)
        lon, speed = res[0][0]%360, res[0][3]
        dsd = None
        if name in RETRO_GRACE_DAYS and speed > 0:
            for bd in range(1, retro_history_days+1):
                rb = swe.calc_ut(jd-bd, pid, FLAGS)
                if rb[0][3] < 0: dsd=float(bd); break
        states.append(PlanetState(name=name, lon=lon, speed=speed, days_since_direct=dsd))
    rahu = swe.calc_ut(jd, swe.MEAN_NODE, FLAGS)
    rl   = rahu[0][0]%360
    states.append(PlanetState("Rahu", rl,       -0.053))
    states.append(PlanetState("Ketu", (rl+180)%360, -0.053))
    return states


# ─────────────────────────────────────────────────────────────────────────────
# 15.  CONVENIENCE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def analyse_symbol(
    symbol: str,
    sector: str = "Unknown",
    ephe_path: Optional[str] = None,
    dt: Optional[datetime] = None,
    stock_lon: Optional[float] = None,
    nak_method: str = "phonetic",
    manual_nak: Optional[str] = None,
    listing_date: Optional[str] = None,
    cmp: Optional[float] = None,
    fetch_live_cmp: bool = True,
) -> SBCResult:
    if dt is None: dt = datetime.now(timezone.utc)
    # Auto-fetch CMP if not supplied
    if cmp is None and fetch_live_cmp:
        cmp = fetch_cmp(symbol)
    planets = fetch_planet_states(dt=dt, ephe_path=ephe_path)
    return analyse_sbc(
        symbol=symbol, planets=planets, sector=sector,
        stock_lon=stock_lon, analysis_datetime=dt,
        nak_method=nak_method, manual_nak=manual_nak,
        listing_date=listing_date, ephe_path=ephe_path, cmp=cmp,
    )


# Self-test
if __name__ == "__main__":
    mock = [
        PlanetState("Sun",35.5,0.95), PlanetState("Moon",210.3,13.2),
        PlanetState("Mars",82.1,0.52), PlanetState("Mercury",38.2,1.85),
        PlanetState("Jupiter",55.7,-0.08), PlanetState("Venus",22.0,1.10),
        PlanetState("Saturn",330.1,-0.03), PlanetState("Rahu",15.8,-0.053),
        PlanetState("Ketu",195.8,-0.053),
    ]
    r = analyse_sbc("NIFTY", mock, "Financial Services",
                    cmp=23907.15,
                    analysis_datetime=datetime(2026,5,28,9,15,tzinfo=timezone.utc))
    print(f"NIFTY | Nak: {r.stock_nak} | Method: {r.nak_method}")
    print(f"Score: {r.sbc_score}/100 | Signal: {r.sbc_label}")
    print(f"\nPrice Levels (CMP={r.cmp}):")
    for lv in r.price_levels:
        tag = "🔴" if lv["type"]=="resistance" else "🟢" if lv["type"]=="support" else "⚪"
        pstr = f" [{', '.join(lv['planets'])}]" if lv['planets'] else ""
        print(f"  {tag} {lv['price']:>10,.2f}  {lv['label']}{pstr}")
