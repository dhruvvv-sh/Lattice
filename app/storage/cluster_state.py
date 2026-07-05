from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_ROOT = PROJECT_ROOT / "storage"
RUNTIME_STORAGE_ROOT = STORAGE_ROOT / "cluster"
SAMPLE_STORAGE_ROOT = STORAGE_ROOT / "samples"
LEGACY_STORAGE_ROOT = STORAGE_ROOT / "legacy"

DEFAULT_CLUSTER_TOPOLOGY = {
    "node-a": [
        RUNTIME_STORAGE_ROOT / "node-a" / "disk1",
        RUNTIME_STORAGE_ROOT / "node-a" / "disk2",
    ],
    "node-b": [
        RUNTIME_STORAGE_ROOT / "node-b" / "disk3",
        RUNTIME_STORAGE_ROOT / "node-b" / "disk4",
    ],
    "node-c": [
        RUNTIME_STORAGE_ROOT / "node-c" / "disk5",
        RUNTIME_STORAGE_ROOT / "node-c" / "disk6",
    ],
    "node-d": [
        RUNTIME_STORAGE_ROOT / "node-d" / "disk7",
        RUNTIME_STORAGE_ROOT / "node-d" / "disk8",
    ],
    "node-e": [
        RUNTIME_STORAGE_ROOT / "node-e" / "disk9",
        RUNTIME_STORAGE_ROOT / "node-e" / "disk10",
    ],
    "node-f": [
        RUNTIME_STORAGE_ROOT / "node-f" / "disk11",
        RUNTIME_STORAGE_ROOT / "node-f" / "disk12",
    ],
    "node-g": [
        RUNTIME_STORAGE_ROOT / "node-g" / "disk13",
        RUNTIME_STORAGE_ROOT / "node-g" / "disk14",
    ],
    "node-h": [
        RUNTIME_STORAGE_ROOT / "node-h" / "disk15",
        RUNTIME_STORAGE_ROOT / "node-h" / "disk16",
    ],
}

disk_status = {}
# will be updating the disk health status onto redis
