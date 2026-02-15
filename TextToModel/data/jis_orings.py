"""JIS B2401 O-ring groove dimensions (Oリング溝).

P-series (cylindrical, for pistons) and G-series (cylindrical, for housings/glands).
All dimensions in mm.
"""

# P-series O-rings (for pistons/shafts - dynamic seal)
# d: O-ring inner diameter, w: O-ring cross-section diameter
P_SERIES = {
    "P3":   {"d": 2.8,   "w": 1.9},
    "P4":   {"d": 3.8,   "w": 1.9},
    "P5":   {"d": 4.8,   "w": 1.9},
    "P6":   {"d": 5.8,   "w": 1.9},
    "P7":   {"d": 6.8,   "w": 1.9},
    "P8":   {"d": 7.8,   "w": 1.9},
    "P9":   {"d": 8.8,   "w": 1.9},
    "P10":  {"d": 9.8,   "w": 1.9},
    "P10A": {"d": 9.8,   "w": 2.4},
    "P11":  {"d": 10.8,  "w": 2.4},
    "P11.2":{"d": 11.0,  "w": 2.4},
    "P12":  {"d": 11.8,  "w": 2.4},
    "P14":  {"d": 13.8,  "w": 2.4},
    "P16":  {"d": 15.8,  "w": 2.4},
    "P18":  {"d": 17.8,  "w": 2.4},
    "P20":  {"d": 19.8,  "w": 2.4},
    "P22":  {"d": 21.8,  "w": 2.4},
    "P22A": {"d": 21.8,  "w": 3.5},
    "P24":  {"d": 23.8,  "w": 3.5},
    "P25":  {"d": 24.4,  "w": 3.5},
    "P26":  {"d": 25.8,  "w": 3.5},
    "P28":  {"d": 27.8,  "w": 3.5},
    "P29":  {"d": 28.8,  "w": 3.5},
    "P30":  {"d": 29.8,  "w": 3.5},
    "P32":  {"d": 31.5,  "w": 3.5},
    "P34":  {"d": 33.5,  "w": 3.5},
    "P36":  {"d": 35.5,  "w": 3.5},
    "P38":  {"d": 37.5,  "w": 3.5},
    "P40":  {"d": 39.5,  "w": 3.5},
}

# G-series O-rings (for glands/housings - static seal)
G_SERIES = {
    "G25":  {"d": 24.4,  "w": 3.5},
    "G30":  {"d": 29.4,  "w": 3.5},
    "G35":  {"d": 34.4,  "w": 3.5},
    "G40":  {"d": 39.4,  "w": 3.5},
    "G45":  {"d": 44.4,  "w": 3.5},
    "G50":  {"d": 49.4,  "w": 3.5},
    "G55":  {"d": 54.4,  "w": 3.5},
    "G60":  {"d": 59.4,  "w": 3.5},
    "G65":  {"d": 64.4,  "w": 5.7},
    "G70":  {"d": 69.4,  "w": 5.7},
    "G75":  {"d": 74.4,  "w": 5.7},
    "G80":  {"d": 79.4,  "w": 5.7},
    "G85":  {"d": 84.4,  "w": 5.7},
    "G90":  {"d": 89.4,  "w": 5.7},
    "G95":  {"d": 94.4,  "w": 5.7},
    "G100": {"d": 99.4,  "w": 5.7},
}

# Groove dimensions based on O-ring cross-section width
# For shaft (piston) grooves and housing (gland) grooves
# groove_width: groove width, groove_depth: groove depth
GROOVE_DIMS = {
    1.9: {"groove_width": 2.1, "groove_depth_shaft": 1.35, "groove_depth_housing": 1.55},
    2.4: {"groove_width": 2.8, "groove_depth_shaft": 1.70, "groove_depth_housing": 1.95},
    3.5: {"groove_width": 4.0, "groove_depth_shaft": 2.65, "groove_depth_housing": 2.90},
    5.7: {"groove_width": 6.6, "groove_depth_shaft": 4.30, "groove_depth_housing": 4.60},
}


def get_oring(oring_number):
    """Get O-ring dimensions by number.

    Args:
        oring_number: O-ring designation (e.g., 'P10', 'G50').

    Returns:
        Dict with d (inner diameter), w (cross-section width) keys.
    """
    number = str(oring_number).upper()

    dims = P_SERIES.get(number)
    if dims:
        return dims

    dims = G_SERIES.get(number)
    if dims:
        return dims

    available_p = sorted(P_SERIES.keys())
    available_g = sorted(G_SERIES.keys())
    raise ValueError("O-ring '{}' not found. P-series: {}, G-series: {}".format(
        oring_number, ", ".join(available_p[:10]) + "...", ", ".join(available_g[:10]) + "..."))


def get_groove_dims(cross_section_width, groove_type="shaft"):
    """Get groove dimensions for an O-ring cross-section.

    Args:
        cross_section_width: O-ring cross-section width (w) in mm.
        groove_type: 'shaft' (piston) or 'housing' (gland).

    Returns:
        Dict with groove_width and groove_depth keys.
    """
    dims = GROOVE_DIMS.get(cross_section_width)
    if dims is None:
        raise ValueError("No groove data for cross-section width {}mm. "
                         "Available: {}".format(cross_section_width,
                                                 ", ".join(str(k) for k in sorted(GROOVE_DIMS.keys()))))

    depth_key = "groove_depth_shaft" if groove_type == "shaft" else "groove_depth_housing"
    return {
        "groove_width": dims["groove_width"],
        "groove_depth": dims[depth_key],
    }
