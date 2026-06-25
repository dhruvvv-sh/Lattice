# Lattice

Lattice is an S3-inspired object storage engine built with Python, FastAPI, and PostgreSQL. The project explores how systems such as Amazon S3, MinIO, and Ceph separate metadata from physical object storage while preserving durability, scalability, and fault tolerance.

The current project has two active layers:

* A working FastAPI object API backed by PostgreSQL metadata and local filesystem storage.
* A storage prototype that demonstrates sharding, Reed-Solomon parity, reconstruction, and disk-failure recovery scenarios.

The long-term goal is to evolve Lattice into a distributed, fault-tolerant object storage platform with S3-compatible APIs, background healing, multi-node replication, and AI-powered semantic retrieval.

---

# Current Features

## Object API

* Bucket creation, listing, update, and deletion
* Object upload, download, listing, and deletion
* PostgreSQL-backed metadata persistence
* SHA-256 checksum generation
* Round-robin whole-file placement across local storage disks
* Concurrent upload benchmarking with Locust

## Storage Prototype

* Object splitting into 4 data shards
* Reed-Solomon parity generation with a `4+2` layout
* Recovery from one or two missing shards
* Full object reconstruction from data shards
* Original-size trimming after padded reconstruction
* Disk health checks and cluster health state
* Documented Reed-Solomon recovery test cases

## Current Boundary

The Reed-Solomon shard engine exists under `app/storage`, but the API upload/download path under `app/storage_engine` still stores each uploaded object as a whole file on one selected disk. The next major integration step is to route API uploads through the shard engine and persist shard placement in the `object_shards` table.

---

# Architecture

```text
                    Client
                       |
                       v
                 FastAPI Server
                       |
                       v
              Object API / Metadata
                       |
          +------------+-------------+
          |                          |
          v                          v
  Whole-file Storage Path     Shard Prototype
  app/storage_engine          app/storage
          |                          |
          v                          v
   Local storage disks       Reed-Solomon 4+2
          |
          v
      PostgreSQL
```

The API layer currently handles production-style bucket/object flows. The shard prototype models the MinIO-inspired fault-tolerant storage layer that will be integrated into the API path next.

---

# Fault-Tolerant Storage Model

The storage prototype now uses Reed-Solomon erasure coding:

```text
4 Data Shards + 2 Parity Shards
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

Supported recovery cases:

* One missing data shard
* Two missing data shards
* One missing data shard plus one missing parity shard
* Two missing parity shards
* Failure when more than two total shards are missing

Detailed results are documented in `app/storage/reed_solomon_test_cases.md`.

---

# Storage Simulations

The storage scripts validate the Reed-Solomon layer independently from the API.

## Reed-Solomon Verification

The current verification covers:

```text
data_size 36
data_shards 4 [9, 9, 9, 9]
parity_shards 2 [9, 9]
case_1_single_data_missing ok
case_2_data_and_parity_missing ok
case_3_two_data_missing ok
case_4_two_parity_missing ok
case_5_three_missing failed_as_expected Too many missing shards to recover
case_6_reconstruction_trim ok
```

## Sample PDF Recovery

The sample shard recovery flow also verifies a recovered shard with SHA-256:

```text
Original : 4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc
Recovered: 4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc
```

Result:

```text
Recovery Successful
Integrity Verified
```

---

# Technology Stack

| Component | Technology |
| --- | --- |
| Language | Python 3 |
| API | FastAPI |
| ORM | SQLAlchemy |
| Metadata Database | PostgreSQL |
| Storage Backend | Local Filesystem |
| Erasure Coding | Reed-Solomon via `reedsolo` |
| Load Testing | Locust |
| Container Runtime | Docker Compose |
| Authentication | JWT (planned) |
| Cache | Redis (planned) |

---

# Run With Docker

Build and start the API with PostgreSQL:

```bash
docker compose --env-file .env.docker up --build
```

The API will be available at:

```text
http://localhost:8000
```

PostgreSQL runs inside Docker with this connection string:

```text
postgresql://postgres:postgres@localhost:5432/lattice
```

Uploaded objects are stored in the local `storage/` directory through a bind mount, and database files are stored in the Docker volume `postgres_data`.

To stop the containers:

```bash
docker compose --env-file .env.docker down
```

To remove the database volume as well:

```bash
docker compose --env-file .env.docker down -v
```

---

# Project Structure

```text
lattice/
|-- app/
|   |-- api/
|   |   |-- buckets.py
|   |   |-- objects.py
|   |   `-- cluster.py
|   |-- storage/
|   |   |-- shard_manager.py
|   |   |-- disk_manager.py
|   |   |-- erasure.py
|   |   |-- reconstruction.py
|   |   |-- health_check.py
|   |   |-- heartbeat.py
|   |   |-- cluster_state.py
|   |   |-- storagestructure.md
|   |   `-- reed_solomon_test_cases.md
|   |-- storage_engine/
|   |   |-- writer.py
|   |   |-- reader.py
|   |   |-- disk_selector.py
|   |   |-- checksum.py
|   |   `-- delete.py
|   |-- database.py
|   |-- models.py
|   `-- schemas.py
|-- benchmark/
|   |-- benchmarks_locust_v1.md
|   `-- benchmarks_locust_v2.md
|-- storage/
|   |-- disk1/
|   |-- disk2/
|   |-- disk3/
|   |-- disk4/
|   |-- disk5/
|   `-- disk6/
|-- Dockerfile
|-- docker-compose.yml
|-- simulationoutputs.md
|-- README.md
`-- requirements.txt
```

