"""
Two original, fictional schematic maps for topographical route-planning
practice, plus the scenarios (start/end pairs) built on each one. Not real
London geography or any licensed map data — see app/models.py's RouteMap
docstring for why.

Seeded the same idempotent way as the question bank: app.seed.run_seed()
adds any map/scenario not already present by slug, and never duplicates or
overwrites existing ones.
"""

ROUTE_MAPS = [
    {
        "slug": "training-map-1",
        "name": "Training Map 1",
        "data": {
            "nodes": {
                "N1": {"label": "Market Square", "x": 60, "y": 60},
                "N2": {"label": "Church Lane Junction", "x": 220, "y": 60},
                "N3": {"label": "Clock Tower", "x": 380, "y": 60},
                "N4": {"label": "Riverside Junction", "x": 60, "y": 200},
                "N5": {"label": "Town Hall", "x": 220, "y": 200},
                "N6": {"label": "Bridge Street Junction", "x": 380, "y": 200},
                "N7": {"label": "Station Approach", "x": 60, "y": 340},
                "N8": {"label": "Library Junction", "x": 220, "y": 340},
                "N9": {"label": "Park Gate", "x": 380, "y": 340},
                "N10": {"label": "Old Mill Roundabout", "x": 520, "y": 200},
            },
            "edges": [
                {"from": "N1", "to": "N2", "name": "High Street (west)"},
                {"from": "N2", "to": "N3", "name": "High Street (east)"},
                {"from": "N1", "to": "N4", "name": "Market Street"},
                {"from": "N2", "to": "N5", "name": "Church Lane", "oneway": "forward"},
                {"from": "N3", "to": "N6", "name": "Bridge Road"},
                {"from": "N4", "to": "N5", "name": "Riverside Walk"},
                {"from": "N5", "to": "N6", "name": "Town Hall Street", "oneway": "forward"},
                {"from": "N4", "to": "N7", "name": "Station Road (north)"},
                {"from": "N5", "to": "N8", "name": "Library Lane"},
                {"from": "N6", "to": "N9", "name": "Park Road"},
                {"from": "N6", "to": "N10", "name": "Mill Lane"},
                {"from": "N7", "to": "N8", "name": "Station Road (south)", "oneway": "forward"},
                {"from": "N8", "to": "N9", "name": "Garden Row"},
                {"from": "N9", "to": "N10", "name": "Mill Approach"},
                {"from": "N3", "to": "N10", "name": "Old Mill Road"},
            ],
        },
        "scenarios": [
            {
                "start": "N10", "end": "N1",
                "prompt": "Plan the most direct legal route from Old Mill Roundabout to Market Square.",
            },
            {
                "start": "N1", "end": "N9",
                "prompt": "Plan the most direct legal route from Market Square to Park Gate.",
            },
            {
                "start": "N7", "end": "N2",
                "prompt": "Plan the most direct legal route from Station Approach to Church Lane Junction. Watch the direction of the one-way streets.",
            },
            {
                "start": "N3", "end": "N7",
                "prompt": "Plan the most direct legal route from Clock Tower to Station Approach. Two different one-way streets block the obvious-looking short cuts — look carefully at their direction.",
            },
        ],
    },
    {
        "slug": "training-map-2",
        "name": "Training Map 2",
        "data": {
            "nodes": {
                "M1": {"label": "North Gate", "x": 60, "y": 40},
                "M2": {"label": "Cathedral Square", "x": 220, "y": 40},
                "M3": {"label": "East Cross", "x": 380, "y": 40},
                "M4": {"label": "Canal Junction", "x": 60, "y": 160},
                "M5": {"label": "Guildhall", "x": 220, "y": 160},
                "M6": {"label": "Dockside Junction", "x": 380, "y": 160},
                "M7": {"label": "West Terminus", "x": 60, "y": 280},
                "M8": {"label": "Museum Corner", "x": 220, "y": 280},
                "M9": {"label": "Harbour Gate", "x": 380, "y": 280},
                "M10": {"label": "Ring Road Roundabout", "x": 500, "y": 160},
            },
            "edges": [
                {"from": "M1", "to": "M2", "name": "Castle Street"},
                {"from": "M2", "to": "M3", "name": "Minster Road"},
                {"from": "M1", "to": "M4", "name": "Canal Road"},
                {"from": "M2", "to": "M5", "name": "Guildhall Lane", "oneway": "forward"},
                {"from": "M3", "to": "M6", "name": "Dock Approach"},
                {"from": "M4", "to": "M5", "name": "Towpath"},
                {"from": "M5", "to": "M6", "name": "Harbour Street", "oneway": "forward"},
                {"from": "M4", "to": "M7", "name": "Terminus Road"},
                {"from": "M5", "to": "M8", "name": "Museum Lane"},
                {"from": "M6", "to": "M9", "name": "Harbour Road"},
                {"from": "M6", "to": "M10", "name": "Ring Road Link"},
                {"from": "M7", "to": "M8", "name": "Quay Walk", "oneway": "forward"},
                {"from": "M8", "to": "M9", "name": "Promenade"},
                {"from": "M9", "to": "M10", "name": "Ring Road East"},
                {"from": "M3", "to": "M10", "name": "Outer Ring"},
            ],
        },
        "scenarios": [
            {
                "start": "M10", "end": "M1",
                "prompt": "Plan the most direct legal route from Ring Road Roundabout to North Gate.",
            },
            {
                "start": "M1", "end": "M9",
                "prompt": "Plan the most direct legal route from North Gate to Harbour Gate.",
            },
            {
                "start": "M7", "end": "M2",
                "prompt": "Plan the most direct legal route from West Terminus to Cathedral Square. Watch the direction of the one-way streets.",
            },
            {
                "start": "M3", "end": "M7",
                "prompt": "Plan the most direct legal route from East Cross to West Terminus. Two different one-way streets block the obvious-looking short cuts — look carefully at their direction.",
            },
        ],
    },
    {
        "slug": "training-map-3",
        "name": "Training Map 3",
        "data": {
            "nodes": {
                "K1": {"label": "North Depot", "x": 60, "y": 40},
                "K2": {"label": "Crossroads", "x": 220, "y": 40},
                "K3": {"label": "East Yard", "x": 380, "y": 40},
                "K4": {"label": "Canal Bridge", "x": 60, "y": 160},
                "K5": {"label": "Market Hall", "x": 220, "y": 160},
                "K6": {"label": "Wharf Junction", "x": 380, "y": 160},
                "K7": {"label": "South Gate", "x": 60, "y": 280},
                "K8": {"label": "Clocktower Square", "x": 220, "y": 280},
                "K9": {"label": "Industrial Gate", "x": 380, "y": 280},
                "K10": {"label": "Ring Junction", "x": 500, "y": 160},
            },
            "edges": [
                {"from": "K1", "to": "K2", "name": "Depot Road"},
                {"from": "K2", "to": "K3", "name": "Crossroads Lane"},
                {"from": "K1", "to": "K4", "name": "Canal Street"},
                {"from": "K2", "to": "K5", "name": "Market Approach", "oneway": "forward"},
                {"from": "K3", "to": "K6", "name": "Yard Road"},
                {"from": "K4", "to": "K5", "name": "Bridge Lane"},
                {"from": "K5", "to": "K6", "name": "Wharf Street", "oneway": "forward"},
                {"from": "K4", "to": "K7", "name": "South Canal Road"},
                {"from": "K5", "to": "K8", "name": "Clocktower Lane"},
                {"from": "K6", "to": "K9", "name": "Industrial Road"},
                {"from": "K6", "to": "K10", "name": "Ring Link"},
                {"from": "K7", "to": "K8", "name": "Gate Row", "oneway": "forward"},
                {"from": "K8", "to": "K9", "name": "Square Walk"},
                {"from": "K9", "to": "K10", "name": "Ring Approach"},
                {"from": "K3", "to": "K10", "name": "Outer Loop"},
            ],
        },
        "scenarios": [
            {
                "start": "K10", "end": "K1",
                "prompt": "Plan the most direct legal route from Ring Junction to North Depot.",
            },
            {
                "start": "K1", "end": "K9",
                "prompt": "Plan the most direct legal route from North Depot to Industrial Gate.",
            },
            {
                "start": "K7", "end": "K2",
                "prompt": "Plan the most direct legal route from South Gate to Crossroads. Watch the direction of the one-way streets.",
            },
            {
                "start": "K3", "end": "K7",
                "prompt": "Plan the most direct legal route from East Yard to South Gate. Two different one-way streets block the obvious-looking short cuts — look carefully at their direction.",
            },
        ],
    },
    {
        "slug": "training-map-4",
        "name": "Training Map 4",
        "data": {
            "nodes": {
                "L1": {"label": "North Yard", "x": 60, "y": 40},
                "L2": {"label": "Five Ways", "x": 220, "y": 40},
                "L3": {"label": "Eastfield", "x": 380, "y": 40},
                "L4": {"label": "Lockside", "x": 60, "y": 160},
                "L5": {"label": "Exchange Hall", "x": 220, "y": 160},
                "L6": {"label": "Dock Junction", "x": 380, "y": 160},
                "L7": {"label": "South Point", "x": 60, "y": 280},
                "L8": {"label": "Fountain Square", "x": 220, "y": 280},
                "L9": {"label": "Harbour Gate", "x": 380, "y": 280},
                "L10": {"label": "Outer Junction", "x": 500, "y": 160},
            },
            "edges": [
                {"from": "L1", "to": "L2", "name": "Yard Road"},
                {"from": "L2", "to": "L3", "name": "Five Ways Lane"},
                {"from": "L1", "to": "L4", "name": "Lockside Street"},
                {"from": "L2", "to": "L5", "name": "Exchange Approach", "oneway": "forward"},
                {"from": "L3", "to": "L6", "name": "Dock Road"},
                {"from": "L4", "to": "L5", "name": "Lock Lane"},
                {"from": "L5", "to": "L6", "name": "Exchange Street", "oneway": "forward"},
                {"from": "L4", "to": "L7", "name": "South Lock Road"},
                {"from": "L5", "to": "L8", "name": "Fountain Lane"},
                {"from": "L6", "to": "L9", "name": "Harbour Road"},
                {"from": "L6", "to": "L10", "name": "Outer Link"},
                {"from": "L7", "to": "L8", "name": "Point Row", "oneway": "forward"},
                {"from": "L8", "to": "L9", "name": "Square Walk"},
                {"from": "L9", "to": "L10", "name": "Outer Approach"},
                {"from": "L3", "to": "L10", "name": "Outer Bypass"},
            ],
        },
        "scenarios": [
            {
                "start": "L10", "end": "L1",
                "prompt": "Plan the most direct legal route from Outer Junction to North Yard.",
            },
            {
                "start": "L1", "end": "L9",
                "prompt": "Plan the most direct legal route from North Yard to Harbour Gate.",
            },
            {
                "start": "L7", "end": "L2",
                "prompt": "Plan the most direct legal route from South Point to Five Ways. Watch the direction of the one-way streets.",
            },
            {
                "start": "L3", "end": "L7",
                "prompt": "Plan the most direct legal route from Eastfield to South Point. Two different one-way streets block the obvious-looking short cuts — look carefully at their direction.",
            },
        ],
    },
]
