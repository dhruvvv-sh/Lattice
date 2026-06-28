import importlib
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.cluster_manager import StorageTarget


@dataclass(frozen=True)
class PlacementDecision:
    shard_id: int
    node_id: str
    disk_id: str
    path: Path
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


BUILT_IN_STRATEGIES = {
    "balanced": BalancedPlacement,
    "capacity": CapacityAwarePlacement,
    "capacity_aware": CapacityAwarePlacement,
    "placement_scheduler": PlacementScheduler,
    "random": RandomPlacement,
    "random_spread": PlacementScheduler,
    "scheduler": PlacementScheduler,
}


def load_strategy(strategy_name: str | None = None) -> PlacementStrategy:
    name = strategy_name or os.getenv("LATTICE_PLACEMENT_STRATEGY", "random_spread")

    if name in BUILT_IN_STRATEGIES:
        return BUILT_IN_STRATEGIES[name]()

    module_name, class_name = name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    strategy_class = getattr(module, class_name)
    strategy = strategy_class()

    if not isinstance(strategy, PlacementStrategy):
        raise TypeError(f"{name} must inherit PlacementStrategy")

    return strategy
