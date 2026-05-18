import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "abs_student_migration_state_year.csv"
GEO_PATH = ROOT / "data" / "au-all.geo.json"
OUT_PATH = ROOT / "data" / "abs_state_choropleth.geojson"

NAME_TO_CODE = {
    "New South Wales": "NSW",
    "Victoria": "VIC",
    "Queensland": "QLD",
    "Western Australia": "WA",
    "South Australia": "SA",
    "Tasmania": "TAS",
    "Northern Territory": "NT",
    "Australian Capital Territory": "ACT"
}

CODE_TO_NAME = {
    "NSW": "New South Wales",
    "VIC": "Victoria",
    "QLD": "Queensland",
    "WA": "Western Australia",
    "SA": "South Australia",
    "TAS": "Tasmania",
    "NT": "Northern Territory",
    "ACT": "Australian Capital Territory"
}


def flatten_coords(coords):
    """Flatten Polygon/MultiPolygon coordinate arrays into x/y pairs."""
    points = []

    def walk(item):
        if (
            isinstance(item, list)
            and len(item) == 2
            and isinstance(item[0], (int, float))
            and isinstance(item[1], (int, float))
        ):
            points.append(item)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(coords)
    return points


def bbox_center(geometry):
    points = flatten_coords(geometry["coordinates"])
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


# Read ABS migration CSV
by_state = {}

with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        state_code = row["state_code"]
        financial_year = row["financial_year"]
        year_start = financial_year[:4]

        if state_code not in by_state:
            by_state[state_code] = {}

        by_state[state_code][year_start] = {
            "financial_year": financial_year,
            "student_arrivals": int(row["student_arrivals"]),
            "student_departures": int(row["student_departures"]),
            "net_student_migration": int(row["net_student_migration"])
        }


# Read Highcharts Australia GeoJSON
with GEO_PATH.open("r", encoding="utf-8-sig") as f:
    geojson = json.load(f)

features_out = []

for feature in geojson["features"]:
    props = feature.get("properties", {})
    state_name = props.get("name")

    if state_name not in NAME_TO_CODE:
        continue

    state_code = NAME_TO_CODE[state_name]
    label_x, label_y = bbox_center(feature["geometry"])

    new_props = {
        "state_code": state_code,
        "state": CODE_TO_NAME[state_code],
        "label_x": label_x,
        "label_y": label_y
    }

    for year_start, values in by_state[state_code].items():
        new_props[f"financial_year_{year_start}"] = values["financial_year"]
        new_props[f"arrivals_{year_start}"] = values["student_arrivals"]
        new_props[f"departures_{year_start}"] = values["student_departures"]
        new_props[f"net_{year_start}"] = values["net_student_migration"]

    features_out.append({
        "type": "Feature",
        "properties": new_props,
        "geometry": feature["geometry"]
    })

output = {
    "type": "FeatureCollection",
    "features": features_out
}

with OUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False)

print(f"Created: {OUT_PATH}")
print(f"Features written: {len(features_out)}")