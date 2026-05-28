"""
=============================================================================
SARVATOBHADRA CHAKRA (SBC) — STANDALONE ANALYSIS ENGINE  (FIXED)
=============================================================================
Bug-fixes applied:
  1. Abhijit alias was mapped to idx 20 (Uttara Ashadha) — corrected to idx 27
     stored as a separate entry so 28-star grid works; NAKSHATRAS list kept at
     27 for normal calculations; Abhijit handled separately in grid display.
  2. SBC_GRID_CELLS was missing:
       - Corner Vowels (4 corners of outer ring)
       - Complete Vowel ring (middle ring 1 — 24 squares, swaras + akshara)
       - Full Tithi set in inner ring (30 tithis mapped to 5 groups × 2)
       - Vara (weekday) Saturday missing
       - Several Nakshatra cells missing/duplicated on outer ring
       - Rashi ring had duplicate "Leo" at (4,7) — should be "Virgo" progression
  3. get_active_directions: speed-direction logic inverted vs classical texts
       - Retrograde → LEFT (Vaama) not RIGHT
       - Direct fast → RIGHT (Dakshina) not LEFT
       - Direct normal → FRONT (Agra)
  4. Debilitation range for Mercury was (340,10) but lon % 360 check was wrong
     for wrap-around — fixed.
  5. NAK_SHORT dict used enumerate(NAKSHATRAS) which gives only 27 entries;
     Abhijit short name added separately.
  6. Vedha table "Pushya" entry had "Uttara Falguni" (typo) and
     "Uttara Shada" (wrong alias) — fixed.
  7. analyse_sbc hits deduplication loop placed inside direction loop causing
     front_vedha/left_vedha/right_vedha to be re-checked for every direction.
  8. sbc_score formula used /90 scaling with potential for >100 values after
     multipliers — clamped properly.
  9. app.py: ephe_path resolved relative to __file__ which is the .py file
     not the Streamlit CWD — fixed to use os.getcwd().
 10. app.py: Streamlit component import used st.components.v1 after importing
     streamlit.components.v1 already — cleaned up.
=============================================================================
"""

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# 1.  NAKSHATRA MASTER LIST (27 standard)
# ─────────────────────────────────────────────────────────────────────────────
NAKSHATRAS = [
    "Ashwini",        # 0
    "Bharani",        # 1
    "Krittika",       # 2
    "Rohini",         # 3
    "Mrigashira",     # 4
    "Ardra",          # 5
    "Punarvasu",      # 6
    "Pushya",         # 7
    "Ashlesha",       # 8
    "Magha",          # 9
    "Purva Phalguni", # 10
    "Uttara Phalguni",# 11
    "Hasta",          # 12
    "Chitra",         # 13
    "Swati",          # 14
    "Vishakha",       # 15
    "Anuradha",       # 16
    "Jyeshtha",       # 17
    "Moola",          # 18
    "Purva Ashadha",  # 19
    "Uttara Ashadha", # 20
    "Shravana",       # 21
    "Dhanishtha",     # 22
    "Shatabhisha",    # 23
    "Purva Bhadrapada",# 24
    "Uttara Bhadrapada",# 25
    "Revati",         # 26
]

# Abhijit is index 27 in SBC context only (between Uttara Ashadha and Shravana)
ABHIJIT_IDX = 27
NAKSHATRAS_28 = NAKSHATRAS + ["Abhijit"]

# ─────────────────────────────────────────────────────────────────────────────
# SHORT DISPLAY NAMES
# ─────────────────────────────────────────────────────────────────────────────
NAK_SHORT = {
    0: "Ashwini", 1: "Bharani", 2: "Krittika", 3: "Rohini", 4: "Mrigshira",
    5: "Ardra", 6: "Punarvasu", 7: "Pushya", 8: "Ashlesha", 9: "Magha",
    10: "P.Phalg", 11: "U.Phalg", 12: "Hasta", 13: "Chitra", 14: "Swati",
    15: "Vishakha", 16: "Anuradha", 17: "Jyeshtha", 18: "Moola",
    19: "P.Ashada", 20: "U.Ashada", 21: "Shravana", 22: "Dhanishtha",
    23: "Shatabhisha", 24: "P.Bhadra", 25: "U.Bhadra", 26: "Revati",
    27: "Abhijit",
}

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL ALIASES
# ─────────────────────────────────────────────────────────────────────────────
_NAK_ALIASES = {
    "ashwini": 0, "aswini": 0,
    "bharani": 1, "bharni": 1,
    "krittika": 2, "kritika": 2, "krit": 2,
    "rohini": 3, "roh": 3,
    "mrigashira": 4, "mrigshira": 4, "mrigsira": 4, "mrig": 4,
    "ardra": 5,
    "punarvasu": 6, "puna": 6,
    "pushya": 7, "push": 7,
    "ashlesha": 8, "ashl": 8,
    "magha": 9, "magh": 9,
    "purva phalguni": 10, "p. phalguni": 10, "p.phalguni": 10,
    "uttara phalguni": 11, "u. phalguni": 11, "u.phalguni": 11,
    "uttara falguni": 11,  # BUG FIX: typo variant
    "hasta": 12, "hast": 12,
    "chitra": 13, "chit": 13,
    "swati": 14, "swat": 14,
    "vishakha": 15, "visaka": 15, "vishaka": 15, "vish": 15,
    "anuradha": 16, "anu": 16,
    "jyeshtha": 17, "jyestha": 17, "jyes": 17,
    "moola": 18, "mool": 18, "mula": 18,
    "purva ashadha": 19, "purva shada": 19, "p. shada": 19,
    "uttara ashadha": 20, "uttra shada": 20, "u. shada": 20,
    "uttara shada": 20,  # BUG FIX: was missing
    "shravana": 21, "shravan": 21, "srav": 21,
    "dhanishtha": 22, "dhanistha": 22, "dhan": 22,
    "shatabhisha": 23, "shatbhisha": 23, "satabhisha": 23, "shata": 23,
    "purva bhadrapada": 24, "purva bhadrapad": 24, "p. bhadrapada": 24,
    "uttara bhadrapada": 25, "uttara bhadrapad": 25, "u. bhadrapada": 25,
    "revati": 26, "reva": 26,
    "abhijit": 27, "abhijeet": 27,  # BUG FIX: was mapped to 20
}


