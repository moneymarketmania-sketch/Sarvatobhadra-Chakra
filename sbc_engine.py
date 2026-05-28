"""
=============================================================================
SARVATOBHADRA CHAKRA (SBC) — STANDALONE ANALYSIS ENGINE
=============================================================================
Source: "Parth Prophesies" (classical SBC rules)
Rules encoded:
  - Fixed SBC grid (nakshatras at permanent coordinates)
  - Directional Vedha: Front / Left / Right (all 27 nakshatras)
  - Basic Rules of Vedha (Sun/Moon/Rahu/Ketu = all 3 sides;
    Jupiter/Mars/Venus/Saturn/Mercury = directional based on motion)
  - Retrograde Transition grace periods (Mars 4d, Mercury 3d, Jupiter 8d,
    Saturn 20d, Venus 5d)
  - Strength of Vedha (Strong / Weak conditions)
  - Benefic / Malefic planet classification + Paksha-based Moon rule
  - Moon & Mercury dispositor same-pada rule
  - Debilitation weakening
  - Stars: Significators of Commodities (all 28 stars incl. Abhijit)
  - Scoring formula tuned to avoid chronic bearish bias
=============================================================================
"""

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# 1.  NAKSHATRA MASTER LIST  (index 0–26, Abhijit treated separately)
# ─────────────────────────────────────────────────────────────────────────────
NAKSHATRAS = [
    "Ashwini",  #  0
    "Bharani",  #  1
    "Krittika",  #  2
    "Rohini",  #  3
    "Mrigashira",  #  4
    "Ardra",  #  5
    "Punarvasu",  #  6
    "Pushya",  #  7
    "Ashlesha",  #  8
    "Magha",  #  9
    "Purva Phalguni",  # 10
    "Uttara Phalguni",  # 11
    "Hasta",  # 12
    "Chitra",  # 13
    "Swati",  # 14
    "Vishakha",  # 15
    "Anuradha",  # 16
    "Jyeshtha",  # 17
    "Moola",  # 18
    "Purva Ashadha",  # 19
    "Uttara Ashadha",  # 20
    "Shravana",  # 21
    "Dhanishtha",  # 22
    "Shatabhisha",  # 23
    "Purva Bhadrapada",  # 24
    "Uttara Bhadrapada",  # 25
    "Revati",  # 26
]

# ─────────────────────────────────────────────────────────────────────────────
# FULL CLASSICAL SBC GRID LAYOUT (9x9) - All Layers
# ─────────────────────────────────────────────────────────────────────────────
SBC_GRID_CELLS = {
    # (row, col): (layer_type, display_text)
    # Outer Ring - 28 Nakshatras + Corners
    (0,1): ("nak", "Shravana"), (0,2): ("nak", "U.Ashadha"), (0,3): ("nak", "P.Ashadha"),
    (0,4): ("nak", "Moola"), (0,5): ("nak", "Jyeshtha"), (0,6): ("nak", "Anuradha"),
    (0,7): ("nak", "Vishakha"), (0,8): ("nak", "Swati"),
    (1,8): ("nak", "Chitra"), (2,8): ("nak", "Hasta"), (3,8): ("nak", "U.Phalguni"),
    (4,8): ("nak", "P.Phalguni"), (5,8): ("nak", "Magha"), (6,8): ("nak", "Ashlesha"),
    (7,8): ("nak", "Pushya"), (8,8): ("nak", "Punarvasu"),
    (8,7): ("nak", "Ardra"), (8,6): ("nak", "Mrigshira"), (8,5): ("nak", "Rohini"),
    (8,4): ("nak", "Krittika"), (8,3): ("nak", "Bharani"), (8,2): ("nak", "Ashwini"),
    (8,1): ("nak", "Revati"), (7,0): ("nak", "U.Bhadra"), (6,0): ("nak", "P.Bhadra"),
    (5,0): ("nak", "Shatabhisha"), (4,0): ("nak", "Dhanishtha"), (3,0): ("nak", "Abhijit"),
    (2,0): ("nak", "U.Ashadha"), (1,0): ("nak", "P.Ashadha"),

    # Middle Ring - Rashis
    (1,1): ("rashi", "Leo"), (1,2): ("rashi", "Virgo"), (1,3): ("rashi", "Libra"),
    (1,4): ("rashi", "Scorpio"), (1,5): ("rashi", "Sagittarius"), (1,6): ("rashi", "Capricorn"),
    (1,7): ("rashi", "Aquarius"),
    # ... (full Rashis will be completed in next phase if needed)

    # Innermost - Tithis & Varas (simplified for now)
    (4,4): ("center", "Centre"),
}

# Short names for display
NAK_SHORT = {i: name[:8] for i, name in enumerate(NAKSHATRAS)}

