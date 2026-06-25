# Lattice Storage Engine Architecture

This document describes the current storage design and the next integration target.

---

# Current State

Lattice currently has two storage paths:

| Layer | Location | State |
| --- | --- | --- |
| API storage path | `app/storage_engine` | Active for FastAPI uploads/downloads; stores each object as a whole file on one selected disk |
| Shard prototype | `app/storage` | Implements sharding, Reed-Solomon parity, reconstruction, and recovery simulations |

The immediate goal is to connect the shard prototype to the API storage path.

---

# Current API Upload Flow

```text
Client
  |
  | POST /objects/upload/{bucket_id}
  v
FastAPI API
  |
  | Validate bucket
  v
app/storage_engine/writer.py
  |
  | Select disk with round-robin
  v
storage/diskN/bucket_{bucket_id}/filename
  |
  | Store object metadata
  v
PostgreSQL objects table
```

Current behavior:

* The whole uploaded file is saved on one disk.
* Metadata is written to the `objects` table.
* The Reed-Solomon shard engine is not yet used by this path.

---

# Target Sharded Upload Flow

```text
Client
  |
  | POST /objects/upload/{bucket_id}
  v
FastAPI API
  |
  | Validate bucket
  v
Storage Engine
  |
  | Read uploaded bytes
  v
Shard Manager
  |
  | Split object into 4 data shards
  v
Erasure Engine
  |
  | Generate 2 Reed-Solomon parity shards
  v
Disk Manager
  |
  | Write data0, data1, data2, data3, parity0, parity1
  v
PostgreSQL
  |
  | Store object row and object_shards rows
  v
Return success response
```

---

# Target Download Flow

```text
Client
  |
  | GET /objects/{object_id}
  v
FastAPI API
  |
  | Query object and shard metadata
  v
Storage Engine
  |
  | Read available shards
  v
Erasure Engine
  |
  | Recover missing shards when <= 2 shards are missing
  v
Shard Manager
  |
  | Reconstruct bytes and trim to original size
  v
Stream object to client
```

---

# Reed-Solomon Fault Tolerance Model

The prototype uses a `4+2` Reed-Solomon layout:

```text
4 data shards + 2 parity shards
```

Example placement:

```text
disk1 -> data0
disk2 -> data1
disk3 -> data2
disk4 -> data3
disk5 -> parity0
disk6 -> parity1
```

Recovery support:

* One missing data shard
* Two missing data shards
* One missing data shard and one missing parity shard
* Two missing parity shards
* Correct failure when more than two total shards are missing

---

# Storage Components

## `shard_manager.py`

Responsibilities:

* Split bytes into equal-sized data shards.
* Pad the final shard when needed.
* Reconstruct bytes by joining data shards.
* Trim reconstructed data back to the original object size when provided.

## `erasure.py`

Responsibilities:

* Generate Reed-Solomon parity shards.
* Recover missing data or parity shards.
* Enforce the `4+2` recovery limit.

## `disk_manager.py`

Responsibilities:

* Map shard indexes to disk directories.
* Write shard files to disk.
* Read shard files from disk.
* Check whether a shard exists.

## `health_check.py` and `heartbeat.py`

Responsibilities:

* Check whether storage disk directories exist.
* Verify basic write/read access with heartbeat files.
* Maintain in-memory cluster health state.

---

# Metadata Layer

## `objects` Table

Currently used by the API path:

* Object ID
* Bucket ID
* Object name
* Whole-file path
* Disk name
* Object size
* Content type
* Checksum
* Created timestamp

## `object_shards` Table

Defined and ready for the sharded path:

* Object ID
* Shard index
* Disk name
* Shard path
* Parity flag
* Shard size
* Created timestamp

The next integration step is to populate this table during API uploads.

---

# Current Verification Results

The Reed-Solomon test cases are documented in `reed_solomon_test_cases.md`.

Summary:

```text
case_1_single_data_missing ok
case_2_data_and_parity_missing ok
case_3_two_data_missing ok
case_4_two_parity_missing ok
case_5_three_missing failed_as_expected Too many missing shards to recover
case_6_reconstruction_trim ok
```

---

# Planned Work

* Route API uploads through the shard manager and erasure engine.
* Persist one `object_shards` row per written shard.
* Reconstruct API downloads from shard metadata.
* Add read repair when a missing shard is reconstructed during a read.
* Skip unhealthy disks during placement.
* Move script-style checks into automated pytest tests.
* Add background healing jobs.