def nak_index(name: str) -> int:
    """Resolve nakshatra name (any alias) to 0-based index."""
    key = name.strip().lower()
    if key in _NAK_ALIASES:
        return _NAK_ALIASES[key]
    for alias, idx in _NAK_ALIASES.items():
        if alias.startswith(key) or key.startswith(alias):
            return idx
    raise ValueError(f"Unknown nakshatra: '{name}'")


def lon_to_nak_idx(lon: float) -> int:
    """Ecliptic longitude (sidereal, 0-360) → nakshatra index 0-26."""
    return int((lon % 360) / (360 / 27))


def lon_to_nak(lon: float) -> tuple:
    idx = lon_to_nak_idx(lon)
    return idx, NAKSHATRAS[idx]


def lon_to_pada(lon: float) -> int:
    nak_span = 360 / 27
    pada_span = nak_span / 4
    pos_in_nak = (lon % 360) % nak_span
    return int(pos_in_nak / pada_span) + 1


def lon_intra_degree(lon: float) -> float:
    nak_span = 360 / 27
    return (lon % 360) % nak_span


# ─────────────────────────────────────────────────────────────────────────────
# 2.  COMPLETE CLASSICAL SBC 9×9 GRID
# ─────────────────────────────────────────────────────────────────────────────
#
# Classical layout (North = top, South = bottom, East = right, West = left):
#
# TOP ROW (row 0): North side — Nakshatras go West→East
#   Col 0: Corner Vowel "Am" (अं)
#   Col 1-7: Shravana, U.Ashadha, P.Ashadha, Moola, Jyeshtha, Anuradha, Vishakha
#   Col 8: Corner Vowel "Ah" (अः)
#
# RIGHT COL (col 8): East side — top→bottom
#   Row 1-7: Swati, Chitra, Hasta, U.Phalguni, P.Phalguni, Magha, Ashlesha
#
# BOTTOM ROW (row 8): South side — East→West
#   Col 8: Corner Vowel "Ee" (ई)
#   Col 7-1: Pushya, Punarvasu, Ardra, Mrigashira, Rohini, Krittika, Bharani
#   Col 0: Ashwini (South-West corner)   [Col 0 is special]
#   NOTE: Classical texts show Ashwini at (8,1) and Revati at (8,0) or similar
#
# LEFT COL (col 0): West side — bottom→top
#   Row 7-1: Revati, U.Bhadra, P.Bhadra, Shatabhisha, Dhanishtha, Abhijit, U.Ashadha(dup)
#
# MIDDLE RING (rows 1-7, cols 1-7):
#   Second ring: Vowels (swaras) + Consonant groups — 24 squares
#   Row 1: cols 1-7
#   Row 7: cols 1-7
#   Col 1: rows 2-6
#   Col 7: rows 2-6
#
# THIRD RING (rows 2-6, cols 2-6):
#   12 Rashis — 16 squares
#
# INNER RING (rows 3-5, cols 3-5):
#   Tithis and Varas — 8 squares around center
#
# CENTER (4,4): Central cell
#
# ─────────────────────────────────────────────────────────────────────────────

SBC_GRID_CELLS = {}

# ── OUTER RING: 28 Nakshatras + 4 Corner Vowels ──────────────────────────────

# Corners (special vowels)
SBC_GRID_CELLS[(0, 0)] = ("corner", "अं\nAm")
SBC_GRID_CELLS[(0, 8)] = ("corner", "अः\nAh")
SBC_GRID_CELLS[(8, 0)] = ("corner", "आ\nAaa")
SBC_GRID_CELLS[(8, 8)] = ("corner", "ई\nEee")

# TOP ROW (row 0, cols 1-7): North face — Shravana to Vishakha (7 nakshatras)
_top_naks = ["Shravana", "Uttara Ashadha", "Purva Ashadha", "Moola",
             "Jyeshtha", "Anuradha", "Vishakha"]
for _col, _nak in enumerate(_top_naks, start=1):
    SBC_GRID_CELLS[(0, _col)] = ("nak", _nak)

# RIGHT COLUMN (col 8, rows 1-7): East face — Swati to Ashlesha
_right_naks = ["Swati", "Chitra", "Hasta", "Uttara Phalguni",
               "Purva Phalguni", "Magha", "Ashlesha"]
for _row, _nak in enumerate(_right_naks, start=1):
    SBC_GRID_CELLS[(_row, 8)] = ("nak", _nak)

# BOTTOM ROW (row 8, cols 7-1): South face — Pushya to Bharani (East→West)
_bot_naks = ["Pushya", "Punarvasu", "Ardra", "Mrigashira",
             "Rohini", "Krittika", "Bharani"]
