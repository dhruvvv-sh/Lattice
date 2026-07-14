#responsible for keeping track of the storage infrastructure
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class StorageNode:  #stores info about the machines / VM
    node_id: str
    host: str | None = None
    port: int | None = None
    online: bool = True
    healthy: bool = True
    region: str | None = None
    rack_id: str | None = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StorageTarget: #stores info about the disks on the VM's 
    node_id: str
    disk_id: str
    path: Path
    capacity: int = 0
    free_space: int = 0
    healthy: bool = True
    online: bool = True
    storage_type: str = "local"
    used_bytes: int = 0
    region: str | None = None
    rack_id: str | None = None
    latency_ms: float | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.disk_id

    @property
    def free_bytes(self) -> int:
        return self.free_space


class ClusterManager:
    def __init__(self):
        self._nodes: dict[str, StorageNode] = {}
        self._targets: dict[tuple[str, str], StorageTarget] = {}

    def register_node(
        self,
        node_id: str,
        host: str | None = None,
        port: int | None = None,
        region: str | None = None,
        rack_id: str | None = None,
    ) -> StorageNode:
        node = StorageNode(
            node_id=node_id,
            host=host,
            port=port,
            region=region,
            rack_id=rack_id,
        )
        self._nodes[node_id] = node
        return node

    def remove_node(self, node_id: str):
        self._nodes.pop(node_id, None)
        for target_key in list(self._targets):
            if target_key[0] == node_id:
                self._targets.pop(target_key)

    def mark_node(
        self,
        node_id: str,
        healthy: bool | None = None,
        online: bool | None = None,
    ):
        node = self._nodes[node_id]

        if healthy is not None:
            node.healthy = healthy
        if online is not None:
            node.online = online

        node.last_seen = datetime.now(timezone.utc)

    def register_storage_target(
        self,
        node_id: str,
        disk_id: str,
        path: str | Path,
        capacity: int = 0,
        free_space: int = 0,
        healthy: bool = True,
        online: bool = True,
        storage_type: str = "local",
        used_bytes: int = 0,
        latency_ms: float | None = None,
        metadata: dict | None = None,
    ) -> StorageTarget:
        if node_id not in self._nodes:
            self.register_node(node_id)

        node = self._nodes[node_id]
        target = StorageTarget(
            node_id=node_id,
            disk_id=disk_id,
            path=Path(path),
            capacity=capacity,
            free_space=free_space,
            healthy=healthy,
            online=online,
            storage_type=storage_type,
            used_bytes=used_bytes,
            region=node.region,
            rack_id=node.rack_id,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )

        self._targets[(node_id, disk_id)] = target
        return target

    def remove_storage_target(self, node_id: str, disk_id: str):
        self._targets.pop((node_id, disk_id), None)

    def get_storage_targets(
        self,
        include_unhealthy: bool = False,
        include_offline: bool = False,
    ) -> list[StorageTarget]:
        targets = []

        for target in self._targets.values():
            node = self._nodes.get(target.node_id)

            if node is None:
                continue
            if not include_unhealthy and (not node.healthy or not target.healthy):
                continue
            if not include_offline and (not node.online or not target.online):
                continue

            targets.append(target)

        return targets


def _path_used_bytes(path: Path) -> int:
    if not path.exists():
        return 0

    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _path_capacity(path: Path) -> tuple[int, int]:
    try:
        usage = shutil.disk_usage(path if path.exists() else path.parent)
        return usage.total, usage.free
    except OSError:
        return 0, 0


def build_local_cluster_manager(
    disks: list[Path],
    node_id: str = "node-1",
) -> ClusterManager:
    manager = ClusterManager()
    manager.register_node(node_id=node_id, host="localhost")

    for disk in disks:
        capacity, free_space = _path_capacity(disk)
        manager.register_storage_target(
            node_id=node_id,
            disk_id=disk.name,
            path=disk,
            capacity=capacity,
            free_space=free_space,
            used_bytes=_path_used_bytes(disk),
        )

    return manager
