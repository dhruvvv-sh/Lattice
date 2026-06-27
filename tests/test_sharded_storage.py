from types import SimpleNamespace

import pytest

from app.storage_engine import sharded


class FakeDb:
    def __init__(self, obj):
        self.obj = obj

    def add(self, shard):
        self.obj.shards.append(shard)


def test_sharded_storage_round_trip_and_two_shard_recovery(tmp_path, monkeypatch):
    disks = [tmp_path / f"disk{i}" for i in range(1, 7)]
    monkeypatch.setattr(sharded, "DISKS", disks)

    data = b"Lattice sharded upload test data" * 257
    obj = SimpleNamespace(
        id=101,
        object_name="sample.bin",
        size=len(data),
        shards=[],
    )

    paths = sharded.save_object_shards(FakeDb(obj), obj, data)

    assert len(paths) == sharded.TOTAL_SHARDS
    assert len(obj.shards) == sharded.TOTAL_SHARDS
    assert all(path.exists() for path in disks)
    assert sharded.load_object_bytes(obj) == data

    (tmp_path / "disk2" / "object_101_sample.bin.part1").unlink()
    (tmp_path / "disk5" / "object_101_sample.bin.part4").unlink()

    assert sharded.load_object_bytes(obj) == data


def test_sharded_storage_fails_when_more_than_two_shards_are_missing(tmp_path, monkeypatch):
    disks = [tmp_path / f"disk{i}" for i in range(1, 7)]
    monkeypatch.setattr(sharded, "DISKS", disks)

    data = b"cannot recover this when three shards are gone" * 129
    obj = SimpleNamespace(
        id=102,
        object_name="sample.bin",
        size=len(data),
        shards=[],
    )

    sharded.save_object_shards(FakeDb(obj), obj, data)

    (tmp_path / "disk1" / "object_102_sample.bin.part0").unlink()
    (tmp_path / "disk2" / "object_102_sample.bin.part1").unlink()
    (tmp_path / "disk5" / "object_102_sample.bin.part4").unlink()

    with pytest.raises(ValueError, match="Too many missing shards"):
        sharded.load_object_bytes(obj)
