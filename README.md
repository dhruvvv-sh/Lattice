# Lattice

Lattice is an S3-inspired object storage engine built with **Python**, **FastAPI**, and **PostgreSQL**. The project explores the internal architecture of modern object storage systems such as Amazon S3, MinIO, and Ceph by implementing their core storage mechanisms from first principles.

Unlike a traditional file upload API, Lattice separates metadata management from physical storage and introduces fault-tolerant storage concepts including object sharding, parity generation, and erasure-coded recovery.

The long-term goal is to evolve Lattice into a distributed, fault-tolerant object storage platform with S3-compatible APIs and AI-powered semantic retrieval.

---

# Current Features

* RESTful object storage API
* Bucket creation and management
* Object upload, download, and deletion
* PostgreSQL-backed metadata persistence
* SHA-256 checksum generation
* Multi-disk storage architecture
* Object sharding across storage disks
* Parity shard generation
* Object reconstruction from shards
* Single-shard recovery using parity information
* Modular storage engine abstraction
* Concurrent upload support
* Performance benchmarking using Locust

---

# Architecture

```text
                    Client
                       │
                       ▼
                 FastAPI Server
                       │
                       ▼
                Storage Engine
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  Shard Manager   Erasure Engine   Disk Manager
        │              │              │
        └──────┬───────┴───────┬──────┘
               ▼               ▼
        PostgreSQL        Storage Disks
          Metadata
```

The API layer remains independent of the storage implementation.

Objects are processed through the storage engine, split into shards, protected using parity information, and distributed across multiple storage disks. Metadata describing shard placement is stored separately in PostgreSQL.

---

# Fault-Tolerant Storage Model

Lattice currently uses an experimental erasure-coding architecture:

```text
4 Data Shards + 2 Parity Shards
```

Example:

```text
disk1 → data0
disk2 → data1
disk3 → data2
disk4 → data3
disk5 → parity0
disk6 → parity1
```

Objects are reconstructed during reads by combining stored shards. Missing shards can be rebuilt using parity information.

Current implementation demonstrates:

* Object sharding
* Parity generation
* Shard reconstruction
* Single-shard recovery

---

# Technology Stack

| Component         | Technology                  |
| ----------------- | --------------------------- |
| Language          | Python 3                    |
| API               | FastAPI                     |
| ORM               | SQLAlchemy                  |
| Metadata Database | PostgreSQL                  |
| Storage Backend   | Local Filesystem            |
| Fault Tolerance   | Experimental Erasure Coding |
| Load Testing      | Locust                      |
| Authentication    | JWT (planned)               |
| Cache             | Redis (planned)             |

---

# Project Structure

```text
lattice/

├── app/
│   ├── api/
│   ├── storage/
│   │   ├── shard_manager.py
│   │   ├── disk_manager.py
│   │   ├── erasure.py
│   │   └── reconstruction.py
│   │
│   ├── models/
│   ├── database.py
│   └── utils/
│
├── storage/
│   ├── disk1/
│   ├── disk2/
│   ├── disk3/
│   ├── disk4/
│   ├── disk5/
│   └── disk6/
│
├── benchmarks/
├── tests/
├── README.md
└── requirements.txt
```

---

# Metadata Architecture

## Objects

Stores logical object metadata:

* Object ID
* Bucket ID
* Object Name
* Object Size
* SHA-256 Checksum

## Object Shards

Stores shard placement information:

* Object ID
* Shard Index
* Disk Name
* File Path
* Parity Flag
* Shard Size

This separation allows storage placement strategies to evolve without affecting API behavior.

---

# Benchmarks

## v1 (SQLite)

* Metadata backend: SQLite
* Concurrent upload failures due to database locking
* Baseline implementation

## v2 (PostgreSQL)

* Migrated metadata layer to PostgreSQL
* Eliminated SQLite write-lock bottlenecks
* Improved concurrent upload performance
* Reduced request failure rates

Performance benchmark results are available in the `benchmarks/` directory.

---

# Design Principles

* Separation of metadata and object storage
* Storage engine abstraction
* Fault-tolerant architecture
* Extensible storage placement strategies
* S3-inspired object model
* Performance-driven development
* Distributed-systems learning focus

---

# Roadmap

## Completed

* Bucket management
* Object CRUD operations
* PostgreSQL metadata engine
* Multi-disk storage abstraction
* Object sharding
* Parity generation
* Shard reconstruction
* Single-shard recovery
* Performance benchmarking

## In Progress

* Upload pipeline integration with erasure coding
* Download reconstruction pipeline
* Disk health monitoring
* Automatic shard recovery

## Planned

* Reed-Solomon erasure coding
* Multipart uploads
* Redis metadata caching
* Object versioning
* Deduplication
* Presigned URLs
* S3-compatible client support
* Background healing jobs
* Distributed multi-node storage
* Cross-node replication
* Kubernetes deployment
* AI-powered semantic object retrieval (RAG)

---

# Motivation

Lattice was created as a systems engineering project to understand how modern object storage platforms separate metadata management from physical storage while maintaining durability, scalability, and fault tolerance.

Rather than relying on existing storage frameworks, Lattice implements core storage concepts directly, including object sharding, parity-based recovery, metadata management, and multi-disk placement.

The long-term vision is to evolve Lattice into a distributed object storage engine with fault-tolerant storage, S3 compatibility, and intelligent semantic retrieval capabilities.

---

# License

MIT License
