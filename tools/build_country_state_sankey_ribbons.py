import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

FLOWS_FILE = DATA_DIR / "country_state_flows.csv"
NODES_FILE = DATA_DIR / "country_state_sankey_nodes.csv"
OUTPUT_FILE = DATA_DIR / "country_state_sankey_ribbons.csv"

N_POINTS = 40
X_START = -0.015
X_END = 1.015


def smoothstep(t):
    return t * t * (3 - 2 * t)


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


flows = read_csv(FLOWS_FILE)
nodes = read_csv(NODES_FILE)

source_nodes = [r for r in nodes if r["side"] == "source"]
target_nodes = [r for r in nodes if r["side"] == "target"]

source_order = [r["label"] for r in source_nodes]
target_order = [r["state_code"] for r in target_nodes]

source_index = {name: i for i, name in enumerate(source_order)}
target_index = {code: i for i, code in enumerate(target_order)}

source_node_map = {r["label"]: r for r in source_nodes}
target_node_map = {r["state_code"]: r for r in target_nodes}

for row in flows:
    row["enrolments"] = int(row["enrolments"])

# Source-side ribbon intervals
flows_by_source = {name: [] for name in source_order}

for row in flows:
    flows_by_source[row["source"]].append(row)

for source in flows_by_source:
    flows_by_source[source].sort(key=lambda r: target_index[r["target"]])

source_intervals = {}

for source, group in flows_by_source.items():
    node = source_node_map[source]
    y0 = float(node["y0"])
    y1 = float(node["y1"])
    total = float(node["total"])
    height = y1 - y0

    current = y0

    for row in group:
        flow_height = height * (row["enrolments"] / total)
        top = current
        bottom = current + flow_height

        flow_id = f"{row['source']} to {row['target']}"
        source_intervals[flow_id] = (top, bottom)

        current = bottom

# Target-side ribbon intervals
flows_by_target = {code: [] for code in target_order}

for row in flows:
    flows_by_target[row["target"]].append(row)

for target in flows_by_target:
    flows_by_target[target].sort(key=lambda r: source_index[r["source"]])

target_intervals = {}

for target, group in flows_by_target.items():
    node = target_node_map[target]
    y0 = float(node["y0"])
    y1 = float(node["y1"])
    total = float(node["total"])
    height = y1 - y0

    current = y0

    for row in group:
        flow_height = height * (row["enrolments"] / total)
        top = current
        bottom = current + flow_height

        flow_id = f"{row['source']} to {row['target']}"
        target_intervals[flow_id] = (top, bottom)

        current = bottom

# Build ribbon boundary rows
ribbon_rows = []

for row in flows:
    flow_id = f"{row['source']} to {row['target']}"

    source_top, source_bottom = source_intervals[flow_id]
    target_top, target_bottom = target_intervals[flow_id]

    for i in range(N_POINTS):
        t = i / (N_POINTS - 1)
        eased = smoothstep(t)

        x = X_START + (X_END - X_START) * t
        y_top = source_top * (1 - eased) + target_top * eased
        y_bottom = source_bottom * (1 - eased) + target_bottom * eased

        ribbon_rows.append({
            "flow_id": flow_id,
            "source": row["source"],
            "target": row["target"],
            "target_name": row["target_name"],
            "enrolments": row["enrolments"],
            "t": i,
            "x": round(x, 6),
            "y_top": round(y_top, 6),
            "y_bottom": round(y_bottom, 6)
        })

write_csv(
    OUTPUT_FILE,
    ribbon_rows,
    [
        "flow_id",
        "source",
        "target",
        "target_name",
        "enrolments",
        "t",
        "x",
        "y_top",
        "y_bottom"
    ]
)

print(f"Created: {OUTPUT_FILE}")
print(f"Rows written: {len(ribbon_rows)}")