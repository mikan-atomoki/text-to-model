"""JIS B1111 Machine screw dimensions (小ねじ).

All dimensions in mm.
"""

# Pan head screws (なべ小ねじ) JIS B1111
# dk: head diameter, k: head height, t: slot depth
PAN_HEAD = {
    "M2":   {"dk": 4.0,  "k": 1.3, "t": 0.6},
    "M2.5": {"dk": 5.0,  "k": 1.6, "t": 0.8},
    "M3":   {"dk": 6.0,  "k": 2.0, "t": 0.9},
    "M4":   {"dk": 8.0,  "k": 2.6, "t": 1.2},
    "M5":   {"dk": 10.0, "k": 3.3, "t": 1.5},
    "M6":   {"dk": 12.0, "k": 3.9, "t": 1.8},
    "M8":   {"dk": 16.0, "k": 5.0, "t": 2.4},
    "M10":  {"dk": 20.0, "k": 6.0, "t": 3.0},
}

# Flat head (countersunk) screws (皿小ねじ) JIS B1111
# dk: head diameter, k: head height (countersink depth), t: slot depth
FLAT_HEAD = {
    "M2":   {"dk": 3.8,  "k": 1.2, "t": 0.5, "angle": 90},
    "M2.5": {"dk": 4.7,  "k": 1.5, "t": 0.7, "angle": 90},
    "M3":   {"dk": 5.6,  "k": 1.65,"t": 0.8, "angle": 90},
    "M4":   {"dk": 7.5,  "k": 2.2, "t": 1.0, "angle": 90},
    "M5":   {"dk": 9.2,  "k": 2.5, "t": 1.2, "angle": 90},
    "M6":   {"dk": 11.0, "k": 3.0, "t": 1.4, "angle": 90},
    "M8":   {"dk": 14.5, "k": 4.0, "t": 2.0, "angle": 90},
    "M10":  {"dk": 18.0, "k": 5.0, "t": 2.4, "angle": 90},
}

# Standard screw lengths (mm)
STANDARD_LENGTHS = {
    "M2":   [3, 4, 5, 6, 8, 10, 12, 16, 20],
    "M2.5": [4, 5, 6, 8, 10, 12, 16, 20, 25],
    "M3":   [5, 6, 8, 10, 12, 16, 20, 25, 30],
    "M4":   [6, 8, 10, 12, 16, 20, 25, 30, 35, 40],
    "M5":   [8, 10, 12, 16, 20, 25, 30, 35, 40],
    "M6":   [10, 12, 16, 20, 25, 30, 35, 40, 50],
    "M8":   [12, 16, 20, 25, 30, 35, 40, 50, 60],
    "M10":  [16, 20, 25, 30, 35, 40, 50, 60, 70, 80],
}


def get_pan_head(size):
    """Get pan head screw dimensions.

    Args:
        size: 'M2' through 'M10'.

    Returns:
        Dict with dk, k, t keys.
    """
    size = size.upper()
    dims = PAN_HEAD.get(size)
    if dims is None:
        raise ValueError("Pan head screw size '{}' not found. Available: {}".format(
            size, ", ".join(sorted(PAN_HEAD.keys()))))
    return dims


def get_flat_head(size):
    """Get flat head (countersunk) screw dimensions.

    Args:
        size: 'M2' through 'M10'.

    Returns:
        Dict with dk, k, t, angle keys.
    """
    size = size.upper()
    dims = FLAT_HEAD.get(size)
    if dims is None:
        raise ValueError("Flat head screw size '{}' not found. Available: {}".format(
            size, ", ".join(sorted(FLAT_HEAD.keys()))))
    return dims