---

# Metadata Architecture

## Objects Table

Stores logical object metadata:

* Object ID
* Bucket ID
* Object name
* Whole-file path
* Disk name
* Object size
* Content type
* SHA-256 checksum

## Object Shards Table

The `ObjectShard` model exists for the upcoming shard-integrated API path:

* Object ID
* Shard index
* Disk name
* Shard path
* Parity flag
* Shard size

This table is the bridge between the current API and the Reed-Solomon storage layer that will be integrated next.

---

# Benchmark Evolution

## Version 1: SQLite

* SQLite metadata backend
* Concurrent upload failures due to database locking
* Initial storage engine implementation

## Version 2: PostgreSQL

* Migrated metadata layer to PostgreSQL
* Eliminated SQLite write-lock bottlenecks
* Improved concurrent upload performance
* Reduced request failure rates

Performance benchmark results are available in the `benchmark/` directory.

---

# Roadmap

## Completed

* Bucket management
* Object CRUD operations
* PostgreSQL metadata engine
* Docker Compose setup for API plus PostgreSQL
* Multi-disk storage directories
* Object sharding prototype
* Reed-Solomon parity generation
* One- and two-shard recovery in the storage prototype
* Full shard reconstruction helper
* Disk health monitoring
* Cluster health endpoint
* Locust performance benchmarking

## In Progress

* Upload pipeline integration with Reed-Solomon shard storage
* Download reconstruction pipeline for API reads
* Persisting shard placement metadata during uploads
* Automatic shard recovery
* Background repair workflows

## Planned

* Multipart uploads
* Redis metadata caching
* Object versioning
* Deduplication
* Presigned URLs
* S3-compatible client support
* Read repair
* Distributed multi-node storage
* Cross-node replication
* Kubernetes deployment
* AI-powered semantic object retrieval (RAG)

---

# Motivation

Lattice was created as a systems engineering project to understand how modern object storage platforms separate metadata management from physical storage while maintaining durability, scalability, and fault tolerance.

Instead of relying on existing storage frameworks for the whole system, Lattice implements the core object-storage concepts directly: bucket/object APIs, metadata persistence, local disk placement, sharding, Reed-Solomon parity, disk health checks, and recovery simulations.

The long-term vision is to evolve Lattice into a distributed object storage engine capable of fault-tolerant storage, S3 compatibility, automatic healing, and intelligent semantic retrieval.

---

# License

MIT License
