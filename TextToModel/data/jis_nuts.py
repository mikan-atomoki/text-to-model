"""JIS B1181 Hexagon nut dimensions (六角ナット).

All dimensions in mm.
"""

# Style 1 hexagon nuts (Type 1)
# s: width across flats, e: width across corners, m: height
HEXAGON_NUT_STYLE1 = {
    "M2":   {"s": 4.0,  "e": 4.62,  "m": 1.6},
    "M2.5": {"s": 5.0,  "e": 5.77,  "m": 2.0},
    "M3":   {"s": 5.5,  "e": 6.35,  "m": 2.4},
    "M4":   {"s": 7.0,  "e": 8.08,  "m": 3.2},
    "M5":   {"s": 8.0,  "e": 9.24,  "m": 4.7},
    "M6":   {"s": 10.0, "e": 11.55, "m": 5.2},
    "M8":   {"s": 13.0, "e": 15.01, "m": 6.8},
    "M10":  {"s": 16.0, "e": 18.48, "m": 8.4},
    "M12":  {"s": 18.0, "e": 20.78, "m": 10.8},
}

# Thin hexagon nuts (低ナット)
# s: width across flats, e: width across corners, m: height
HEXAGON_NUT_THIN = {
    "M2":   {"s": 4.0,  "e": 4.62,  "m": 1.2},
    "M2.5": {"s": 5.0,  "e": 5.77,  "m": 1.6},
    "M3":   {"s": 5.5,  "e": 6.35,  "m": 1.8},
    "M4":   {"s": 7.0,  "e": 8.08,  "m": 2.2},
    "M5":   {"s": 8.0,  "e": 9.24,  "m": 2.7},
    "M6":   {"s": 10.0, "e": 11.55, "m": 3.2},
    "M8":   {"s": 13.0, "e": 15.01, "m": 4.0},
    "M10":  {"s": 16.0, "e": 18.48, "m": 5.0},
    "M12":  {"s": 18.0, "e": 20.78, "m": 6.0},
}


def get_nut(size, style="style1"):
    """Get hexagon nut dimensions.

    Args:
        size: 'M2' through 'M12'.
        style: 'style1' (standard) or 'thin' (低ナット).

    Returns:
        Dict with s, e, m keys.
    """
    size = size.upper()
    table = HEXAGON_NUT_STYLE1 if style == "style1" else HEXAGON_NUT_THIN
    dims = table.get(size)
    if dims is None:
        raise ValueError("Nut size '{}' ({}) not found. Available: {}".format(
            size, style, ", ".join(sorted(table.keys()))))
    return dims
