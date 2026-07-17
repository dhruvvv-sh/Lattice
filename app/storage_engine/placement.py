import importlib
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from app.cluster_manager import StorageTarget
import hashlib

@dataclass(frozen=True)
class PlacementDecision:
    shard_id: int
    node_id: str
    disk_id: str
    path: Path
    copy_index: int = 0
    role: str = "primary"
    replica: bool = False
    metadata: dict | None = None


@dataclass(frozen=True)
class ShardPlacement:
    shard_index: int
    disk_name: str
    disk_path: Path


@dataclass(frozen=True)
class PlacementRequest:
    object_id: int
    object_name: str
    object_size: int
    total_shards: int
    data_shards: int | None = None
    parity_shards: int = 0

    @property
    def parity_shard_ids(self) -> set[int]:
        if self.data_shards is None or self.parity_shards <= 0:
            return set()

        return set(range(self.data_shards, self.data_shards + self.parity_shards))


class PlacementStrategy(ABC):
    @abstractmethod
    def place_object(
        self,
        request: PlacementRequest,
        targets: list[StorageTarget],
    ) -> list[PlacementDecision]:
        pass


class BalancedPlacement(PlacementStrategy):
    def place_object(
        self,
        request: PlacementRequest,
        targets: list[StorageTarget],
    ) -> list[PlacementDecision]:
        healthy_targets = [target for target in targets if target.healthy and target.online]

        if len(healthy_targets) < request.total_shards:
            raise ValueError("Not enough healthy storage targets for shard placement")

        selected = sorted(
            healthy_targets,
            key=lambda target: (
                target.used_bytes,
                target.node_id,
                target.disk_id,
            ),
        )[:request.total_shards]

        return [
            PlacementDecision(
                shard_id=shard_id,
                node_id=target.node_id,
                disk_id=target.disk_id,
                path=target.path,
            )
            for shard_id, target in enumerate(selected)
        ]


class CapacityAwarePlacement(PlacementStrategy):
    def place_object(
        self,
        request: PlacementRequest,
        targets: list[StorageTarget],
    ) -> list[PlacementDecision]:
        healthy_targets = [
            target
            for target in targets
            if target.healthy and target.online
        ]

        if len(healthy_targets) < request.total_shards:
            raise ValueError("Not enough healthy storage targets for shard placement")

        selected = sorted(
            healthy_targets,
            key=lambda target: (
                -target.free_space,
                target.used_bytes,
                target.node_id,
                target.disk_id,
            ),
        )[:request.total_shards]

        return [
            PlacementDecision(
                shard_id=shard_id,
                node_id=target.node_id,
                disk_id=target.disk_id,
                path=target.path,
            )
            for shard_id, target in enumerate(selected)
        ]


class PlacementScheduler(PlacementStrategy):
    def place_object(
        self,
        request: PlacementRequest,
        targets: list[StorageTarget],
    ) -> list[PlacementDecision]:
        healthy_targets = [target for target in targets if target.healthy and target.online]

        if len(healthy_targets) < request.total_shards:
            raise ValueError("Not enough healthy storage targets for shard placement")

        parity_ids = sorted(request.parity_shard_ids)

        if request.parity_shards and len(parity_ids) != request.parity_shards:
            raise ValueError("Placement request has invalid parity shard metadata")

        decisions_by_shard = {}
        selected_keys = set()

        if parity_ids:
            targets_by_node = {}

            for target in healthy_targets:
                targets_by_node.setdefault(target.node_id, []).append(target)

            if len(targets_by_node) < len(parity_ids):
                raise ValueError("Not enough healthy nodes to place parity shards separately")

            parity_nodes = random.sample(list(targets_by_node), len(parity_ids))

            for shard_id, node_id in zip(parity_ids, parity_nodes):
                candidates = [
                    target
                    for target in targets_by_node[node_id]
                    if (target.node_id, target.disk_id) not in selected_keys
                ]

                if not candidates:
                    raise ValueError(f"No available disk on {node_id} for parity shard")

                target = random.choice(candidates)
                selected_keys.add((target.node_id, target.disk_id))
                decisions_by_shard[shard_id] = self._decision(shard_id, target)

        remaining_shard_ids = [
            shard_id
            for shard_id in range(request.total_shards)
            if shard_id not in decisions_by_shard
        ]
        remaining_targets = [
            target
            for target in healthy_targets
            if (target.node_id, target.disk_id) not in selected_keys
        ]

        if len(remaining_targets) < len(remaining_shard_ids):
            raise ValueError("Not enough healthy storage targets for shard placement")

        for shard_id, target in zip(
            remaining_shard_ids,
            random.sample(remaining_targets, len(remaining_shard_ids)),
        ):
            decisions_by_shard[shard_id] = self._decision(shard_id, target)

        return [
            decisions_by_shard[shard_id]
            for shard_id in range(request.total_shards)
        ]

    @staticmethod
    def _decision(shard_id: int, target: StorageTarget) -> PlacementDecision:
        return PlacementDecision(
            shard_id=shard_id,
            node_id=target.node_id,
            disk_id=target.disk_id,
            path=target.path,
            metadata={
                "placement": "random-spread",
            },
        )


class RandomPlacement(PlacementScheduler):
    pass

