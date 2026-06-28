# app/cluster/cluster_state.py

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CLUSTER_TOPOLOGY = {
    "node-a": [
        PROJECT_ROOT / "storage" / "node-a" / "disk1",
        PROJECT_ROOT / "storage" / "node-a" / "disk2",
    ],
    "node-b": [
        PROJECT_ROOT / "storage" / "node-b" / "disk3",
        PROJECT_ROOT / "storage" / "node-b" / "disk4",
    ],
    "node-c": [
        PROJECT_ROOT / "storage" / "node-c" / "disk5",
        PROJECT_ROOT / "storage" / "node-c" / "disk6",
    ],
    "node-d": [
        PROJECT_ROOT / "storage" / "node-d" / "disk7",
        PROJECT_ROOT / "storage" / "node-d" / "disk8",
    ],
    "node-e": [
        PROJECT_ROOT / "storage" / "node-e" / "disk9",
        PROJECT_ROOT / "storage" / "node-e" / "disk10",
    ],
}

disk_status = {}
# will be updating the disk health status onto redis