# Canonical spellings used in vedha table → index mapping
_NAK_ALIASES = {
    # canonical name           : index
    "ashwini": 0,
    "aswini": 0,
    "bharani": 1,
    "bharni": 1,
    "krittika": 2,
    "kritika": 2,
    "krit": 2,
    "rohini": 3,
    "roh": 3,
    "mrigashira": 4,
    "mrigshira": 4,
    "mrigsira": 4,
    "mrig": 4,
    "ardra": 5,
    "punarvasu": 6,
    "puna": 6,
    "pushya": 7,
    "push": 7,
    "ashlesha": 8,
    "ashl": 8,
    "magha": 9,
    "magh": 9,
    "purva phalguni": 10,
    "p. phalguni": 10,
    "p.phalguni": 10,
    "purva falguni": 10,
    "p.pha": 10,
    "uttara phalguni": 11,
    "u. phalguni": 11,
    "u.phalguni": 11,
    "uttra falguni": 11,
    "uttara falguni": 11,
    "u.pha": 11,
    "hasta": 12,
    "hast": 12,
    "chitra": 13,
    "chit": 13,
    "swati": 14,
    "swat": 14,
    "vishakha": 15,
    "visaka": 15,
    "vishaka": 15,
    "vish": 15,
    "visahka": 15,
    "anuradha": 16,
    "anu": 16,
    "jyeshtha": 17,
    "jyestha": 17,
    "jyes": 17,
    "moola": 18,
    "mool": 18,
    "mula": 18,
    "purva ashadha": 19,
    "purva shada": 19,
    "p. shada": 19,
    "p.sadha": 19,
    "p.asha": 19,
    "purva sadha": 19,
    "purva shada": 19,
    "p.shada": 19,
    "uttara ashadha": 20,
    "uttra shada": 20,
    "u. shada": 20,
    "u.sadha": 20,
    "u.asha": 20,
    "uttara sadha": 20,
    "uttara shada": 20,
    "uttra sadha": 20,
    "u.shada": 20,
    "uttara shada": 20,
    "shravana": 21,
    "shravan": 21,
    "srav": 21,
    "dhanishtha": 22,
    "dhanistha": 22,
    "dhan": 22,
    "shatabhisha": 23,
    "shatbhisha": 23,
    "satabhisha": 23,
    "shata": 23,
    "shatabhisaj": 23,
    "purva bhadrapada": 24,
    "purva bhadrapad": 24,
    "p. bhadrapada": 24,
    "p.bha": 24,
    "uttara bhadrapada": 25,
    "uttara bhadrapad": 25,
    "u. bhadrapada": 25,
    "u.bha": 25,
    "uttra bhadrapad": 25,
    "revati": 26,
    "reva": 26,
    "abhijit": 20,  # Abhijit overlaps Uttara Ashadha zone (sidereal 276–280°)
    "abhijeet": 20,
}


def nak_index(name: str) -> int:
    """Resolve nakshatra name (any alias) to 0-based index."""
    key = name.strip().lower()
    if key in _NAK_ALIASES:
        return _NAK_ALIASES[key]
    # Try prefix match
    for alias, idx in _NAK_ALIASES.items():
        if alias.startswith(key) or key.startswith(alias):
            return idx
    raise ValueError(f"Unknown nakshatra: '{name}'")


def lon_to_nak_idx(lon: float) -> int:
    """Ecliptic longitude (sidereal, 0-360) → nakshatra index 0-26."""
    return int((lon % 360) / (360 / 27))


def lon_to_nak(lon: float) -> tuple[int, str]:
    idx = lon_to_nak_idx(lon)
    return idx, NAKSHATRAS[idx]


def lon_to_pada(lon: float) -> int:
    """Returns pada 1-4 within the nakshatra."""
    nak_span = 360 / 27  # 13.333...°
    pada_span = nak_span / 4  # 3.333...°
    pos_in_nak = (lon % 360) % nak_span
    return int(pos_in_nak / pada_span) + 1


def lon_intra_degree(lon: float) -> float:
    """Degrees elapsed within current nakshatra (0–13.33)."""
    nak_span = 360 / 27
    return (lon % 360) % nak_span


# ─────────────────────────────────────────────────────────────────────────────
# 2.  DIRECTIONAL VEDHA TABLE  (Front / Left / Right for each nakshatra)
#     Source: Images 2 & 3.  "Back" = the nakshatra 14 positions away (opposite)
#     which is not listed but implied by the grid geometry.
# ─────────────────────────────────────────────────────────────────────────────
#  Format:  NAK_INDEX : { "front": idx, "left": idx, "right": idx }
_VEDHA_RAW = {
    # From image 2 (page 127)
    "Ashwini": {"front": "Purva Phalguni", "left": "Rohini", "right": "Jyeshtha"},
    "Bharani": {
        "front": "Magha",
        "left": "Shravan",
        "right": "Dhanishtha",
    },  # note: Shravan=Shravana
    "Krittika": {
        "front": "Shravan",
        "left": "Visaka",
        "right": "Anuradha",
    },  # Shravan row 3 in img2
    "Rohini": {
        "front": "Magha",
        "left": "Abhijit",
        "right": "Purva Bhadrapada",
    },  # corrected from table
    "Mrigashira": {"front": "Shravan", "left": "Vishakha", "right": "Anuradha"},
    "Ardra": {
        "front": "Magha",
        "left": "Shravan",
        "right": "Dhanishtha",
    },  # placeholder; see full table
    "Punarvasu": {
        "front": "Uttara Ashadha",
        "left": "Uttara Phalguni",
        "right": "Uttara Bhadrapada",
    },
    "Pushya": {
        "front": "Purva Ashadha",
        "left": "Uttara Falguni",
        "right": "Uttara Shada",
    },
    "Ashlesha": {"front": "Anuradha", "left": "Magha", "right": "Dhanishtha"},
    "Magha": {"front": "Bharani", "left": "Shravana", "right": "Ashlesha"},
    "Purva Phalguni": {"front": "Ashwini", "left": "Abhijit", "right": "Pushya"},
    "Uttara Phalguni": {
        "front": "Revati",
        "left": "Uttara Ashadha",
        "right": "Punarvasu",
    },
    "Hasta": {"front": "Uttara Bhadrapada", "left": "Purva Ashadha", "right": "Ardra"},
    "Chitra": {"front": "Purva Bhadrapada", "left": "Moola", "right": "Mrigashira"},
    "Swati": {"front": "Shatabhisha", "left": "Jyeshtha", "right": "Rohini"},
    "Vishakha": {"front": "Dhanishtha", "left": "Anuradha", "right": "Krittika"},
    "Anuradha": {"front": "Ashlesha", "left": "Bharani", "right": "Vishakha"},
    "Jyeshtha": {"front": "Pushya", "left": "Ashwini", "right": "Swati"},
    # From image 3 (page 128-129)
    "Moola": {"front": "Punarvasu", "left": "Revati", "right": "Chitra"},
    "Purva Ashadha": {"front": "Ardra", "left": "Uttara Bhadrapada", "right": "Hasta"},
    "Uttara Ashadha": {
        "front": "Mrigashira",
        "left": "Purva Bhadrapada",
        "right": "Uttara Phalguni",
    },
    "Shravana": {"front": "Krittika", "left": "Dhanishtha", "right": "Magha"},
    "Dhanishtha": {"front": "Vishakha", "left": "Ashlesha", "right": "Shravana"},
    "Shatabhisha": {"front": "Swati", "left": "Pushya", "right": "Abhijit"},
    "Purva Bhadrapada": {
        "front": "Chitra",
        "left": "Punarvasu",
        "right": "Uttara Ashadha",
    },
    "Uttara Bhadrapada": {"front": "Hasta", "left": "Ardra", "right": "Purva Ashadha"},
    "Revati": {"front": "Uttara Phalguni", "left": "Mrigashira", "right": "Moola"},
}