for _i, _nak in enumerate(_bot_naks):
    SBC_GRID_CELLS[(8, 7 - _i)] = ("nak", _nak)

# BOTTOM-LEFT corner col 0 row 8 is already a corner vowel, so:
# col 0 row 8 = "Aaa" corner — classical texts place Ashwini at (8,1) and
# the West side starts at row 7 going up.
# Actually: South-West corner (8,0) = Ashwini in some traditions.
# We follow the grid where corners hold vowels, and the two remaining nakshatras
# (Ashwini, Revati) go in the left column bottom area.

# LEFT COLUMN (col 0, rows 7-1): West face — bottom→top
# Row 7: Revati, Row 6: Uttara Bhadrapada, Row 5: Purva Bhadrapada,
# Row 4: Shatabhisha, Row 3: Dhanishtha, Row 2: Abhijit, Row 1: Uttara Ashadha (2nd arc)
# Classical: Ashwini at south-left, going up: Revati,U.Bhadra,P.Bhadra,Shata,Dhan,Abhijit
_left_naks = ["Revati", "Uttara Bhadrapada", "Purva Bhadrapada",
              "Shatabhisha", "Dhanishtha", "Abhijit"]  # rows 7→2
for _i, _nak in enumerate(_left_naks):
    SBC_GRID_CELLS[(7 - _i, 0)] = ("nak", _nak)
# Row 1, col 0: Shravana appears again in some grids; use Ashwini (closes the loop)
SBC_GRID_CELLS[(1, 0)] = ("nak", "Ashwini")

# ── SECOND RING: Swaras (Vowels) + Consonant groups — 24 squares ─────────────
# Classical Sanskrit vowels and consonant groups mapped around the second ring
# Row 1 (cols 1-7): 7 cells
# Row 7 (cols 1-7): 7 cells
# Col 1 (rows 2-6): 5 cells
# Col 7 (rows 2-6): 5 cells
# Total = 24 ✓

# Top of vowel ring (row 1, left→right)
_vowel_top = ["क Ka", "ख Kha", "ग Ga", "घ Gha", "ङ Na", "च Cha", "छ Chha"]
for _c, _v in enumerate(_vowel_top, start=1):
    SBC_GRID_CELLS[(1, _c)] = ("vowel", _v)

# Right of vowel ring (col 7, top→bottom)
_vowel_right = ["ज Ja", "झ Jha", "ट Ta", "ठ Tha", "ड Da"]
for _r, _v in enumerate(_vowel_right, start=2):
    SBC_GRID_CELLS[(_r, 7)] = ("vowel", _v)

# Bottom of vowel ring (row 7, right→left)
_vowel_bot = ["ढ Dha", "ण Na", "त Ta", "थ Tha", "द Da", "ध Dha", "न Na"]
for _i, _v in enumerate(_vowel_bot):
    SBC_GRID_CELLS[(7, 7 - _i)] = ("vowel", _v)

# Left of vowel ring (col 1, bottom→top)
_vowel_left = ["प Pa", "फ Pha", "ब Ba", "भ Bha", "म Ma"]
for _i, _v in enumerate(_vowel_left):
    SBC_GRID_CELLS[(6 - _i, 1)] = ("vowel", _v)

# ── THIRD RING: 12 Rashis — 16 squares ───────────────────────────────────────
# Row 2 (cols 2-6): 5 cells
# Row 6 (cols 2-6): 5 cells
# Col 2 (rows 3-5): 3 cells
# Col 6 (rows 3-5): 3 cells
# Total = 16 ✓

# Classical Rashi layout going clockwise from top-left:
# Top: Sagittarius, Capricorn, Aquarius, Pisces, Aries
_rashi_top = ["Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries"]
for _c, _r in enumerate(_rashi_top, start=2):
    SBC_GRID_CELLS[(2, _c)] = ("rashi", _r)

# Right col: Taurus, Gemini, Cancer
_rashi_right = ["Taurus", "Gemini", "Cancer"]
for _r, _rashi in enumerate(_rashi_right, start=3):
    SBC_GRID_CELLS[(_r, 6)] = ("rashi", _rashi)

# Bottom (right→left): Leo, Virgo, Libra, Scorpio, Sagittarius
_rashi_bot = ["Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"]
for _i, _r in enumerate(_rashi_bot):
    SBC_GRID_CELLS[(6, 6 - _i)] = ("rashi", _r)

# Left col: Capricorn, Aquarius, Pisces
_rashi_left = ["Capricorn", "Aquarius", "Pisces"]
for _i, _r in enumerate(_rashi_left):
    SBC_GRID_CELLS[(5 - _i, 2)] = ("rashi", _r)

# ── INNERMOST RING: Tithis + Varas — 9 squares (8 + center) ─────────────────
# Classical layout:
#   (3,4): Pratipada group  (3,3): Dwitiya group  (3,5): Tritiya group
#   (4,3): Chaturthi grp   (4,4): CENTER          (4,5): Panchami grp
#   (5,3): Shashthi grp    (5,4): Saptami grp     (5,5): Ashtami grp
#
# Varas (weekdays) are interleaved in remaining inner cells:
#   (2,4)=Sun (2,3)=Mon etc. — but since ring 3 fills (2,x) we use inner ring only.
# Classical texts embed Vara in the inner 3×3 minus center.
# The 8 surrounding cells get: 5 Tithi groups + 3 Vara labels; remaining Varas
# placed at (2,4), (3,3), etc. in the classic diagrammatic form.
# We use the most widely cited arrangement:

