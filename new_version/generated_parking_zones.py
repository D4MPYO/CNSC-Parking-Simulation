# CNSC PARKING MAP LAYOUT
# Based on visual layout from Parking Zone Editor
# CAPACITY MANUALLY SET: MC=140, Cars=81, Trucks=10 (Total: 231)

# PARKING ZONES - Capacity values are FIXED, do not auto-calculate!
PARKING_ZONES = [
    # TRUCK ZONE: 10 total
    {"name": "Truck 1", "x": 1530, "y": 60, "width": 180, "height": 90, "capacity": 10, "zone_type": "truck"},

    # MOTORCYCLE ZONES: 140 total (split across 8 zones)
    {"name": "MC 1", "x": 300, "y": 300, "width": 210, "height": 60, "capacity": 18, "zone_type": "motorcycle"},
    {"name": "MC 2", "x": 300, "y": 390, "width": 210, "height": 60, "capacity": 18, "zone_type": "motorcycle"},
    {"name": "MC 3", "x": 300, "y": 660, "width": 210, "height": 60, "capacity": 18, "zone_type": "motorcycle"},
    {"name": "MC 4", "x": 300, "y": 750, "width": 210, "height": 60, "capacity": 18, "zone_type": "motorcycle"},
    {"name": "MC 5", "x": 1680, "y": 330, "width": 30, "height": 150, "capacity": 17, "zone_type": "motorcycle"},
    {"name": "MC 6", "x": 1650, "y": 810, "width": 180, "height": 30, "capacity": 17, "zone_type": "motorcycle"},
    {"name": "MC 7", "x": 1650, "y": 1170, "width": 30, "height": 270, "capacity": 17, "zone_type": "motorcycle"},
    {"name": "MC 8", "x": 185, "y": 935, "width": 35, "height": 165, "capacity": 17, "zone_type": "motorcycle"},

    # CAR ZONES: 81 total (split across 4 zones)
    {"name": "Cars 1", "x": 630, "y": 240, "width": 840, "height": 30, "capacity": 25, "zone_type": "car"},
    {"name": "Cars 2", "x": 630, "y": 840, "width": 840, "height": 30, "capacity": 25, "zone_type": "car"},
    {"name": "Cars 3", "x": 1680, "y": 240, "width": 150, "height": 30, "capacity": 16, "zone_type": "car"},
    {"name": "Cars 4", "x": 1650, "y": 870, "width": 30, "height": 180, "capacity": 15, "zone_type": "car"},
]

# BUILDINGS
BUILDINGS = [
    ("Bldg 1", 210, 60, 210, 90),
    ("Bldg 2", 450, 60, 210, 90),
    ("Bldg 3", 720, 60, 510, 90),
    ("Bldg 4", 1290, 60, 180, 90),
    ("Bldg 5", 1770, 60, 180, 90),
    ("Bldg 6", 180, 300, 90, 510),
    ("Bldg 8", 240, 480, 90, 150),
    ("Bldg 9", 630, 360, 120, 390),
    ("Bldg 12", 780, 420, 120, 300),
    ("Bldg 15", 930, 630, 60, 60),
    ("Bldg 13", 930, 420, 60, 60),
    ("Bldg 16", 1050, 420, 60, 60),
    ("Bldg 17", 1050, 630, 60, 60),
    ("Bldg 14", 990, 510, 60, 90),
    ("Bldg 18", 900, 300, 240, 60),
    ("Bldg 19", 1140, 300, 240, 60),
    ("Bldg 20", 1380, 300, 90, 60),
    ("Bldg 10", 630, 300, 270, 60),
    ("Bldg 11", 630, 750, 300, 60),
    ("Bldg 23", 1140, 390, 90, 330),
    ("Bldg 24", 1260, 480, 60, 240),
    ("Bldg 25", 1260, 390, 90, 60),
    ("Bldg 26", 1350, 450, 180, 240),
    ("Bldg 22", 930, 750, 300, 60),
    ("Bldg 27", 1230, 750, 300, 60),
    ("Bldg 28", 1680, 270, 300, 60),
    ("Bldg 31", 1740, 330, 150, 150),
    ("Bldg 30", 1680, 480, 210, 90),
    ("Bldg 29", 1890, 330, 90, 240),
    ("Bldg 32", 1650, 630, 180, 180),
    ("Bldg 33", 1890, 660, 90, 150),
    ("Bldg 35", 1680, 870, 300, 180),
    ("Bldg 36", 1680, 1140, 300, 330),
    ("Bldg 38", 330, 935, 220, 110),
    ("Bldg 39", 550, 935, 275, 110),
    ("Bldg 40", 825, 935, 715, 110),
    ("Bldg 37", 225, 935, 105, 220),
]

# ROADS
ROADS = [
    {"name": "Road 5", "x": 540, "y": 180, "width": 60, "height": 750},
    {"name": "Road 6", "x": 1560, "y": 180, "width": 60, "height": 1320},
    {"name": "Road 2", "x": 180, "y": 180, "width": 1800, "height": 60},
    {"name": "Road 7", "x": 180, "y": 870, "width": 1440, "height": 60},
]

# SUMMARY (MANUALLY SET - DO NOT AUTO-CALCULATE):
# Motorcycles: 140 slots (18+18+18+18+17+17+17+17)
# Cars: 81 slots (25+25+16+15)
# Trucks: 10 slots
# Total Parking: 231 slots
# Buildings: 37
# Roads: 4
#
# Gates: ENTRY=(200, 900), EXIT=(200, 210)

ENTRY_GATE = (200, 900)
EXIT_GATE = (200, 210)