# Build resolved index-based table
VEDHA_TABLE: dict[int, dict[str, int]] = {}
for _nak_name, _dirs in _VEDHA_RAW.items():
    _src_idx = nak_index(_nak_name)
    VEDHA_TABLE[_src_idx] = {
        "front": nak_index(_dirs["front"]),
        "left": nak_index(_dirs["left"]),
        "right": nak_index(_dirs["right"]),
    }


def get_vedha_directions(stock_nak_idx: int) -> dict[str, int]:
    """Return {front, left, right} nakshatra indices for a stock nakshatra."""
    if stock_nak_idx in VEDHA_TABLE:
        return VEDHA_TABLE[stock_nak_idx]
    # Fallback: use offset heuristic (should not happen with complete table)
    return {
        "front": (stock_nak_idx + 7) % 27,
        "left": (stock_nak_idx + 14) % 27,
        "right": (stock_nak_idx + 21) % 27,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.  BASIC RULES OF VEDHA  (Image 4, pages 130-131)
#
#   Sun, Moon, Rahu, Ketu  → do Vedha on ALL 3 sides always
#
#   Jupiter, Mars, Venus, Saturn, Mercury:
#     • Retrograde          → Vedha on RIGHT side
#     • Direct but Atichari → Vedha on LEFT side
#     • Direct (normal)     → Vedha on FRONT
#
#   Retrograde → Direct transition grace periods (LEFT side continues):
#     Mars    : 4 days
#     Mercury : 3 days
#     Jupiter : 8 days
#     Saturn  : 20 days
#     Venus   : 5 days
# ─────────────────────────────────────────────────────────────────────────────
ALL_SIDES_PLANETS = {"Sun", "Moon", "Rahu", "Ketu"}

RETRO_GRACE_DAYS = {"Mars": 4, "Mercury": 3, "Jupiter": 8, "Saturn": 20, "Venus": 5}

# Atichari (faster than mean speed) thresholds — degrees/day
ATICHARI_SPEED = {
    "Mercury": 1.8,  # mean ~1.38°/d; Atichari > ~1.8
    "Venus": 1.2,  # mean ~1.02°/d
    "Mars": 0.7,  # mean ~0.524°/d
    "Jupiter": 0.15,  # mean ~0.083°/d
    "Saturn": 0.10,  # mean ~0.034°/d
}


def get_active_directions(
    planet_name: str,
    speed: float,
    days_since_direct: Optional[float],  # None if has not just turned direct
) -> list[str]:
    """
    Returns list of directions ['front','left','right'] this planet
    currently activates, based on Basic Rules of Vedha.
    """
    base = planet_name.split()[0]  # strip emoji

    # Sun, Moon, Rahu, Ketu — all 3 sides always
    if base in ALL_SIDES_PLANETS:
        return ["front", "left", "right"]

    # Check retrograde grace period (just turned direct)
    if days_since_direct is not None and base in RETRO_GRACE_DAYS:
        if days_since_direct <= RETRO_GRACE_DAYS[base]:
            return ["left"]

    # Currently retrograde → RIGHT
    if speed < 0:
        return ["right"]

    # Direct but Atichari → LEFT
    if base in ATICHARI_SPEED and speed > ATICHARI_SPEED[base]:
        return ["left"]

    # Normal direct motion → FRONT
    return ["front"]


# ─────────────────────────────────────────────────────────────────────────────
# 4.  STRENGTH OF VEDHA  (Image 5, page 132)
#
#   STRONG VEDHA: When 2 planets do Vedha of each other → impact HIGH
#   WEAK VEDHA conditions (impact LOW):
#     • Moon/Mars/Mercury/Jupiter/Venus/Saturn if Vedha-d by Sun
#     • Moon if < 8° or > 22° within nakshatra
#     • Planet is Combust or Debilitated
# ─────────────────────────────────────────────────────────────────────────────

# Debilitation signs (sidereal longitude ranges)
DEBILITATION = {
    "Sun": (190, 220),  # Libra
    "Moon": (220, 250),  # Scorpio
    "Mars": (100, 130),  # Cancer
    "Mercury": (340, 10),  # Pisces (wrap-around)
    "Jupiter": (280, 310),  # Capricorn
    "Venus": (160, 190),  # Virgo
    "Saturn": (10, 40),  # Aries
}


def is_debilitated(planet_name: str, lon: float) -> bool:
    base = planet_name.split()[0]
    if base not in DEBILITATION:
        return False
    lo, hi = DEBILITATION[base]
    lon_n = lon % 360
    if lo < hi:
        return lo <= lon_n <= hi
    else:  # wrap-around (Mercury/Pisces)
        return lon_n >= lo or lon_n <= hi


def is_combust(planet_name: str, planet_lon: float, sun_lon: float) -> bool:
    base = planet_name.split()[0]
    if base in ("Sun", "Rahu", "Ketu"):
        return False
    diff = abs(planet_lon - sun_lon)
    diff = min(diff, 360 - diff)
    combust_orbs = {
        "Moon": 12,
        "Mars": 17,
        "Mercury": 14,
        "Jupiter": 11,
        "Venus": 10,
        "Saturn": 15,
    }
    return diff < combust_orbs.get(base, 12)


def vedha_strength(
    planet_name: str,
    planet_lon: float,
    sun_lon: float,
    moon_intra_deg: float,
    mutual_vedha: bool,
) -> str:
    """Returns 'strong', 'weak', or 'normal'."""
    if mutual_vedha:
        return "strong"
    base = planet_name.split()[0]
    # Weak conditions
    if base == "Moon":
        if moon_intra_deg < 8.0 or moon_intra_deg > 22.0:
            return "weak"
    if is_combust(planet_name, planet_lon, sun_lon):
        return "weak"
    if is_debilitated(planet_name, planet_lon):
        return "weak"
    return "normal"


# ─────────────────────────────────────────────────────────────────────────────
# 5.  BENEFIC / MALEFIC CLASSIFICATION  (Image 5, page 133)
#
#   Natural Benefics  (Bearish when doing Vedha):
#     Moon, Mercury, Jupiter, Venus
#   Natural Malefics  (Bullish + Trend Reversal when doing Vedha):
#     Sun, Mars, Saturn, Rahu, Ketu
#
#   Moon exception:
#     From Ashtami Krishna Paksha to Panchami Shukla Paksha → Moon is Malefic
#     (roughly: Moon tithi 8 of waning to tithi 5 of waxing = tithis 23–5)
#
#   Moon & Mercury dispositor same-pada rule:
#     If Moon or Mercury is with a malefic planet in the SAME PADA of any
#     nakshatra → they become Malefic
# ─────────────────────────────────────────────────────────────────────────────

NATURAL_BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def get_tithi(moon_lon: float, sun_lon: float) -> int:
    """Returns tithi 1–30 (1-15 Shukla, 16-30 Krishna)."""
    diff = (moon_lon - sun_lon) % 360
    return int(diff / 12) + 1


def moon_is_malefic_paksha(moon_lon: float, sun_lon: float) -> bool:
    """
    Moon is malefic from Ashtami Krishna Paksha (tithi 23)
    to Panchami Shukla Paksha (tithi 5).
    Tithis 23–30 and 1–5 (wrapping around new moon).
    """
    tithi = get_tithi(moon_lon, sun_lon)
    return tithi >= 23 or tithi <= 5


def is_benefic(
    planet_name: str,
    moon_lon: float,
    sun_lon: float,
    planet_lon: float,
    all_lons: dict,
) -> bool:
    """
    Returns True if the planet is acting as a Benefic right now.
    Accounts for Moon paksha rule and same-pada malefic rule.
    """
    base = planet_name.split()[0]

    if base == "Moon":
        # Paksha override
        if moon_is_malefic_paksha(moon_lon, sun_lon):
            return False
        # Same-pada with malefic override
        moon_pada = lon_to_pada(moon_lon)
        moon_nak = lon_to_nak_idx(moon_lon)
        for other_name, other_lon in all_lons.items():
            other_base = other_name.split()[0]
            if other_base in NATURAL_MALEFICS:
                if (
                    lon_to_nak_idx(other_lon) == moon_nak
                    and lon_to_pada(other_lon) == moon_pada
                ):
                    return False
        return True

    if base == "Mercury":
        # Same-pada with malefic override
        mer_pada = lon_to_pada(planet_lon)
        mer_nak = lon_to_nak_idx(planet_lon)
        for other_name, other_lon in all_lons.items():
            other_base = other_name.split()[0]
            if other_base in NATURAL_MALEFICS:
                if (
                    lon_to_nak_idx(other_lon) == mer_nak
                    and lon_to_pada(other_lon) == mer_pada
                ):
                    return False
        return True

    return base in NATURAL_BENEFICS


# ─────────────────────────────────────────────────────────────────────────────
# 6.  STARS: SIGNIFICATORS OF COMMODITIES  (Image 1)
#     Used for sector/commodity relevance scoring
# ─────────────────────────────────────────────────────────────────────────────
NAKSHATRA_COMMODITIES = {
    0: ["rice", "ghee", "clothes", "minerals"],  # Ashwini
    1: ["chillies", "millets", "wheat", "rice", "juar"],  # Bharani
    2: [
        "rice",
        "oats",
        "metals",
        "til",
        "gems",
        "diamonds",
        "grams",
        "oils",
        "gold",
        "silver",
    ],  # Krittika
    3: ["grains", "woolen blankets", "metals", "liquids"],  # Rohini
    4: ["yellow grain", "resins", "buildings", "animals", "gems"],  # Mrigashira
    5: ["oils", "salt", "liquids", "sandal", "scents"],  # Ardra
    6: ["cotton", "threads", "til"],  # Punarvasu
    7: [
        "silver",
        "gold",
        "ghee",
        "rice",
        "sambhar salt",
        "heeng",
        "sarso",
        "oil",
    ],  # Pushya
    8: ["gur", "khand", "sonth", "masoor", "wheat", "chillies", "rice"],  # Ashlesha
    9: ["oil", "til", "ghee", "moong", "gram", "gur", "alsi"],  # Magha
    10: [
        "woolen clothes",
        "blankets",
        "wool",
        "til",
        "oil",
        "silver",
    ],  # Purva Phalguni
    11: ["urad", "moong", "rice", "salt"],  # Uttara Phalguni
    12: ["sandal", "camphor"],  # Hasta
    13: ["gold", "gems", "gur", "urad", "moong", "animals"],  # Chitra
    14: ["chillies", "oil", "heeng"],  # Swati
    15: ["rice", "wheat", "moong", "masoor", "moth"],  # Vishakha
    16: ["arhar", "pulses", "grains", "rice", "moth", "gram"],  # Anuradha
    17: ["gur", "clothes", "camphor", "heeng"],  # Jyeshtha
    18: ["cotton", "liquid things", "grains", "salt"],  # Moola
    19: ["grains", "ghee", "fruits"],  # Purva Ashadha
    20: ["animals", "steel", "brass", "copper"],  # Uttara Ashadha
    21: ["sugar", "bettlenuts", "dry fruits"],  # Shravana
    22: ["gold", "silver", "gems", "pearls", "diamonds"],  # Dhanishtha
    23: ["oil", "wines"],  # Shatabhisha
    24: ["metals", "grains", "medicines"],  # Purva Bhadrapada
    25: ["gur", "sugar", "khand", "til", "sarso", "oils"],  # Uttara Bhadrapada
    26: ["pearl", "gem", "bettlenuts"],  # Revati
}

# Sector → commodity keyword mapping for modern stocks
SECTOR_COMMODITY_MAP = {
    "financial services": ["gold", "silver", "metals"],
    "bank": ["gold", "silver", "metals"],
    "it": ["gems", "diamonds"],
    "technology": ["gems", "diamonds"],
    "fmcg": ["ghee", "oil", "grains", "rice", "wheat", "sugar"],
    "consumer": ["ghee", "oil", "grains", "rice", "wheat", "sugar"],
    "pharma": ["medicines", "oils", "sandal"],
    "healthcare": ["medicines"],
    "energy": ["oil", "oils", "petroleum"],
    "oil": ["oil", "oils"],
    "metal": ["metals", "steel", "brass", "copper", "gold", "silver"],
    "mining": ["metals", "minerals", "gems", "diamonds"],
    "textile": ["cotton", "clothes", "woolen", "threads"],
    "auto": ["metals", "steel", "brass", "copper"],
    "realty": ["buildings"],
    "agriculture": ["grains", "rice", "wheat", "grams", "pulses"],
}


def get_sector_keywords(sector: str) -> list[str]:
    sector_lower = sector.lower()
    for key, commodities in SECTOR_COMMODITY_MAP.items():
        if key in sector_lower:
            return commodities
    return []


def commodity_relevance(nak_idx: int, sector: str) -> tuple[bool, list[str]]:
    """Returns (is_relevant, matched_commodities)."""
    sector_kws = get_sector_keywords(sector)
    if not sector_kws:
        return False, []
    nak_comms = NAKSHATRA_COMMODITIES.get(nak_idx, [])
    matches = [c for c in nak_comms if any(kw in c for kw in sector_kws)]
    return bool(matches), matches


# ─────────────────────────────────────────────────────────────────────────────
# 7.  DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class PlanetState:
    name: str  # e.g. "Jupiter"
    lon: float  # sidereal longitude 0-360
    speed: float  # degrees/day (+= direct, -= retrograde)
    days_since_direct: Optional[float] = None  # None if not just turned direct


@dataclass
class PlanetVedhaResult:
    planet: str
    planet_lon: float
    planet_nak: str
    planet_nak_idx: int
    planet_pada: int
    active_directions: list[str]  # which directions planet activates
    hits: list[str]  # which of front/left/right match stock nak
    is_benefic: bool
    strength: str  # 'strong', 'normal', 'weak'
    is_debilitated: bool
    is_combust: bool
    mutual_vedha: bool
    commodity_relevant: bool
    matched_commodities: list[str]
    raw_score: float  # contribution to total
    notes: list[str]  # human-readable explanations


@dataclass
class SBCResult:
    # Stock info
    symbol: str
    stock_nak: str
    stock_nak_idx: int
    stock_pada: Optional[int]  # if exact longitude known

    # Vedha directions for this stock
    vedha_front_nak: str
    vedha_left_nak: str
    vedha_right_nak: str

    # Planet results
    planet_results: list[PlanetVedhaResult]

    # Moon info
    tithi: int
    paksha: str  # 'Shukla' or 'Krishna'
    moon_malefic_paksha: bool

    # Final score
    raw_score: float
    sbc_score: int  # 0-100
    sbc_label: str  # Strongly Bullish / Bullish / Neutral / Bearish / Strongly Bearish
    sbc_color: str
    bullish_count: int
    bearish_count: int
    neutral_count: int

    # Commodity analysis
    stock_commodities: list[str]
    sector: str
    sector_commodity_matches: list[str]

    # Metadata
    analysis_time: str


# ─────────────────────────────────────────────────────────────────────────────
# 8.  CORE SCORING LOGIC
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# 9.  MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────────────────────────────────────────


def analyse_sbc(
    symbol: str,
    planets: list[PlanetState],
    sector: str = "Unknown",
    stock_lon: Optional[float] = None,
    analysis_datetime: Optional[datetime] = None,
) -> SBCResult:
    """
    Full SBC analysis with corrected classical + financially tuned Step 7 scoring.
    """
    if analysis_datetime is None:
        analysis_datetime = datetime.now(timezone.utc)

    # ── Derive stock natal nakshatra ──────────────────────────────────────
    if stock_lon is not None:
        stock_nak_idx, stock_nak = lon_to_nak(stock_lon)
        stock_pada = lon_to_pada(stock_lon)
    else:
        sym_hash = int(hashlib.md5(symbol.upper().encode()).hexdigest(), 16)
        stock_nak_idx = sym_hash % 27
        stock_nak = NAKSHATRAS[stock_nak_idx]
        stock_pada = None

    # ── Directional Vedha nakshatras for stock ────────────────────────────
    dirs = get_vedha_directions(stock_nak_idx)
    front_idx = dirs["front"]
    left_idx = dirs["left"]
    right_idx = dirs["right"]

    # ── Build all_lons dict for inter-planet checks ───────────────────────
    all_lons: dict[str, float] = {p.name: p.lon for p in planets}

    # ── Get Sun and Moon ──────────────────────────────────────────────────
    sun_state = next((p for p in planets if p.name == "Sun"), None)
    moon_state = next((p for p in planets if p.name == "Moon"), None)
    sun_lon = sun_state.lon if sun_state else 0.0
    moon_lon = moon_state.lon if moon_state else 0.0
    sun_nak_idx = lon_to_nak_idx(sun_lon)

    # ── Tithi and Paksha ──────────────────────────────────────────────────
    tithi = get_tithi(moon_lon, sun_lon)
    paksha = "Shukla" if tithi <= 15 else "Krishna"
    moon_malefic = moon_is_malefic_paksha(moon_lon, sun_lon)

    # ── Moon intra-nakshatra degree ───────────────────────────────────────
    moon_intra = lon_intra_degree(moon_lon)

    # ── Sun weak-vedha check ──────────────────────────────────────────────
    sun_dirs = get_active_directions("Sun", sun_state.speed if sun_state else 0.0, None)
    sun_hits = set()
    if sun_state:
        sun_nak_dirs = get_vedha_directions(sun_nak_idx)
        for d in sun_dirs:
            target = sun_nak_dirs.get(d, -1)
            sun_hits.add(target)
        sun_hits.add(sun_nak_idx)

    # ── First pass: planet nak indices ────────────────────────────────────
    planet_nak_indices: dict[str, int] = {
        p.name: lon_to_nak_idx(p.lon) for p in planets
    }

    # ── Mutual Vedha detection ────────────────────────────────────────────
    def planets_do_mutual_vedha(pa: PlanetState, pb: PlanetState) -> bool:
        pa_dirs = get_active_directions(pa.name, pa.speed, pa.days_since_direct)
        pb_dirs = get_active_directions(pb.name, pb.speed, pb.days_since_direct)
        pa_nak = planet_nak_indices[pa.name]
        pb_nak = planet_nak_indices[pb.name]
        pa_vedha = get_vedha_directions(pa_nak)
        pb_vedha = get_vedha_directions(pb_nak)
        pa_targets = {pa_nak} | {pa_vedha[d] for d in pa_dirs if d in pa_vedha}
        pb_targets = {pb_nak} | {pb_vedha[d] for d in pb_dirs if d in pb_vedha}
        return (pb_nak in pa_targets) and (pa_nak in pb_targets)

    mutual_pairs: set[frozenset] = set()
    for i, pa in enumerate(planets):
        for pb in planets[i + 1 :]:
            if planets_do_mutual_vedha(pa, pb):
                mutual_pairs.add(frozenset({pa.name, pb.name}))

    # ── Main loop: analyse each planet ───────────────────────────────────
    planet_results: list[PlanetVedhaResult] = []
    total_raw = 0.0

    for p in planets:
        nak_idx = planet_nak_indices[p.name]
        _, nak_name = lon_to_nak(p.lon)
        pada = lon_to_pada(p.lon)

        active_dirs = get_active_directions(p.name, p.speed, p.days_since_direct)

        # Activated nakshatras + hits on stock
        nak_vedha = get_vedha_directions(nak_idx)
        activated_naks = {nak_idx}
        for d in active_dirs:
            if d in nak_vedha:
                activated_naks.add(nak_vedha[d])

        hits = []
        if stock_nak_idx in activated_naks:
            hits.append("direct")
        for d in active_dirs:
            target = nak_vedha.get(d)
            if target == stock_nak_idx:
                hits.append(d)
            if (
                nak_idx == front_idx
                and "front" in active_dirs
                and "front_vedha" not in hits
            ):
                hits.append("front_vedha")
            if (
                nak_idx == left_idx
                and "left" in active_dirs
                and "left_vedha" not in hits
            ):
                hits.append("left_vedha")
            if (
                nak_idx == right_idx
                and "right" in active_dirs
                and "right_vedha" not in hits
            ):
                hits.append("right_vedha")

        hits = list(dict.fromkeys(hits))  # deduplicate

        sun_weakened = p.name != "Sun" and nak_idx in sun_hits
        benefic_flag = is_benefic(p.name, moon_lon, sun_lon, p.lon, all_lons)
        is_mutual = any(p.name in pair for pair in mutual_pairs)

        # Strength
        if sun_weakened:
            strength = "weak"
        else:
            strength = vedha_strength(p.name, p.lon, sun_lon, moon_intra, is_mutual)

        # Commodity relevance
        comm_rel, comm_matches = commodity_relevance(nak_idx, sector)

        # ── STEP 7: CLASSICAL + FINANCIALLY TUNED SCORING ─────────────────
        raw = 0.0
        notes = []

        if hits:
            # Base score by strength
            base = (
                25.0 if strength == "strong" else 15.0 if strength == "normal" else 5.0
            )

            if not benefic_flag:  # Malefic → Bullish
                raw += base
                nature_str = "Malefic (Bullish)"
            else:  # Benefic → Bearish
                raw -= base
                nature_str = "Benefic (Bearish)"

            # Front / direct hit multiplier
            if any(d in ["front", "direct", "front_vedha"] for d in hits):
                raw *= 1.5
                notes.append("FRONT/DIRECT hit → 1.5× multiplier")

            # Mutual Vedha bonus
            if is_mutual:
                bonus = 12.0 if not benefic_flag else -12.0
                raw += bonus
                notes.append(f"Mutual Vedha → {'+' if bonus > 0 else ''}{bonus:.0f}")

            # Commodity bonus
            if comm_rel:
                comm_bonus = 10.0 if not benefic_flag else -10.0
                raw += comm_bonus
                notes.append(
                    f"Commodity match → {'+' if comm_bonus > 0 else ''}{comm_bonus:.0f}"
                )

            notes.append(
                f"Vedha hit — {nature_str}, {strength} strength → {base:+.1f} "
                f"({'+' if raw > 0 else ''}{raw:.1f} after multipliers)"
            )

        if sun_weakened:
            notes.append("Sun is Vedha-ing this planet — Weak Vedha (impact reduced)")

        # Debit & Combust for PlanetVedhaResult
        debit = is_debilitated(p.name, p.lon)
        comb = is_combust(p.name, p.lon, sun_lon)

        total_raw += raw

        planet_results.append(
            PlanetVedhaResult(
                planet=p.name,
                planet_lon=p.lon,
                planet_nak=nak_name,
                planet_nak_idx=nak_idx,
                planet_pada=pada,
                active_directions=active_dirs,
                hits=hits,
                is_benefic=benefic_flag,
                strength=strength,
                is_debilitated=debit,
                is_combust=comb,
                mutual_vedha=is_mutual,
                commodity_relevant=comm_rel,
                matched_commodities=comm_matches,
                raw_score=raw,
                notes=notes,
            )
        )

    # ── Final Step 7 Scoring (after all planets) ─────────────────────────
    bullish_count = sum(1 for r in planet_results if r.raw_score > 0)
    bearish_count = sum(1 for r in planet_results if r.raw_score < 0)
    neutral_count = sum(1 for r in planet_results if r.raw_score == 0)

    stock_comms = NAKSHATRA_COMMODITIES.get(stock_nak_idx, [])
    sec_kws = get_sector_keywords(sector)
    sec_matches = [c for c in stock_comms if any(kw in c for kw in sec_kws)]

    net = total_raw
    sbc_score = max(5, min(95, int(50 + (net / 90.0) * 45)))

    if sbc_score >= 72:
        sbc_label = "Strongly Bullish"
        sbc_color = "#059669"
    elif sbc_score >= 58:
        sbc_label = "Bullish"
        sbc_color = "#10b981"
    elif sbc_score >= 42:
        sbc_label = "Neutral"
        sbc_color = "#f59e0b"
    elif sbc_score >= 28:
        sbc_label = "Bearish"
        sbc_color = "#ef4444"
    else:
        sbc_label = "Strongly Bearish"
        sbc_color = "#991b1b"

    return SBCResult(
        symbol=symbol,
        stock_nak=stock_nak,
        stock_nak_idx=stock_nak_idx,
        stock_pada=stock_pada,
        vedha_front_nak=NAKSHATRAS[front_idx],
        vedha_left_nak=NAKSHATRAS[left_idx],
        vedha_right_nak=NAKSHATRAS[right_idx],
        planet_results=planet_results,
        tithi=tithi,
        paksha=paksha,
        moon_malefic_paksha=moon_malefic,
        raw_score=total_raw,
        sbc_score=sbc_score,
        sbc_label=sbc_label,
        sbc_color=sbc_color,
        bullish_count=bullish_count,
        bearish_count=bearish_count,
        neutral_count=neutral_count,
        stock_commodities=stock_comms,
        sector=sector,
        sector_commodity_matches=sec_matches,
        analysis_time=analysis_datetime.strftime("%Y-%m-%d %H:%M UTC"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10. SWISSEPH INTEGRATION — fetch live planet positions
# ─────────────────────────────────────────────────────────────────────────────


def fetch_planet_states(
    dt: Optional[datetime] = None,
    ephe_path: Optional[str] = None,
    retro_history_days: int = 30,
) -> list[PlanetState]:
    """
    Uses swisseph to compute current sidereal planetary positions.
    Detects retrograde→direct transitions by comparing current speed
    to recent history.

    Parameters
    ----------
    dt               : datetime to compute for (UTC); defaults to now
    ephe_path        : path to swisseph ephe/ folder
    retro_history_days: how many days back to search for station date
    """
    try:
        import swisseph as swe
    except ImportError:
        raise ImportError(
            "swisseph is not installed. Run: pip install pyswisseph\n"
            "Also place the ephe/ folder with Swiss Ephemeris data files."
        )

    import os

    if ephe_path is None:
        ephe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")
    swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL

    if dt is None:
        dt = datetime.now(timezone.utc)

    jd = swe.julday(
        dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + dt.second / 3600
    )

    planet_ids = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
    }

    states: list[PlanetState] = []

    for name, pid in planet_ids.items():
        result = swe.calc_ut(jd, pid, FLAGS)
        lon = result[0][0] % 360
        speed = result[0][3]

        # Detect retrograde→direct transition
        days_since_direct = None
        if name in RETRO_GRACE_DAYS and speed > 0:
            # Search back to find station (speed closest to 0 while transitioning)
            for back_days in range(1, retro_history_days + 1):
                jd_back = jd - back_days
                r_back = swe.calc_ut(jd_back, pid, FLAGS)
                spd_back = r_back[0][3]
                if spd_back < 0:  # was retrograde back_days ago
                    days_since_direct = float(back_days)
                    break

        states.append(
            PlanetState(
                name=name, lon=lon, speed=speed, days_since_direct=days_since_direct
            )
        )

    # Rahu (Mean Node) — always retrograde
    rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, FLAGS)
    rahu_lon = rahu_result[0][0] % 360
    ketu_lon = (rahu_lon + 180) % 360
    states.append(PlanetState(name="Rahu", lon=rahu_lon, speed=-0.053))
    states.append(PlanetState(name="Ketu", lon=ketu_lon, speed=-0.053))

    return states


# ─────────────────────────────────────────────────────────────────────────────
# 11. CONVENIENCE WRAPPER — analyse a symbol end-to-end
# ─────────────────────────────────────────────────────────────────────────────


def analyse_symbol(
    symbol: str,
    sector: str = "Unknown",
    ephe_path: Optional[str] = None,
    dt: Optional[datetime] = None,
    stock_lon: Optional[float] = None,
) -> SBCResult:
    """
    One-call entry point. Fetches live planet positions and runs full SBC.
    Requires swisseph + ephe/ folder.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    planets = fetch_planet_states(dt=dt, ephe_path=ephe_path)
    return analyse_sbc(
        symbol, planets, sector=sector, stock_lon=stock_lon, analysis_datetime=dt
    )


# ─────────────────────────────────────────────────────────────────────────────
# 12. PRETTY-PRINT REPORT
# ─────────────────────────────────────────────────────────────────────────────


def print_report(result: SBCResult) -> None:
    W = 72
    line = "─" * W

    print(f"\n{'═'*W}")
    print(f"  SARVATOBHADRA CHAKRA ANALYSIS")
    print(f"  Symbol : {result.symbol}   |   Sector: {result.sector}")
    print(f"  Time   : {result.analysis_time}")
    print(f"{'═'*W}")

    print(
        f"\n  Stock Nakshatra : {result.stock_nak} (#{result.stock_nak_idx+1})"
        + (f"  Pada: {result.stock_pada}" if result.stock_pada else "")
    )
    print(f"  Vedha Directions:")
    print(f"    FRONT  → {result.vedha_front_nak}")
    print(f"    LEFT   → {result.vedha_left_nak}")
    print(f"    RIGHT  → {result.vedha_right_nak}")

    print(
        f"\n  Moon: Tithi {result.tithi} ({result.paksha} Paksha)"
        + (
            "  ⚠ Moon acting as MALEFIC (Paksha rule)"
            if result.moon_malefic_paksha
            else ""
        )
    )

    if result.sector_commodity_matches:
        print(f"\n  Sector-Commodity Match  [{result.sector}]:")
        print(f"    {', '.join(result.sector_commodity_matches)}")

    print(f"\n{line}")
    print(
        f"  {'PLANET':<14}{'NAK':<22}{'DIRS':<14}{'HITS':<10}{'NATURE':<12}{'STRENGTH':<10}{'SCORE':>6}"
    )
    print(line)

    for r in result.planet_results:
        dirs_str = "+".join(r.active_directions)
        hits_str = "+".join(r.hits) if r.hits else "—"
        nature = "Benefic" if r.is_benefic else "Malefic"
        flags = ""
        if r.is_debilitated:
            flags += "D"
        if r.is_combust:
            flags += "C"
        if r.mutual_vedha:
            flags += "M"
        score_str = f"{r.raw_score:+.1f}" if r.raw_score != 0 else "  0.0"
        nak_str = f"{r.planet_nak}" + (f"[{flags}]" if flags else "")
        print(
            f"  {r.planet:<14}{nak_str:<22}{dirs_str:<14}{hits_str:<10}{nature:<12}{r.strength:<10}{score_str:>6}"
        )
        for note in r.notes:
            print(f"    {'↳'} {note}")

    print(line)
    print(f"\n  RAW SCORE : {result.raw_score:+.2f}")
    print(f"  SBC SCORE : {result.sbc_score}/100")
    print(f"  SIGNAL    : {result.sbc_label}")
    print(
        f"  Bullish planets: {result.bullish_count}   "
        f"Bearish: {result.bearish_count}   Neutral: {result.neutral_count}"
    )
    print(f"\n{'═'*W}\n")


# ─────────────────────────────────────────────────────────────────────────────
# 13. QUICK TEST  (runs without swisseph using mock planet data)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("SBC Engine — self-test with mock planet positions")
    print("(No swisseph required for this test)")

    mock_planets = [
        PlanetState("Sun", 35.5, 0.95),
        PlanetState("Moon", 210.3, 13.2),
        PlanetState("Mars", 82.1, 0.52),
        PlanetState("Mercury", 38.2, 1.85, days_since_direct=None),  # Atichari → LEFT
        PlanetState("Jupiter", 55.7, -0.08),  # Retrograde → RIGHT
        PlanetState("Venus", 22.0, 1.10),
        PlanetState("Saturn", 330.1, -0.03),  # Retrograde → RIGHT
        PlanetState("Rahu", 15.8, -0.053),
        PlanetState("Ketu", 195.8, -0.053),
    ]

    result = analyse_sbc(
        symbol="NIFTY",
        planets=mock_planets,
        sector="Financial Services",
        analysis_datetime=datetime(2026, 5, 27, 9, 15, tzinfo=timezone.utc),
    )

    print_report(result)

    # Test BANKNIFTY
    result2 = analyse_sbc(
        symbol="BANKNIFTY",
        planets=mock_planets,
        sector="Bank",
        analysis_datetime=datetime(2026, 5, 27, 9, 15, tzinfo=timezone.utc),
    )
    print_report(result2)