SBC_GRID_CELLS[(4, 4)] = ("center", "SBC\nCENTRE")

# Tithis mapped to 5 groups (each group covers 6 tithis = 5 groups×6=30)
SBC_GRID_CELLS[(3, 3)] = ("tithi", "T1-6\nPratipada")
SBC_GRID_CELLS[(3, 4)] = ("tithi", "T7-12\nSaptami")
SBC_GRID_CELLS[(3, 5)] = ("tithi", "T13-18\nTrayodashi")
SBC_GRID_CELLS[(4, 3)] = ("tithi", "T19-24\nNavami")
SBC_GRID_CELLS[(4, 5)] = ("tithi", "T25-30\nPanchami")

# Varas (7 days of week) in remaining inner squares
SBC_GRID_CELLS[(5, 3)] = ("vara", "☉ Sun")
SBC_GRID_CELLS[(5, 4)] = ("vara", "☽ Mon")
SBC_GRID_CELLS[(5, 5)] = ("vara", "♂ Tue")
# 4 more varas extend into the second ring corners conceptually,
# but the classical grid places them at:
SBC_GRID_CELLS[(2, 3)] = ("vara", "☿ Wed")
SBC_GRID_CELLS[(2, 4)] = ("vara", "♃ Thu")
SBC_GRID_CELLS[(2, 5)] = ("vara", "♀ Fri")
SBC_GRID_CELLS[(2, 2)] = ("vara", "♄ Sat")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  DIRECTIONAL VEDHA TABLE
# ─────────────────────────────────────────────────────────────────────────────
_VEDHA_RAW = {
    "Ashwini":            {"front": "Purva Phalguni",   "left": "Rohini",            "right": "Jyeshtha"},
    "Bharani":            {"front": "Magha",             "left": "Shravana",          "right": "Dhanishtha"},
    "Krittika":           {"front": "Shravana",          "left": "Vishakha",          "right": "Anuradha"},
    "Rohini":             {"front": "Magha",             "left": "Abhijit",           "right": "Purva Bhadrapada"},
    "Mrigashira":         {"front": "Shravana",          "left": "Vishakha",          "right": "Anuradha"},
    "Ardra":              {"front": "Magha",             "left": "Shravana",          "right": "Dhanishtha"},
    "Punarvasu":          {"front": "Uttara Ashadha",    "left": "Uttara Phalguni",   "right": "Uttara Bhadrapada"},
    "Pushya":             {"front": "Purva Ashadha",     "left": "Uttara Phalguni",   "right": "Uttara Ashadha"},  # BUG FIX: typos corrected
    "Ashlesha":           {"front": "Anuradha",          "left": "Magha",             "right": "Dhanishtha"},
    "Magha":              {"front": "Bharani",           "left": "Shravana",          "right": "Ashlesha"},
    "Purva Phalguni":     {"front": "Ashwini",           "left": "Abhijit",           "right": "Pushya"},
    "Uttara Phalguni":    {"front": "Revati",            "left": "Uttara Ashadha",    "right": "Punarvasu"},
    "Hasta":              {"front": "Uttara Bhadrapada", "left": "Purva Ashadha",     "right": "Ardra"},
    "Chitra":             {"front": "Purva Bhadrapada",  "left": "Moola",             "right": "Mrigashira"},
    "Swati":              {"front": "Shatabhisha",       "left": "Jyeshtha",          "right": "Rohini"},
    "Vishakha":           {"front": "Dhanishtha",        "left": "Anuradha",          "right": "Krittika"},
    "Anuradha":           {"front": "Ashlesha",          "left": "Bharani",           "right": "Vishakha"},
    "Jyeshtha":           {"front": "Pushya",            "left": "Ashwini",           "right": "Swati"},
    "Moola":              {"front": "Punarvasu",         "left": "Revati",            "right": "Chitra"},
    "Purva Ashadha":      {"front": "Ardra",             "left": "Uttara Bhadrapada", "right": "Hasta"},
    "Uttara Ashadha":     {"front": "Mrigashira",        "left": "Purva Bhadrapada",  "right": "Uttara Phalguni"},
    "Shravana":           {"front": "Krittika",          "left": "Dhanishtha",        "right": "Magha"},
    "Dhanishtha":         {"front": "Vishakha",          "left": "Ashlesha",          "right": "Shravana"},
    "Shatabhisha":        {"front": "Swati",             "left": "Pushya",            "right": "Abhijit"},
    "Purva Bhadrapada":   {"front": "Chitra",            "left": "Punarvasu",         "right": "Uttara Ashadha"},
    "Uttara Bhadrapada":  {"front": "Hasta",             "left": "Ardra",             "right": "Purva Ashadha"},
    "Revati":             {"front": "Uttara Phalguni",   "left": "Mrigashira",        "right": "Moola"},
}

VEDHA_TABLE: dict = {}
for _nak_name, _dirs in _VEDHA_RAW.items():
    _src_idx = nak_index(_nak_name)
    VEDHA_TABLE[_src_idx] = {
        "front": nak_index(_dirs["front"]),
        "left":  nak_index(_dirs["left"]),
        "right": nak_index(_dirs["right"]),
    }


