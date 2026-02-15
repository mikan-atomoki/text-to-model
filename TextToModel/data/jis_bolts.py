"""JIS bolt dimensions.

B1176: Socket head cap screws (六角穴付きボルト)
B1180: Hexagon head bolts (六角ボルト)

All dimensions in mm.
"""

# JIS B1176 Socket Head Cap Screws (六角穴付きボルト)
# dk: head diameter, k: head height, s: hex socket size
SOCKET_HEAD_CAP = {
    "M2":   {"dk": 3.8,  "k": 2.0,  "s": 1.5},
    "M2.5": {"dk": 4.5,  "k": 2.5,  "s": 2.0},
    "M3":   {"dk": 5.5,  "k": 3.0,  "s": 2.5},
    "M4":   {"dk": 7.0,  "k": 4.0,  "s": 3.0},
    "M5":   {"dk": 8.5,  "k": 5.0,  "s": 4.0},
    "M6":   {"dk": 10.0, "k": 6.0,  "s": 5.0},
    "M8":   {"dk": 13.0, "k": 8.0,  "s": 6.0},
    "M10":  {"dk": 16.0, "k": 10.0, "s": 8.0},
    "M12":  {"dk": 18.0, "k": 12.0, "s": 10.0},
}

# JIS B1180 Hexagon Head Bolts (六角ボルト)
# s: width across flats, e: width across corners, k: head height
HEXAGON_HEAD = {
    "M2":   {"s": 4.0,   "e": 4.62,  "k": 1.4},
    "M2.5": {"s": 5.0,   "e": 5.77,  "k": 1.7},
    "M3":   {"s": 5.5,   "e": 6.35,  "k": 2.0},
    "M4":   {"s": 7.0,   "e": 8.08,  "k": 2.8},
    "M5":   {"s": 8.0,   "e": 9.24,  "k": 3.5},
    "M6":   {"s": 10.0,  "e": 11.55, "k": 4.0},
    "M8":   {"s": 13.0,  "e": 15.01, "k": 5.3},
    "M10":  {"s": 16.0,  "e": 18.48, "k": 6.4},
    "M12":  {"s": 18.0,  "e": 20.78, "k": 7.5},
}

# Standard bolt lengths (mm) for each size
STANDARD_LENGTHS = {
    "M2":   [4, 5, 6, 8, 10, 12, 16, 20],
    "M2.5": [5, 6, 8, 10, 12, 16, 20, 25],
    "M3":   [5, 6, 8, 10, 12, 16, 20, 25, 30],
    "M4":   [6, 8, 10, 12, 16, 20, 25, 30, 35, 40],
    "M5":   [8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50],
    "M6":   [10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60],
    "M8":   [12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80],
    "M10":  [16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 100],
    "M12":  [20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 100, 110, 120],
}


def get_socket_head(size):
    """Get socket head cap screw dimensions.

    Args:
        size: 'M2' through 'M12'.

    Returns:
        Dict with dk, k, s keys.
    """
    size = size.upper()
    dims = SOCKET_HEAD_CAP.get(size)
    if dims is None:
        raise ValueError("Socket head cap screw size '{}' not found. Available: {}".format(
            size, ", ".join(sorted(SOCKET_HEAD_CAP.keys()))))
    return dims


def get_hex_head(size):
    """Get hexagon head bolt dimensions.

    Args:
        size: 'M2' through 'M12'.

    Returns:
        Dict with s, e, k keys.
    """
    size = size.upper()
    dims = HEXAGON_HEAD.get(size)
    if dims is None:
        raise ValueError("Hex head bolt size '{}' not found. Available: {}".format(
            size, ", ".join(sorted(HEXAGON_HEAD.keys()))))
    return dims
