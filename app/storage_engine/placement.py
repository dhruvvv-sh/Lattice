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


class RandomPlacement(PlacementStrategy):
    def place_object(
        self,
        request: PlacementRequest,
        targets: list[StorageTarget],
    ) -> list[PlacementDecision]:
        healthy_targets = [target for target in targets if target.healthy and target.online]

        if len(healthy_targets) < request.total_shards:
            raise ValueError("Not enough healthy storage targets for shard placement")

        selected = random.sample(healthy_targets, request.total_shards)

        return [
            PlacementDecision(
                shard_id=shard_id,
                node_id=target.node_id,
                disk_id=target.disk_id,
                path=target.path,
            )
            for shard_id, target in enumerate(selected)
        ]


BUILT_IN_STRATEGIES = {
    "balanced": BalancedPlacement,
    "capacity": CapacityAwarePlacement,
    "capacity_aware": CapacityAwarePlacement,
    "random": RandomPlacement,
}


def load_strategy(strategy_name: str | None = None) -> PlacementStrategy:
    name = strategy_name or os.getenv("LATTICE_PLACEMENT_STRATEGY", "balanced")

    if name in BUILT_IN_STRATEGIES:
        return BUILT_IN_STRATEGIES[name]()

    module_name, class_name = name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    strategy_class = getattr(module, class_name)
    strategy = strategy_class()

    if not isinstance(strategy, PlacementStrategy):
        raise TypeError(f"{name} must inherit PlacementStrategy")

    return strategy
