# Lattice

Lattice is an S3-inspired object storage engine built with **Python**, **FastAPI**, and **PostgreSQL**. The project explores the internal architecture of modern object storage systems such as Amazon S3 and MinIO by implementing their core building blocks from first principles.

Rather than serving as a simple file upload API, Lattice is designed as a modular storage engine with separate metadata and storage layers, enabling future support for replication, erasure coding, and distributed storage clusters.

---

# Current Features

* RESTful object storage API
* Bucket creation and management
* Object upload, download, and deletion
* PostgreSQL-backed metadata persistence
* SHA-256 checksum generation
* Multi-disk object placement
* Round-robin storage allocation
* Modular storage engine abstraction
* Concurrent upload support
* Performance benchmarking using Locust

---

# Architecture

```
                    Client
                       │
                       ▼
                 FastAPI Server
                       │
              PostgreSQL Metadata
                       │
                       ▼
              Storage Placement Layer
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Disk 1         Disk 2         Disk 3
```

The API layer is responsible for request handling while the storage engine independently determines physical object placement across multiple storage disks.

This separation allows future storage strategies to be implemented without modifying the API layer.

---

# Technology Stack

| Component         | Technology       |
| ----------------- | ---------------- |
| Language          | Python 3         |
| API               | FastAPI          |
| ORM               | SQLAlchemy       |
| Metadata Database | PostgreSQL       |
| Storage Backend   | Local Filesystem |
| Load Testing      | Locust           |
| Authentication    | JWT (planned)    |
| Cache             | Redis (planned)  |

---

# Project Structure

```
lattice/

├── app/
│   ├── api/
│   ├── storage_engine/
│   ├── models/
│   ├── database.py
│   └── utils/
│
├── storage/
│   ├── disk1/
│   ├── disk2/
│   └── disk3/
│
├── benchmarks/
├── tests/
├── README.md
└── requirements.txt
```

---

# Storage Engine

Objects are distributed across multiple storage disks using a round-robin placement strategy.

Example:

```
Upload 1 → disk1
Upload 2 → disk2
Upload 3 → disk3
Upload 4 → disk1
Upload 5 → disk2
```

Metadata stored in PostgreSQL records the physical location of every object, allowing retrieval independent of storage placement.

---

# Benchmarks

## v1 (SQLite)

* Metadata backend: SQLite
* Upload failures under concurrent load due to SQLite write locking
* Baseline implementation

## v2 (PostgreSQL)

* Migrated metadata layer to PostgreSQL
* Eliminated concurrent write-lock failures
* Reduced upload latency significantly
* Improved concurrent upload performance

Performance benchmarks are available in the `benchmarks/` directory.

---

# Design Principles

* Separation of metadata and object storage
* Modular storage engine design
* Storage placement abstraction
* Extensible architecture
* S3-inspired object model
* Performance-driven development

---

# Roadmap

## Completed

* Bucket management
* Object CRUD operations
* PostgreSQL metadata engine
* Multi-disk storage abstraction
* Round-robin object placement
* Performance benchmarking

## In Progress

* Replicated object storage
* Read failover
* Disk health monitoring

## Planned

* Reed-Solomon erasure coding
* Multipart uploads
* Redis metadata caching
* Object versioning
* Deduplication
* Presigned URLs
* S3-compatible client support
* AI-powered semantic object retrieval (RAG)
* Distributed multi-node storage
* Kubernetes deployment

---

# Motivation

Lattice was created as a systems engineering project to understand how modern object storage platforms separate metadata management from physical storage while providing scalability, fault tolerance, and efficient object retrieval.

The long-term objective is to evolve Lattice into a distributed storage engine featuring replication, erasure coding, and intelligent object retrieval while remaining compatible with standard S3 workflows.

---

# License

MIT License
