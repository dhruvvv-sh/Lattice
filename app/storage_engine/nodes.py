from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.cluster_manager import ClusterManager


@dataclass(frozen=True)
class ShardRef:
    node_id: str
    disk_id: str
    path: str


class StorageNodeClient(Protocol):
    node_id: str

    def get_storage_targets(self, manager: ClusterManager):
        pass

    def write_shard(self, disk_id: str, shard_name: str, data: bytes) -> ShardRef:
        pass

    def read_shard(self, disk_id: str, path: str) -> bytes:
        pass

    def delete_shard(self, disk_id: str, path: str):
        pass


class LocalStorageNode:
    def __init__(
        self,
        node_id: str,
        disks: dict[str, Path],
        host: str | None = "localhost",
        port: int | None = None,
    ):
        self.node_id = node_id
        self.host = host
        self.port = port
        self._disks = {disk_id: Path(path) for disk_id, path in disks.items()}

    def get_storage_targets(self, manager: ClusterManager):
        manager.register_node(
            node_id=self.node_id,
            host=self.host,
            port=self.port,
        )

        for disk_id, path in self._disks.items():
            manager.register_storage_target(
                node_id=self.node_id,
                disk_id=disk_id,
                path=path,
            )

    def write_shard(self, disk_id: str, shard_name: str, data: bytes) -> ShardRef:
        disk = self._disk(disk_id)
        disk.mkdir(parents=True, exist_ok=True)

        shard_path = disk / shard_name
        shard_path.write_bytes(data)

        return ShardRef(
            node_id=self.node_id,
            disk_id=disk_id,
            path=str(shard_path),
        )

    def read_shard(self, disk_id: str, path: str) -> bytes:
        shard_path = self._resolve_shard_path(disk_id, path)
        return shard_path.read_bytes()

    def delete_shard(self, disk_id: str, path: str):
        shard_path = self._resolve_shard_path(disk_id, path)
        shard_path.unlink(missing_ok=True)

    def _disk(self, disk_id: str) -> Path:
        try:
            return self._disks[disk_id]
        except KeyError as exc:
            raise ValueError(f"Node {self.node_id} does not own disk {disk_id}") from exc

    def _resolve_shard_path(self, disk_id: str, path: str) -> Path:
        shard_path = Path(path)

        if shard_path.is_absolute():
            return shard_path

        return self._disk(disk_id) / shard_path


class StorageNodeRegistry:
    def __init__(self):
        self._nodes: dict[str, StorageNodeClient] = {}

    def register(self, node: StorageNodeClient):
        self._nodes[node.node_id] = node

    def get(self, node_id: str) -> StorageNodeClient:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise ValueError(f"Storage node {node_id} is not registered") from exc

    def build_cluster_manager(self) -> ClusterManager:
        manager = ClusterManager()

        for node in self._nodes.values():
            node.get_storage_targets(manager)

        return manager


def build_single_node_registry(disks: list[Path], node_id: str = "node-1"):
    registry = StorageNodeRegistry()
    registry.register(
        LocalStorageNode(
            node_id=node_id,
            disks={disk.name: disk for disk in disks},
        )
    )
    return registry


def build_local_node_registry(node_disks: dict[str, list[Path]]):
    registry = StorageNodeRegistry()

    for node_id, disks in node_disks.items():
        registry.register(
            LocalStorageNode(
                node_id=node_id,
                disks={disk.name: disk for disk in disks},
            )
        )

    return registry
