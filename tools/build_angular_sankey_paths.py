import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATHS_IN = ROOT / "data" / "country_state_sankey_paths.csv"
NODES_IN = ROOT / "data" / "country_state_sankey_nodes.csv"
OUT_PATH = ROOT / "data" / "country_state_sankey_paths_angular.csv"

source_nodes = {}
target_nodes = {}

with NODES_IN.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["side"] == "source":
            source_nodes[row["label"]] = row
        elif row["side"] == "target":
            target_nodes[row["label"]] = row

flows = {}

with PATHS_IN.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        flow_id = row["flow_id"]
        t = int(row["t"])

        if flow_id not in flows:
            flows[flow_id] = {
                "source": row["source"],
                "target": row["target"],
                "target_name": row["target_name"],
                "enrolments": row["enrolments"],
                "start": None,
                "end": None
            }

        if t == 0:
            flows[flow_id]["start"] = row

        if t == 28:
            flows[flow_id]["end"] = row

with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
    fieldnames = [
        "flow_id",
        "source",
        "target",
        "target_name",
        "enrolments",
        "t",
        "x",
        "y"
    ]

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    written = 0

    for flow_id, flow in flows.items():
        start = flow["start"]
        end = flow["end"]

        if start is None or end is None:
            continue

        source_node = source_nodes.get(flow["source"])
        target_node = target_nodes.get(flow["target_name"])

        if source_node is None or target_node is None:
            continue

        x0 = float(source_node["x1"])
        x1 = float(target_node["x0"])
        y0 = float(start["y"])
        y1 = float(end["y"])
        mid_x = (x0 + x1) / 2

        points = [
            (0, x0, y0),
            (1, mid_x, y0),
            (2, mid_x, y1),
            (3, x1, y1)
        ]

        for t, x, y in points:
            writer.writerow({
                "flow_id": flow_id,
                "source": flow["source"],
                "target": flow["target"],
                "target_name": flow["target_name"],
                "enrolments": flow["enrolments"],
                "t": t,
                "x": x,
                "y": y
            })

        written += 1

print(f"Created: {OUT_PATH}")
print(f"Flows written: {written}")