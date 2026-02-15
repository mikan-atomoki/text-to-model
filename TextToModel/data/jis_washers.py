"""JIS B1256 Plain washer dimensions (平ワッシャー).

All dimensions in mm.
"""

# Plain washers - normal series (並形)
# d1: inner diameter, d2: outer diameter, t: thickness
PLAIN_WASHER = {
    "M2":   {"d1": 2.2,  "d2": 5.0,  "t": 0.3},
    "M2.5": {"d1": 2.7,  "d2": 6.0,  "t": 0.5},
    "M3":   {"d1": 3.2,  "d2": 7.0,  "t": 0.5},
    "M4":   {"d1": 4.3,  "d2": 9.0,  "t": 0.8},
    "M5":   {"d1": 5.3,  "d2": 10.0, "t": 1.0},
    "M6":   {"d1": 6.4,  "d2": 12.0, "t": 1.6},
    "M8":   {"d1": 8.4,  "d2": 16.0, "t": 1.6},
    "M10":  {"d1": 10.5, "d2": 20.0, "t": 2.0},
    "M12":  {"d1": 13.0, "d2": 24.0, "t": 2.5},
}

# Plain washers - small series (小形)
PLAIN_WASHER_SMALL = {
    "M2":   {"d1": 2.2,  "d2": 4.0,  "t": 0.3},
    "M2.5": {"d1": 2.7,  "d2": 5.0,  "t": 0.5},
    "M3":   {"d1": 3.2,  "d2": 6.0,  "t": 0.5},
    "M4":   {"d1": 4.3,  "d2": 8.0,  "t": 0.5},
    "M5":   {"d1": 5.3,  "d2": 9.0,  "t": 1.0},
    "M6":   {"d1": 6.4,  "d2": 11.0, "t": 1.6},
    "M8":   {"d1": 8.4,  "d2": 15.0, "t": 1.6},
    "M10":  {"d1": 10.5, "d2": 18.0, "t": 1.6},
    "M12":  {"d1": 13.0, "d2": 20.0, "t": 2.0},
}

# Spring washers (ばね座金) JIS B1251
SPRING_WASHER = {
    "M2":   {"d1": 2.1,  "d2": 4.4,  "t": 0.5, "h": 0.5},
    "M2.5": {"d1": 2.6,  "d2": 5.1,  "t": 0.6, "h": 0.6},
    "M3":   {"d1": 3.1,  "d2": 6.2,  "t": 0.8, "h": 0.8},
    "M4":   {"d1": 4.1,  "d2": 7.6,  "t": 0.9, "h": 0.9},
    "M5":   {"d1": 5.1,  "d2": 9.2,  "t": 1.2, "h": 1.2},
    "M6":   {"d1": 6.1,  "d2": 11.8, "t": 1.6, "h": 1.6},
    "M8":   {"d1": 8.2,  "d2": 14.8, "t": 2.0, "h": 2.0},
    "M10":  {"d1": 10.2, "d2": 18.1, "t": 2.2, "h": 2.2},
    "M12":  {"d1": 12.2, "d2": 21.1, "t": 2.5, "h": 2.5},
}


def get_washer(size, series="normal"):
    """Get plain washer dimensions.

    Args:
        size: 'M2' through 'M12'.
        series: 'normal' (並形), 'small' (小形), or 'spring' (ばね座金).

    Returns:
        Dict with d1, d2, t keys (and h for spring washers).
    """
    size = size.upper()
    tables = {
        "normal": PLAIN_WASHER,
        "small": PLAIN_WASHER_SMALL,
        "spring": SPRING_WASHER,
    }
    table = tables.get(series)
    if table is None:
        raise ValueError("Unknown washer series: '{}'. Use: normal, small, spring".format(series))

    dims = table.get(size)
    if dims is None:
        raise ValueError("Washer size '{}' ({}) not found. Available: {}".format(
            size, series, ", ".join(sorted(table.keys()))))
    return dims
