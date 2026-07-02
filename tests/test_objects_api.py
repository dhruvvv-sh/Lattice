from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import objects
from app.database import Base
from app.models import Bucket, Object, ObjectPlacementManifest, ObjectShard
from app.storage_engine import sharded


def build_test_session(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    disks = [tmp_path / f"disk{i}" for i in range(1, 7)]
    monkeypatch.setattr(sharded, "DISKS", disks)
    monkeypatch.setenv("LATTICE_PLACEMENT_STRATEGY", "balanced")
    monkeypatch.setattr(objects, "SessionLocal", testing_session)

    return testing_session


def test_api_upload_download_recovers_and_delete_cleans_shards(tmp_path, monkeypatch):
    testing_session = build_test_session(tmp_path, monkeypatch)

    db = testing_session()
    bucket = Bucket(name="documents")
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    bucket_id = bucket.id
    db.close()

    payload = b"Lattice API sharded object" * 401
    upload_body = objects.upload(
        bucket_id=bucket_id,
        file=SimpleNamespace(
            filename="notes.bin",
            file=BytesIO(payload),
            content_type="application/octet-stream",
        ),
    )

    assert upload_body["shards"] == sharded.TOTAL_SHARDS
    object_id = upload_body["object_id"]

    db = testing_session()
    obj = db.query(Object).filter(Object.id == object_id).one()
    shards = (
        db.query(ObjectShard)
        .filter(ObjectShard.object_id == object_id)
        .order_by(ObjectShard.shard_index)
        .all()
    )
    manifest = (
        db.query(ObjectPlacementManifest)
        .filter(ObjectPlacementManifest.object_id == object_id)
        .one()
    )
    assert obj.disk_name == "erasure-4+2"
    assert len(shards) == sharded.TOTAL_SHARDS
    assert sum(shard.is_parity for shard in shards) == sharded.PARITY_SHARDS
    assert {shard.node_id for shard in shards} == {"node-1"}
    assert [shard.disk_id for shard in shards] == [f"disk{i}" for i in range(1, 7)]
    assert all(Path(shard.shard_path).exists() for shard in shards)
    assert manifest.strategy == "BalancedPlacement"
    assert manifest.manifest["strategy"] == "BalancedPlacement"
    assert len(manifest.manifest["layout"]) == sharded.TOTAL_SHARDS

    Path(shards[1].shard_path).unlink()
    Path(shards[4].shard_path).unlink()
    db.close()

    download = objects.download(object_id)

    assert download.status_code == 200
    assert download.body == payload

    delete = objects.delete_obj(object_id)

    assert delete["object_id"] == object_id

    db = testing_session()
    assert db.query(Object).filter(Object.id == object_id).first() is None
    assert db.query(ObjectShard).filter(ObjectShard.object_id == object_id).count() == 0
    assert (
        db.query(ObjectPlacementManifest)
        .filter(ObjectPlacementManifest.object_id == object_id)
        .count()
        == 0
    )
    db.close()

    for disk in tmp_path.iterdir():
        assert not list(disk.iterdir())