class NodeHashPlacement(PlacementStrategy):
    """
    Deterministically places each shard on a storage node by hashing
    (object_id, shard_index). The selected node then stores the shard
    on one of its local disks.
    """

    def place_object(
        self,
        request: PlacementRequest,
        targets: list[StorageTarget],
    ) -> list[PlacementDecision]:
        healthy_targets = [
            target
            for target in targets
            if target.healthy and target.online
        ]

        if not healthy_targets:
            raise ValueError("No healthy storage targets available for placement")

        targets_by_node: dict[str, list[StorageTarget]] = {}
        for target in healthy_targets:
            targets_by_node.setdefault(target.node_id, []).append(target)

        node_ids = sorted(targets_by_node)
        if not node_ids:
            raise ValueError("No healthy storage targets available for placement")

        decisions: list[PlacementDecision] = []

        for shard_id in range(request.total_shards):
            digest = hashlib.sha256(
                f"{request.object_id}:{shard_id}".encode("utf-8")
            ).hexdigest()
            node_index = int(digest, 16) % len(node_ids)
            node_id = node_ids[node_index]

            node_targets = sorted(
                targets_by_node[node_id],
                key=lambda target: (target.disk_id, target.path.as_posix()),
            )
            disk_digest = hashlib.sha256(
                f"{request.object_id}:{shard_id}:{node_id}".encode("utf-8")
            ).hexdigest()
            disk_index = int(disk_digest, 16) % len(node_targets)
            target = node_targets[disk_index]

            decisions.append(
                PlacementDecision(
                    shard_id=shard_id,
                    node_id=target.node_id,
                    disk_id=target.disk_id,
                    path=target.path,
                    metadata={
                        "placement": "node_hash",
                        "node_hash": digest,
                    },
                )
            )

        return decisions


class ReplicationAwarePlacement(PlacementStrategy):
    """
    Places each logical shard as one primary copy plus replica copies.

    Replicas for a shard are always placed on different logical nodes from the
    primary and from each other. This keeps the strategy simple enough for the
    current local-node architecture while preserving the key production rule:
    do not let one node failure remove every copy of the same logical shard.
    """

    def __init__(self, replication_factor: int = 2):
        if replication_factor < 1:
            raise ValueError("replication_factor must be at least 1")

        self.replication_factor = replication_factor

    def place_object(
        self,
        request: PlacementRequest,
        targets: list[StorageTarget],
    ) -> list[PlacementDecision]:
        healthy_targets = [
            target
            for target in targets
            if target.healthy and target.online
        ]
        targets_by_node = self._targets_by_node(healthy_targets)

        if len(targets_by_node) < self.replication_factor:
            raise ValueError(
                "Not enough healthy logical nodes for shard replication"
            )

        decisions: list[PlacementDecision] = []

        for shard_id in range(request.total_shards):
            selected_nodes: set[str] = set()

            for copy_index in range(self.replication_factor):
                role = "primary" if copy_index == 0 else "replica"
                target = self._select_target(
                    request=request,
                    targets_by_node=targets_by_node,
                    shard_id=shard_id,
                    copy_index=copy_index,
                    excluded_nodes=selected_nodes,
                )
                selected_nodes.add(target.node_id)
                decisions.append(
                    PlacementDecision(
                        shard_id=shard_id,
                        node_id=target.node_id,
                        disk_id=target.disk_id,
                        path=target.path,
                        copy_index=copy_index,
                        role=role,
                        replica=copy_index > 0,
                        metadata={
                            "placement": "replication_aware",
                            "replication_factor": self.replication_factor,
                        },
                    )
                )

        return decisions

    @staticmethod
    def _targets_by_node(
        targets: list[StorageTarget],
    ) -> dict[str, list[StorageTarget]]:
        targets_by_node: dict[str, list[StorageTarget]] = {}

        for target in targets:
            targets_by_node.setdefault(target.node_id, []).append(target)

        return {
            node_id: sorted(
                node_targets,
                key=lambda target: (
                    target.used_bytes,
                    -target.free_space,
                    target.disk_id,
                    target.path.as_posix(),
                ),
            )
            for node_id, node_targets in targets_by_node.items()
        }

    @staticmethod
    def _select_target(
        request: PlacementRequest,
        targets_by_node: dict[str, list[StorageTarget]],
        shard_id: int,
        copy_index: int,
        excluded_nodes: set[str],
    ) -> StorageTarget:
        candidate_node_ids = [
            node_id
            for node_id in sorted(targets_by_node)
            if node_id not in excluded_nodes
        ]

        if not candidate_node_ids:
            raise ValueError("No healthy node available for shard replica")

        node_digest = hashlib.sha256(
            f"{request.object_id}:{shard_id}:{copy_index}:node".encode("utf-8")
        ).hexdigest()
        node_id = candidate_node_ids[int(node_digest, 16) % len(candidate_node_ids)]
        node_targets = targets_by_node[node_id]
        disk_digest = hashlib.sha256(
            f"{request.object_id}:{shard_id}:{copy_index}:{node_id}:disk".encode(
                "utf-8"
            )
        ).hexdigest()

        return node_targets[int(disk_digest, 16) % len(node_targets)]


BUILT_IN_STRATEGIES = {
    "balanced": BalancedPlacement,
    "capacity": CapacityAwarePlacement,
    "capacity_aware": CapacityAwarePlacement,
    "placement_scheduler": PlacementScheduler,
    "random": RandomPlacement,
    "random_spread": PlacementScheduler,
    "scheduler": PlacementScheduler,

    "node_hash": NodeHashPlacement,
    "replication": ReplicationAwarePlacement,
    "replication_aware": ReplicationAwarePlacement,
}


def load_strategy(strategy_name: str | None = None) -> PlacementStrategy:
    name = strategy_name or os.getenv(
    "LATTICE_PLACEMENT_STRATEGY",
    "node_hash",
    )

    if name in BUILT_IN_STRATEGIES:
        return BUILT_IN_STRATEGIES[name]()

    module_name, class_name = name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    strategy_class = getattr(module, class_name)
    strategy = strategy_class()

    if not isinstance(strategy, PlacementStrategy):
        raise TypeError(f"{name} must inherit PlacementStrategy")

    return strategy