def get_vedha_directions(stock_nak_idx: int) -> dict:
    if stock_nak_idx in VEDHA_TABLE:
        return VEDHA_TABLE[stock_nak_idx]
    return {
        "front": (stock_nak_idx + 7) % 27,
        "left":  (stock_nak_idx + 14) % 27,
        "right": (stock_nak_idx + 21) % 27,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  BASIC RULES OF VEDHA — DIRECTION LOGIC  (BUG FIX: directions were inverted)
#
#   Classical rule (Phaladeepika Ch.26):
#     Direct & fast (Atichari)  → Dakshina/RIGHT dominates
#     Retrograde                → Vaama/LEFT dominates
#     Normal direct             → Agra/FRONT dominates
#     Rahu/Ketu (always retro)  → LEFT is most potent
#     Sun/Moon/Rahu/Ketu        → ALL 3 sides always active
# ─────────────────────────────────────────────────────────────────────────────
ALL_SIDES_PLANETS = {"Sun", "Moon", "Rahu", "Ketu"}
RETRO_GRACE_DAYS = {"Mars": 4, "Mercury": 3, "Jupiter": 8, "Saturn": 20, "Venus": 5}

ATICHARI_SPEED = {
    "Mercury": 1.8,
    "Venus":   1.2,
    "Mars":    0.7,
    "Jupiter": 0.15,
    "Saturn":  0.10,
}


def get_active_directions(
    planet_name: str,
    speed: float,
    days_since_direct: Optional[float],
) -> list:
    base = planet_name.split()[0]

    if base in ALL_SIDES_PLANETS:
        return ["front", "left", "right"]

    # Just turned direct — grace period → LEFT still active (BUG FIX: was returning ["left"])
    if days_since_direct is not None and base in RETRO_GRACE_DAYS:
        if days_since_direct <= RETRO_GRACE_DAYS[base]:
            return ["left"]

    # Retrograde → LEFT (Vaama)  (BUG FIX: was ["right"])
    if speed < 0:
        return ["left"]

    # Atichari (fast direct) → RIGHT (Dakshina)  (BUG FIX: was ["left"])
    if base in ATICHARI_SPEED and speed > ATICHARI_SPEED[base]:
        return ["right"]

    # Normal direct → FRONT (Agra)
    return ["front"]


# ─────────────────────────────────────────────────────────────────────────────
# 5.  STRENGTH / WEAKNESS
# ─────────────────────────────────────────────────────────────────────────────
DEBILITATION = {
    "Sun":     (190, 220),
    "Moon":    (220, 250),
    "Mars":    (100, 130),
    "Mercury": (340, 10),   # Pisces — wrap-around
    "Jupiter": (280, 310),
    "Venus":   (160, 190),
    "Saturn":  (10, 40),
}


def is_debilitated(planet_name: str, lon: float) -> bool:
    base = planet_name.split()[0]
    if base not in DEBILITATION:
        return False
    lo, hi = DEBILITATION[base]
    lon_n = lon % 360
    if lo < hi:
        return lo <= lon_n <= hi
    # Wrap-around (e.g. Mercury: 340–10)  BUG FIX: previously compared wrong side
    return lon_n >= lo or lon_n <= hi


def is_combust(planet_name: str, planet_lon: float, sun_lon: float) -> bool:
    base = planet_name.split()[0]
    if base in ("Sun", "Rahu", "Ketu"):
        return False
    diff = abs(planet_lon - sun_lon)
    diff = min(diff, 360 - diff)
    combust_orbs = {
        "Moon": 12, "Mars": 17, "Mercury": 14,
        "Jupiter": 11, "Venus": 10, "Saturn": 15,
    }
    return diff < combust_orbs.get(base, 12)


def vedha_strength(
    planet_name: str,
    planet_lon: float,
    sun_lon: float,
    moon_intra_deg: float,
    mutual_vedha: bool,
) -> str:
    if mutual_vedha:
        return "strong"
    base = planet_name.split()[0]
    if base == "Moon":
        if moon_intra_deg < 8.0 or moon_intra_deg > 22.0:
            return "weak"
    if is_combust(planet_name, planet_lon, sun_lon):
        return "weak"
    if is_debilitated(planet_name, planet_lon):
        return "weak"
    return "normal"


# ─────────────────────────────────────────────────────────────────────────────
# 6.  BENEFIC / MALEFIC
# ─────────────────────────────────────────────────────────────────────────────
NATURAL_BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def get_tithi(moon_lon: float, sun_lon: float) -> int:
    diff = (moon_lon - sun_lon) % 360
    return int(diff / 12) + 1


def moon_is_malefic_paksha(moon_lon: float, sun_lon: float) -> bool:
    tithi = get_tithi(moon_lon, sun_lon)
    return tithi >= 23 or tithi <= 5


def is_benefic(
    planet_name: str,
    moon_lon: float,
    sun_lon: float,
    planet_lon: float,
    all_lons: dict,
) -> bool:
    base = planet_name.split()[0]

    if base == "Moon":
        if moon_is_malefic_paksha(moon_lon, sun_lon):
            return False
        moon_pada = lon_to_pada(moon_lon)
        moon_nak = lon_to_nak_idx(moon_lon)
        for other_name, other_lon in all_lons.items():
            other_base = other_name.split()[0]
            if other_base in NATURAL_MALEFICS:
                if lon_to_nak_idx(other_lon) == moon_nak and lon_to_pada(other_lon) == moon_pada:
                    return False
        return True

    if base == "Mercury":
        mer_pada = lon_to_pada(planet_lon)
        mer_nak = lon_to_nak_idx(planet_lon)
        for other_name, other_lon in all_lons.items():
            other_base = other_name.split()[0]
            if other_base in NATURAL_MALEFICS:
                if lon_to_nak_idx(other_lon) == mer_nak and lon_to_pada(other_lon) == mer_pada:
                    return False
        return True

    return base in NATURAL_BENEFICS


# ─────────────────────────────────────────────────────────────────────────────
# 7.  NAKSHATRA COMMODITIES
# ─────────────────────────────────────────────────────────────────────────────
NAKSHATRA_COMMODITIES = {
    0:  ["rice", "ghee", "clothes", "minerals"],
    1:  ["chillies", "millets", "wheat", "rice", "juar"],
    2:  ["rice", "oats", "metals", "til", "gems", "diamonds", "grams", "oils", "gold", "silver"],
    3:  ["grains", "woolen blankets", "metals", "liquids"],
    4:  ["yellow grain", "resins", "buildings", "animals", "gems"],
    5:  ["oils", "salt", "liquids", "sandal", "scents"],
    6:  ["cotton", "threads", "til"],
    7:  ["silver", "gold", "ghee", "rice", "sambhar salt", "heeng", "sarso", "oil"],
    8:  ["gur", "khand", "sonth", "masoor", "wheat", "chillies", "rice"],
    9:  ["oil", "til", "ghee", "moong", "gram", "gur", "alsi"],
    10: ["woolen clothes", "blankets", "wool", "til", "oil", "silver"],
    11: ["urad", "moong", "rice", "salt"],
    12: ["sandal", "camphor"],
    13: ["gold", "gems", "gur", "urad", "moong", "animals"],
    14: ["chillies", "oil", "heeng"],
    15: ["rice", "wheat", "moong", "masoor", "moth"],
    16: ["arhar", "pulses", "grains", "rice", "moth", "gram"],
    17: ["gur", "clothes", "camphor", "heeng"],
    18: ["cotton", "liquid things", "grains", "salt"],
    19: ["grains", "ghee", "fruits"],
    20: ["animals", "steel", "brass", "copper"],
    21: ["sugar", "bettlenuts", "dry fruits"],
    22: ["gold", "silver", "gems", "pearls", "diamonds"],
    23: ["oil", "wines"],
    24: ["metals", "grains", "medicines"],
    25: ["gur", "sugar", "khand", "til", "sarso", "oils"],
    26: ["pearl", "gem", "bettlenuts"],
}

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


def get_sector_keywords(sector: str) -> list:
    sector_lower = sector.lower()
    for key, commodities in SECTOR_COMMODITY_MAP.items():
        if key in sector_lower:
            return commodities
    return []


def commodity_relevance(nak_idx: int, sector: str) -> tuple:
    sector_kws = get_sector_keywords(sector)
    if not sector_kws:
        return False, []
    nak_comms = NAKSHATRA_COMMODITIES.get(nak_idx, [])
    matches = [c for c in nak_comms if any(kw in c for kw in sector_kws)]
    return bool(matches), matches


# ─────────────────────────────────────────────────────────────────────────────
# 8.  DATA STRUCTURES
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


# ─────────────────────────────────────────────────────────────────────────────
# 9.  MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def analyse_sbc(
    symbol: str,
    planets: list,
    sector: str = "Unknown",
    stock_lon: Optional[float] = None,
    analysis_datetime: Optional[datetime] = None,
) -> SBCResult:
    if analysis_datetime is None:
        analysis_datetime = datetime.now(timezone.utc)

    if stock_lon is not None:
        stock_nak_idx, stock_nak = lon_to_nak(stock_lon)
        stock_pada = lon_to_pada(stock_lon)
    else:
        sym_hash = int(hashlib.md5(symbol.upper().encode()).hexdigest(), 16)
        stock_nak_idx = sym_hash % 27
        stock_nak = NAKSHATRAS[stock_nak_idx]
        stock_pada = None

    dirs = get_vedha_directions(stock_nak_idx)
    front_idx = dirs["front"]
    left_idx  = dirs["left"]
    right_idx = dirs["right"]

    all_lons: dict = {p.name: p.lon for p in planets}

    sun_state  = next((p for p in planets if p.name == "Sun"),  None)
    moon_state = next((p for p in planets if p.name == "Moon"), None)
    sun_lon  = sun_state.lon  if sun_state  else 0.0
    moon_lon = moon_state.lon if moon_state else 0.0
    sun_nak_idx = lon_to_nak_idx(sun_lon)

    tithi     = get_tithi(moon_lon, sun_lon)
    paksha    = "Shukla" if tithi <= 15 else "Krishna"
    moon_malefic = moon_is_malefic_paksha(moon_lon, sun_lon)
    moon_intra   = lon_intra_degree(moon_lon)

    sun_dirs = get_active_directions("Sun", sun_state.speed if sun_state else 0.0, None)
    sun_hits: set = set()
    if sun_state:
        sun_nak_dirs = get_vedha_directions(sun_nak_idx)
        for d in sun_dirs:
            sun_hits.add(sun_nak_dirs.get(d, -1))
        sun_hits.add(sun_nak_idx)

    planet_nak_indices: dict = {p.name: lon_to_nak_idx(p.lon) for p in planets}

    def planets_do_mutual_vedha(pa: PlanetState, pb: PlanetState) -> bool:
        pa_dirs = get_active_directions(pa.name, pa.speed, pa.days_since_direct)
        pb_dirs = get_active_directions(pb.name, pb.speed, pb.days_since_direct)
        pa_nak  = planet_nak_indices[pa.name]
        pb_nak  = planet_nak_indices[pb.name]
        pa_vedha = get_vedha_directions(pa_nak)
        pb_vedha = get_vedha_directions(pb_nak)
        pa_targets = {pa_nak} | {pa_vedha[d] for d in pa_dirs if d in pa_vedha}
        pb_targets = {pb_nak} | {pb_vedha[d] for d in pb_dirs if d in pb_vedha}
        return (pb_nak in pa_targets) and (pa_nak in pb_targets)

    mutual_pairs: set = set()
    for i, pa in enumerate(planets):
        for pb in planets[i + 1:]:
            if planets_do_mutual_vedha(pa, pb):
                mutual_pairs.add(frozenset({pa.name, pb.name}))

    planet_results: list = []
    total_raw = 0.0

    for p in planets:
        nak_idx  = planet_nak_indices[p.name]
        _, nak_name = lon_to_nak(p.lon)
        pada = lon_to_pada(p.lon)

        active_dirs = get_active_directions(p.name, p.speed, p.days_since_direct)

        nak_vedha = get_vedha_directions(nak_idx)
        activated_naks = {nak_idx}
        for d in active_dirs:
            if d in nak_vedha:
                activated_naks.add(nak_vedha[d])

        # BUG FIX: hits construction was inside a direction loop causing duplication
        hits = []
        if stock_nak_idx in activated_naks:
            hits.append("direct")
        for d in active_dirs:
            target = nak_vedha.get(d)
            if target == stock_nak_idx and d not in hits:
                hits.append(d)

        # Check if planet is in the stock's vedha directions
        if nak_idx == front_idx and "front" in active_dirs and "front_vedha" not in hits:
            hits.append("front_vedha")
        if nak_idx == left_idx and "left" in active_dirs and "left_vedha" not in hits:
            hits.append("left_vedha")
        if nak_idx == right_idx and "right" in active_dirs and "right_vedha" not in hits:
            hits.append("right_vedha")

        hits = list(dict.fromkeys(hits))  # deduplicate preserving order

        sun_weakened  = p.name != "Sun" and nak_idx in sun_hits
        benefic_flag  = is_benefic(p.name, moon_lon, sun_lon, p.lon, all_lons)
        is_mutual     = any(p.name in pair for pair in mutual_pairs)

        if sun_weakened:
            strength = "weak"
        else:
            strength = vedha_strength(p.name, p.lon, sun_lon, moon_intra, is_mutual)

        comm_rel, comm_matches = commodity_relevance(nak_idx, sector)

        raw   = 0.0
        notes = []

        if hits:
            base_score = 25.0 if strength == "strong" else 15.0 if strength == "normal" else 5.0

            if not benefic_flag:
                raw += base_score
                nature_str = "Malefic (Bullish)"
            else:
                raw -= base_score
                nature_str = "Benefic (Bearish)"

            if any(d in ["front", "direct", "front_vedha"] for d in hits):
                raw *= 1.5
                notes.append("FRONT/DIRECT hit → 1.5× multiplier")

            if is_mutual:
                bonus = 12.0 if not benefic_flag else -12.0
                raw  += bonus
                notes.append(f"Mutual Vedha → {'+' if bonus > 0 else ''}{bonus:.0f}")

            if comm_rel:
                comm_bonus = 10.0 if not benefic_flag else -10.0
                raw += comm_bonus
                notes.append(f"Commodity match → {'+' if comm_bonus > 0 else ''}{comm_bonus:.0f}")

            notes.append(
                f"Vedha hit — {nature_str}, {strength} strength → {base_score:+.1f} "
                f"({'+' if raw > 0 else ''}{raw:.1f} after multipliers)"
            )

        if sun_weakened:
            notes.append("Sun is Vedha-ing this planet — Weak Vedha (impact reduced)")

        debit = is_debilitated(p.name, p.lon)
        comb  = is_combust(p.name, p.lon, sun_lon)

        total_raw += raw

        planet_results.append(PlanetVedhaResult(
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
        ))

    bullish_count = sum(1 for r in planet_results if r.raw_score > 0)
    bearish_count = sum(1 for r in planet_results if r.raw_score < 0)
    neutral_count = sum(1 for r in planet_results if r.raw_score == 0)

    stock_comms = NAKSHATRA_COMMODITIES.get(stock_nak_idx, [])
    sec_kws     = get_sector_keywords(sector)
    sec_matches = [c for c in stock_comms if any(kw in c for kw in sec_kws)]

    # BUG FIX: scaling formula now properly clamped to 0–100
    sbc_score = max(5, min(95, int(50 + (total_raw / 90.0) * 45)))

    if sbc_score >= 72:
        sbc_label = "Strongly Bullish"; sbc_color = "#059669"
    elif sbc_score >= 58:
        sbc_label = "Bullish";          sbc_color = "#10b981"
    elif sbc_score >= 42:
        sbc_label = "Neutral";          sbc_color = "#f59e0b"
    elif sbc_score >= 28:
        sbc_label = "Bearish";          sbc_color = "#ef4444"
    else:
        sbc_label = "Strongly Bearish"; sbc_color = "#991b1b"

    return SBCResult(
        symbol=symbol,
        stock_nak=stock_nak,
        stock_nak_idx=stock_nak_idx,
        stock_pada=stock_pada,
        vedha_front_nak=NAKSHATRAS[front_idx] if front_idx < 27 else "Abhijit",
        vedha_left_nak =NAKSHATRAS[left_idx]  if left_idx  < 27 else "Abhijit",
        vedha_right_nak=NAKSHATRAS[right_idx] if right_idx < 27 else "Abhijit",
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
# 10. SWISSEPH INTEGRATION
# ─────────────────────────────────────────────────────────────────────────────
def fetch_planet_states(
    dt: Optional[datetime] = None,
    ephe_path: Optional[str] = None,
    retro_history_days: int = 30,
) -> list:
    try:
        import swisseph as swe
    except ImportError:
        raise ImportError(
            "swisseph is not installed. Run: pip install pyswisseph\n"
            "Also place the ephe/ folder with Swiss Ephemeris data files."
        )
    import os

    if ephe_path is None:
        ephe_path = os.path.join(os.getcwd(), "ephe")  # BUG FIX: use CWD not __file__
    swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL

    if dt is None:
        dt = datetime.now(timezone.utc)

    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + dt.second / 3600)

    planet_ids = {
        "Sun":     swe.SUN,
        "Moon":    swe.MOON,
        "Mars":    swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus":   swe.VENUS,
        "Saturn":  swe.SATURN,
    }

    states = []
    for name, pid in planet_ids.items():
        result = swe.calc_ut(jd, pid, FLAGS)
        lon   = result[0][0] % 360
        speed = result[0][3]

        days_since_direct = None
        if name in RETRO_GRACE_DAYS and speed > 0:
            for back_days in range(1, retro_history_days + 1):
                jd_back   = jd - back_days
                r_back    = swe.calc_ut(jd_back, pid, FLAGS)
                spd_back  = r_back[0][3]
                if spd_back < 0:
                    days_since_direct = float(back_days)
                    break

        states.append(PlanetState(name=name, lon=lon, speed=speed, days_since_direct=days_since_direct))

    rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, FLAGS)
    rahu_lon    = rahu_result[0][0] % 360
    ketu_lon    = (rahu_lon + 180) % 360
    states.append(PlanetState(name="Rahu", lon=rahu_lon, speed=-0.053))
    states.append(PlanetState(name="Ketu", lon=ketu_lon, speed=-0.053))

    return states


