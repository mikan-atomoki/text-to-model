"""ISO Metric thread dimensions (JIS B0205 / ISO 261).

All dimensions in mm.
Keys: d (nominal diameter), p (pitch), d2 (pitch diameter), d1 (minor diameter)
"""

# Coarse pitch threads M2-M12
METRIC_COARSE = {
    "M2":   {"d": 2.0,   "p": 0.4,  "d2": 1.740,  "d1": 1.509},
    "M2.5": {"d": 2.5,   "p": 0.45, "d2": 2.208,  "d1": 1.948},
    "M3":   {"d": 3.0,   "p": 0.5,  "d2": 2.675,  "d1": 2.387},
    "M4":   {"d": 4.0,   "p": 0.7,  "d2": 3.545,  "d1": 3.141},
    "M5":   {"d": 5.0,   "p": 0.8,  "d2": 4.480,  "d1": 4.019},
    "M6":   {"d": 6.0,   "p": 1.0,  "d2": 5.350,  "d1": 4.773},
    "M8":   {"d": 8.0,   "p": 1.25, "d2": 7.188,  "d1": 6.466},
    "M10":  {"d": 10.0,  "p": 1.5,  "d2": 9.026,  "d1": 8.160},
    "M12":  {"d": 12.0,  "p": 1.75, "d2": 10.863, "d1": 9.853},
}

# Fine pitch threads M2-M12 (common fine pitches)
METRIC_FINE = {
    "M3x0.35":  {"d": 3.0,   "p": 0.35, "d2": 2.773,  "d1": 2.571},
    "M4x0.5":   {"d": 4.0,   "p": 0.5,  "d2": 3.675,  "d1": 3.387},
    "M5x0.5":   {"d": 5.0,   "p": 0.5,  "d2": 4.675,  "d1": 4.387},
    "M6x0.75":  {"d": 6.0,   "p": 0.75, "d2": 5.513,  "d1": 5.080},
    "M8x0.75":  {"d": 8.0,   "p": 0.75, "d2": 7.513,  "d1": 7.080},
    "M8x1.0":   {"d": 8.0,   "p": 1.0,  "d2": 7.350,  "d1": 6.773},
    "M10x1.0":  {"d": 10.0,  "p": 1.0,  "d2": 9.350,  "d1": 8.773},
    "M10x1.25": {"d": 10.0,  "p": 1.25, "d2": 9.188,  "d1": 8.466},
    "M12x1.0":  {"d": 12.0,  "p": 1.0,  "d2": 11.350, "d1": 10.773},
    "M12x1.25": {"d": 12.0,  "p": 1.25, "d2": 11.188, "d1": 10.466},
    "M12x1.5":  {"d": 12.0,  "p": 1.5,  "d2": 11.026, "d1": 10.160},
}


def get_thread(size, fine_pitch=None):
    """Get thread dimensions for a given size.

    Args:
        size: Thread size string like 'M6' or 'M8x1.0'.
        fine_pitch: If provided and size doesn't include pitch, use this fine pitch.

    Returns:
        Dict with d, p, d2, d1 keys.

    Raises:
        ValueError: If thread size is not found.
    """
    size = size.upper()

    # Check if fine pitch is specified in the size string
    if "X" in size and size not in METRIC_COARSE:
        thread = METRIC_FINE.get(size)
        if thread:
            return thread

    # Check if fine pitch is requested
    if fine_pitch:
        key = "{}x{}".format(size, fine_pitch)
        thread = METRIC_FINE.get(key)
        if thread:
            return thread

    # Default to coarse pitch
    thread = METRIC_COARSE.get(size)
    if thread:
        return thread

    available = sorted(list(METRIC_COARSE.keys()) + list(METRIC_FINE.keys()))
    raise ValueError("Thread size '{}' not found. Available: {}".format(size, ", ".join(available)))


def get_tap_drill(size, fine_pitch=None):
    """Get the tap drill diameter for a given thread size.

    Returns the minor diameter (d1) which is the recommended tap drill size.
    """
    thread = get_thread(size, fine_pitch)
    return thread["d1"]
