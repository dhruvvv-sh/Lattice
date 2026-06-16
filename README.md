# Lattice

**Lattice** is a distributed, **S3-compatible object storage engine** built with **Python** and **FastAPI**. It provides scalable object storage through a modular architecture supporting buckets, multipart uploads, deduplication, metadata management, and future horizontal scaling across multiple storage nodes.

The project aims to explore the design principles behind modern object storage systems such as Amazon S3 and MinIO while maintaining compatibility with standard S3 clients.

---

## Features

* S3-compatible REST API
* Bucket creation and management
* Object upload, download, and deletion
* Multipart uploads
* SHA-256 content hashing
* Content-addressable deduplication
* Object versioning
* Metadata persistence
* Redis-backed metadata caching
* JWT authentication
* Modular storage engine
* Designed for future distributed replication

---

# Architecture

```
                    AWS CLI
                       │
                       ▼
                FastAPI Server
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   PostgreSQL                    Redis Cache
(metadata & users)          (hot objects/cache)

                       │
                       ▼
              Object Storage Engine
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
        Disk 1                 Disk 2
```

The API layer handles all incoming requests while PostgreSQL stores persistent metadata and Redis accelerates frequently accessed object lookups. The storage engine abstracts physical storage and manages object placement independently of the API.

---

# Technology Stack

| Layer            | Technology       |
| ---------------- | ---------------- |
| Language         | Python 3.12      |
| API              | FastAPI          |
| Database         | PostgreSQL       |
| Cache            | Redis            |
| ORM              | SQLAlchemy       |
| Authentication   | JWT              |
| Storage          | Local Filesystem |
| Async Runtime    | asyncio          |
| File I/O         | aiofiles         |
| Containerization | Docker           |
| Reverse Proxy    | Nginx            |
| Testing          | pytest           |
| CI/CD            | GitHub Actions   |

---

# Project Structure

```
lattice/

├── app/
│   ├── api/
│   ├── auth/
│   ├── buckets/
│   ├── objects/
│   ├── storage/
│   ├── metadata/
│   ├── replication/
│   ├── multipart/
│   ├── dedup/
│   ├── scheduler/
│   └── utils/
│
├── tests/
├── docker/
├── docs/
├── benchmarks/
├── scripts/
├── docker-compose.yml
└── README.md
```

Each module is isolated to simplify maintenance and allow future replacement of individual components without affecting the overall architecture.

---

# Database Schema

## Users

| Field         | Type      |
| ------------- | --------- |
| id            | UUID      |
| email         | VARCHAR   |
| password_hash | TEXT      |
| created_at    | TIMESTAMP |

---

## Buckets

| Field       | Type      |
| ----------- | --------- |
| id          | UUID      |
| owner_id    | UUID      |
| bucket_name | VARCHAR   |
| created_at  | TIMESTAMP |

---

## Objects

| Field        | Type      |
| ------------ | --------- |
| id           | UUID      |
| bucket_id    | UUID      |
| key          | TEXT      |
| size         | BIGINT    |
| sha256       | TEXT      |
| version      | INTEGER   |
| created_at   | TIMESTAMP |
| storage_path | TEXT      |

---

# Design Goals

* S3 API compatibility
* Clean separation between metadata and object storage
* Modular architecture
* Horizontal scalability
* Fault-tolerant design
* Efficient large object handling
* Content-addressable storage
* Future support for distributed replication

---

# Roadmap

## Phase 1

* Bucket management
* Object CRUD
* Metadata persistence
* Filesystem backend

## Phase 2

* Authentication
* Access control
* Object listing

## Phase 3

* SHA-256 deduplication
* Redis metadata cache

## Phase 4

* Multipart uploads
* Parallel upload support
* Upload resume capability

## Phase 5

* Object versioning
* Soft deletion
* Lifecycle management

## Phase 6

* Presigned URLs
* Temporary object access
* Secure sharing

## Phase 7

* Multi-node storage
* Object placement strategy
* Consistent hashing

## Phase 8

* Replication
* Node health monitoring
* Automatic recovery

## Phase 9

* Full S3 API compatibility
* AWS CLI integration
* SDK compatibility

---

# Future Work

* Erasure coding
* Compression
* Encryption at rest
* Object lifecycle policies
* Storage quotas
* Metrics and monitoring
* Prometheus integration
* Grafana dashboards
* Kubernetes deployment
* Cross-region replication

---

# Motivation

Modern applications depend heavily on object storage for managing images, videos, backups, machine learning datasets, and application assets.

Lattice is an educational systems project focused on understanding the internal architecture of distributed object storage engines by implementing the core concepts from first principles rather than relying on managed cloud services.

---

# License

MIT License