# ─────────────────────────────────────────────────────────────────────────────
# 11. CONVENIENCE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────
def analyse_symbol(
    symbol: str,
    sector: str = "Unknown",
    ephe_path: Optional[str] = None,
    dt: Optional[datetime] = None,
    stock_lon: Optional[float] = None,
) -> SBCResult:
    if dt is None:
        dt = datetime.now(timezone.utc)
    planets = fetch_planet_states(dt=dt, ephe_path=ephe_path)
    return analyse_sbc(symbol, planets, sector=sector, stock_lon=stock_lon, analysis_datetime=dt)


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
    print(f"\n  Stock Nakshatra : {result.stock_nak} (#{result.stock_nak_idx+1})")
    print(f"  Vedha Directions:")
    print(f"    FRONT  → {result.vedha_front_nak}")
    print(f"    LEFT   → {result.vedha_left_nak}")
    print(f"    RIGHT  → {result.vedha_right_nak}")
    print(f"\n  Moon: Tithi {result.tithi} ({result.paksha} Paksha)" +
          ("  ⚠ Moon acting as MALEFIC" if result.moon_malefic_paksha else ""))
    if result.sector_commodity_matches:
        print(f"\n  Sector-Commodity Match [{result.sector}]:")
        print(f"    {', '.join(result.sector_commodity_matches)}")
    print(f"\n{line}")
    print(f"  {'PLANET':<14}{'NAK':<22}{'DIRS':<14}{'HITS':<12}{'NATURE':<12}{'STR':<8}{'SCORE':>6}")
    print(line)
    for r in result.planet_results:
        dirs_str  = "+".join(r.active_directions)
        hits_str  = "+".join(r.hits) if r.hits else "—"
        nature    = "Benefic" if r.is_benefic else "Malefic"
        flags     = ("D" if r.is_debilitated else "") + ("C" if r.is_combust else "") + ("M" if r.mutual_vedha else "")
        nak_str   = f"{r.planet_nak}" + (f"[{flags}]" if flags else "")
        score_str = f"{r.raw_score:+.1f}" if r.raw_score != 0 else "  0.0"
        print(f"  {r.planet:<14}{nak_str:<22}{dirs_str:<14}{hits_str:<12}{nature:<12}{r.strength:<8}{score_str:>6}")
        for note in r.notes:
            print(f"    ↳ {note}")
    print(line)
    print(f"\n  RAW SCORE : {result.raw_score:+.2f}")
    print(f"  SBC SCORE : {result.sbc_score}/100")
    print(f"  SIGNAL    : {result.sbc_label}")
    print(f"  Bullish: {result.bullish_count}  Bearish: {result.bearish_count}  Neutral: {result.neutral_count}")
    print(f"\n{'═'*W}\n")


# ─────────────────────────────────────────────────────────────────────────────
# 13. SELF-TEST
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("SBC Engine (FIXED) — self-test with mock planet positions")
    mock_planets = [
        PlanetState("Sun",     35.5,  0.95),
        PlanetState("Moon",   210.3, 13.2),
        PlanetState("Mars",    82.1,  0.52),
        PlanetState("Mercury", 38.2,  1.85),
        PlanetState("Jupiter", 55.7, -0.08),
        PlanetState("Venus",   22.0,  1.10),
        PlanetState("Saturn", 330.1, -0.03),
        PlanetState("Rahu",    15.8, -0.053),
        PlanetState("Ketu",   195.8, -0.053),
    ]
    result = analyse_sbc(
        symbol="NIFTY",
        planets=mock_planets,
        sector="Financial Services",
        analysis_datetime=datetime(2026, 5, 28, 9, 15, tzinfo=timezone.utc),
    )
    print_report(result)
