def build_sbc_grid_html(stock_nak, front_nak, left_nak, right_nak, moon_nak):
    from sbc_engine import NAKSHATRAS

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

    # ── CORRECTED CLASSICAL PERIMETER (28 unique positions) ──
    # Clockwise from NE corner (standard SBC layout)
    perimeter = [
        (0,1,21), (0,2,20), (0,3,19), (0,4,18), (0,5,17), (0,6,16), (0,7,15), (0,8,14),
        (1,8,13), (2,8,12), (3,8,11), (4,8,10), (5,8,9), (6,8,8), (7,8,7), (8,8,6),
        (8,7,5), (8,6,4), (8,5,3), (8,4,2), (8,3,1), (8,2,0), (8,1,26),
        (7,0,25), (6,0,24), (5,0,23), (4,0,22), (3,0,21), (2,0,20), (1,0,19)
    ]

    short = [
        "Ashwini","Bharani","Krittika","Rohini","Mrigshira","Ardra","Punarvasu","Pushya",
        "Ashlesha","Magha","P.Phalguni","U.Phalguni","Hasta","Chitra","Swati","Vishakha",
        "Anuradha","Jyeshtha","Moola","P.Ashadha","U.Ashadha","Shravana","Dhanishtha",
        "Shatabhisha","P.Bhadra","U.Bhadra","Revati"
    ]

    cell_map = {(row, col): nak for row, col, nak in perimeter}

    # ── Beautiful HTML with Vedic dark theme ─────────────────────────────
    html = f"""
    <div style="font-family: 'Crimson Pro', serif; padding: 20px; background: #0a0806; color: #d4c4a0; border-radius: 8px;">
        <div style="text-align:center; font-size:13px; color:#c9a84c; margin-bottom:8px; letter-spacing:2px;">SARVATOBHADRA CHAKRA</div>
        
        <div style="display:flex; align-items:center; justify-content:center; gap:8px;">
            <div style="writing-mode:vertical-rl; transform:rotate(180deg); font-size:11px; color:#c9a84c;">WEST</div>
            
            <div style="display:grid; grid-template-columns:repeat(9, 68px); grid-template-rows:repeat(9, 68px); gap:3px; background:#2e2618; padding:3px; border-radius:6px;">
    """

    # Build 9x9 grid cells
    for row in range(9):
        for col in range(9):
            nak_i = cell_map.get((row, col))
            style = "width:68px;height:68px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-radius:4px;font-size:10px;position:relative;"
            
            if (row in [0,8] and col in [0,8]):  # corners
                style += "background:#1a1610;color:#6b5320;border:1px solid #c9a84c;"
                html += f'<div style="{style}">◼</div>'
            elif nak_i is not None:  # nakshatra cells
                is_stock = nak_i == s
                is_front = nak_i == f
                is_left  = nak_i == l
                is_right = nak_i == r
                is_moon  = nak_i == m and m != -1

                if is_stock:
                    style += "background:#EEEDFE;border:3px solid #534AB7;color:#3C3489;font-weight:700;"
                elif is_front:
                    style += "background:rgba(232,200,122,0.18);border:3px solid #e8c87a;animation:vedhaFront 1.5s infinite alternate;"
                elif is_left:
                    style += "background:rgba(196,74,58,0.18);border:3px solid #c44a3a;animation:vedhaLeft 1.5s infinite alternate;"
                elif is_right:
                    style += "background:rgba(74,156,106,0.18);border:3px solid #4a9c6a;animation:vedhaRight 1.5s infinite alternate;"
                else:
                    style += "background:#120f09;color:#d4c4a0;border:1px solid #6b5320;"

                badge = f'<div style="position:absolute;top:2px;right:2px;font-size:9px;background:#FAECE7;color:#993C1D;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;">🌕</div>' if is_moon else ''
                
                html += f'<div style="{style}"><span style="font-weight:600">{short[nak_i]}</span>{badge}</div>'
            else:
                # Inner cells (rashi/tithi)
                style += "background:#1a1610;color:#7a6d55;font-size:9px;border:1px solid #2e2618;"
                html += f'<div style="{style}">•</div>'

    html += """
            </div>
            
            <div style="writing-mode:vertical-rl; font-size:11px; color:#c9a84c;">EAST</div>
        </div>
        
        <div style="text-align:center; font-size:11px; color:#c9a84c; margin-top:8px;">SOUTH</div>
        
        <!-- Legend -->
        <div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center; margin-top:16px; font-size:12px;">
            <span style="display:flex;align-items:center;gap:6px;"><span style="width:14px;height:14px;background:#EEEDFE;border:2px solid #534AB7;border-radius:3px;"></span>Stock Nakshatra</span>
            <span style="display:flex;align-items:center;gap:6px;"><span style="width:14px;height:14px;background:rgba(232,200,122,0.18);border:2px solid #e8c87a;border-radius:3px;"></span>Front Vedha</span>
            <span style="display:flex;align-items:center;gap:6px;"><span style="width:14px;height:14px;background:rgba(74,156,106,0.18);border:2px solid #4a9c6a;border-radius:3px;"></span>Right Vedha</span>
            <span style="display:flex;align-items:center;gap:6px;"><span style="width:14px;height:14px;background:rgba(196,74,58,0.18);border:2px solid #c44a3a;border-radius:3px;"></span>Left Vedha</span>
            <span style="display:flex;align-items:center;gap:6px;"><span style="width:14px;height:14px;background:#FAECE7;color:#993C1D;border-radius:50%;display:flex;align-items:center;justify-content:center;">🌕</span>Moon</span>
        </div>
    </div>
    
    <style>
    @keyframes vedhaFront { from { opacity: 0.7; } to { opacity: 1; } }
    @keyframes vedhaRight { from { opacity: 0.7; } to { opacity: 1; } }
    @keyframes vedhaLeft  { from { opacity: 0.7; } to { opacity: 1; } }
    </style>
    """

    return html
