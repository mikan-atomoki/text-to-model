"""JIS B1301 Keyway dimensions (キー溝).

Parallel key dimensions for shafts based on shaft diameter.
All dimensions in mm.
"""

# Shaft diameter range -> key dimensions
# b: key width, h: key height, t1: shaft keyway depth, t2: hub keyway depth
KEYWAY_BY_SHAFT = {
    # shaft_d_min, shaft_d_max, b, h, t1, t2
    (6, 8):     {"b": 2,  "h": 2,  "t1": 1.2, "t2": 1.0},
    (8, 10):    {"b": 3,  "h": 3,  "t1": 1.8, "t2": 1.4},
    (10, 12):   {"b": 4,  "h": 4,  "t1": 2.5, "t2": 1.8},
    (12, 17):   {"b": 5,  "h": 5,  "t1": 3.0, "t2": 2.3},
    (17, 22):   {"b": 6,  "h": 6,  "t1": 3.5, "t2": 2.8},
    (22, 30):   {"b": 8,  "h": 7,  "t1": 4.0, "t2": 3.3},
    (30, 38):   {"b": 10, "h": 8,  "t1": 5.0, "t2": 3.3},
    (38, 44):   {"b": 12, "h": 8,  "t1": 5.0, "t2": 3.3},
    (44, 50):   {"b": 14, "h": 9,  "t1": 5.5, "t2": 3.8},
    (50, 58):   {"b": 16, "h": 10, "t1": 6.0, "t2": 4.3},
    (58, 65):   {"b": 18, "h": 11, "t1": 7.0, "t2": 4.4},
    (65, 75):   {"b": 20, "h": 12, "t1": 7.5, "t2": 4.9},
}

# Standard key lengths (mm)
STANDARD_KEY_LENGTHS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40, 45, 50, 56, 63, 70, 80, 90, 100]


def get_keyway(shaft_diameter):
    """Get keyway dimensions for a given shaft diameter.

    Args:
        shaft_diameter: Shaft diameter in mm.

    Returns:
        Dict with b, h, t1, t2 keys.

    Raises:
        ValueError: If no keyway data for the shaft size.
    """
    for (d_min, d_max), dims in KEYWAY_BY_SHAFT.items():
        if d_min <= shaft_diameter < d_max:
            return dims

    raise ValueError(
        "No keyway data for shaft diameter {}mm. "
        "Supported range: 6-75mm.".format(shaft_diameter)
    )


def get_key_length(shaft_diameter, hub_length=None):
    """Get recommended key length.

    Args:
        shaft_diameter: Shaft diameter in mm.
        hub_length: Hub length in mm. If provided, key length = hub_length - 2mm.

    Returns:
        Recommended key length in mm (from standard lengths).
    """
    if hub_length:
        target = hub_length - 2
    else:
        target = shaft_diameter * 1.5

    # Find nearest standard length
    for length in STANDARD_KEY_LENGTHS:
        if length >= target:
            return length

    return STANDARD_KEY_LENGTHS[-1]
