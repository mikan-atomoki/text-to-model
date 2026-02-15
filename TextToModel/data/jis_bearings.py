"""JIS B1520 Bearing bore dimensions (ベアリング穴).

Standard bearing bore dimensions for deep groove ball bearings.
All dimensions in mm.
"""

# Deep groove ball bearings (深溝玉軸受) by bore size
# d: bore diameter, D: outer diameter, B: width, r: chamfer
DEEP_GROOVE_BALL = {
    # 6000 series (light)
    "6000": {"d": 10, "D": 26,  "B": 8,  "r": 0.3},
    "6001": {"d": 12, "D": 28,  "B": 8,  "r": 0.3},
    "6002": {"d": 15, "D": 32,  "B": 9,  "r": 0.3},
    "6003": {"d": 17, "D": 35,  "B": 10, "r": 0.3},
    "6004": {"d": 20, "D": 42,  "B": 12, "r": 0.6},
    "6005": {"d": 25, "D": 47,  "B": 12, "r": 0.6},
    "6006": {"d": 30, "D": 55,  "B": 13, "r": 1.0},
    "6007": {"d": 35, "D": 62,  "B": 14, "r": 1.0},
    "6008": {"d": 40, "D": 68,  "B": 15, "r": 1.0},
    "6009": {"d": 45, "D": 75,  "B": 16, "r": 1.0},
    "6010": {"d": 50, "D": 80,  "B": 16, "r": 1.0},
    # 6200 series (medium)
    "6200": {"d": 10, "D": 30,  "B": 9,  "r": 0.6},
    "6201": {"d": 12, "D": 32,  "B": 10, "r": 0.6},
    "6202": {"d": 15, "D": 35,  "B": 11, "r": 0.6},
    "6203": {"d": 17, "D": 40,  "B": 12, "r": 0.6},
    "6204": {"d": 20, "D": 47,  "B": 14, "r": 1.0},
    "6205": {"d": 25, "D": 52,  "B": 15, "r": 1.0},
    "6206": {"d": 30, "D": 62,  "B": 16, "r": 1.0},
    "6207": {"d": 35, "D": 72,  "B": 17, "r": 1.1},
    "6208": {"d": 40, "D": 80,  "B": 18, "r": 1.1},
    "6209": {"d": 45, "D": 85,  "B": 19, "r": 1.1},
    "6210": {"d": 50, "D": 90,  "B": 20, "r": 1.1},
    # 6300 series (heavy)
    "6300": {"d": 10, "D": 35,  "B": 11, "r": 0.6},
    "6301": {"d": 12, "D": 37,  "B": 12, "r": 1.0},
    "6302": {"d": 15, "D": 42,  "B": 13, "r": 1.0},
    "6303": {"d": 17, "D": 47,  "B": 14, "r": 1.0},
    "6304": {"d": 20, "D": 52,  "B": 15, "r": 1.1},
    "6305": {"d": 25, "D": 62,  "B": 17, "r": 1.1},
    "6306": {"d": 30, "D": 72,  "B": 19, "r": 1.1},
}

# Bearing fit tolerances (shaft)
# H7 tolerance for bearing housing, k6/m6 for shaft
FIT_TOLERANCES = {
    # bore_d: {shaft_tolerance_class: (deviation_low, deviation_high)}
    10: {"k6": (0.001, 0.010), "m6": (0.004, 0.013), "j6": (-0.003, 0.006)},
    12: {"k6": (0.001, 0.012), "m6": (0.004, 0.015), "j6": (-0.004, 0.007)},
    15: {"k6": (0.001, 0.012), "m6": (0.004, 0.015), "j6": (-0.004, 0.007)},
    17: {"k6": (0.001, 0.012), "m6": (0.004, 0.015), "j6": (-0.004, 0.007)},
    20: {"k6": (0.002, 0.015), "m6": (0.005, 0.018), "j6": (-0.005, 0.008)},
    25: {"k6": (0.002, 0.015), "m6": (0.005, 0.018), "j6": (-0.005, 0.008)},
    30: {"k6": (0.002, 0.018), "m6": (0.006, 0.022), "j6": (-0.005, 0.009)},
    35: {"k6": (0.002, 0.018), "m6": (0.006, 0.022), "j6": (-0.005, 0.009)},
    40: {"k6": (0.003, 0.021), "m6": (0.007, 0.025), "j6": (-0.006, 0.010)},
    45: {"k6": (0.003, 0.021), "m6": (0.007, 0.025), "j6": (-0.006, 0.010)},
    50: {"k6": (0.003, 0.021), "m6": (0.007, 0.025), "j6": (-0.006, 0.010)},
}


def get_bearing(bearing_number):
    """Get bearing dimensions by bearing number.

    Args:
        bearing_number: Standard bearing number (e.g., '6204', '6305').

    Returns:
        Dict with d, D, B, r keys.
    """
    dims = DEEP_GROOVE_BALL.get(str(bearing_number))
    if dims is None:
        raise ValueError("Bearing '{}' not found. Available: {}".format(
            bearing_number,
            ", ".join(sorted(DEEP_GROOVE_BALL.keys()))
        ))
    return dims


def get_bearing_by_bore(bore_diameter, series="6200"):
    """Find a bearing by bore diameter and series.

    Args:
        bore_diameter: Bore diameter in mm.
        series: Series prefix ('6000', '6200', '6300').

    Returns:
        Tuple of (bearing_number, dimensions dict).
    """
    for num, dims in DEEP_GROOVE_BALL.items():
        if num.startswith(series[:2]) and dims["d"] == bore_diameter:
            return num, dims

    raise ValueError("No {} series bearing with bore {}mm.".format(series, bore_diameter))
