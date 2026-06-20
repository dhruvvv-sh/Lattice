# Lattice Performance Benchmark (v2.0)

## Architecture Changes

* Migrated metadata storage from **SQLite** to **PostgreSQL**
* Improved concurrent write handling
* Eliminated SQLite write-lock contention
* Retained local filesystem object storage

---

## Workload Distribution

| Endpoint                         | Weight |
| -------------------------------- | ------ |
| GET /objects/                    | 5      |
| GET /buckets/                    | 3      |
| GET /objects/{object_id}         | 2      |
| POST /objects/upload/{bucket_id} | 1      |

---

## Overall Performance

| Metric          | Value             |
| --------------- | ----------------- |
| Total Requests  | 5776              |
| Failures        | 0                 |
| Failure Rate    | 0%                |
| Average Latency | 710.38 ms         |
| Throughput      | 47.5 Requests/sec |

---

## Endpoint Performance

| Endpoint                         | Avg Latency | P95      | Max      | Requests | Failures |
| -------------------------------- | ----------- | -------- | -------- | -------- | -------- |
| GET /buckets/                    | 257.40 ms   | 620 ms   | 1022 ms  | 1188     | 0        |
| GET /objects/                    | 277.98 ms   | 640 ms   | 1036 ms  | 3466     | 0        |
| GET /objects/{object_id}         | 4944.98 ms  | 12000 ms | 12483 ms | 534      | 0        |
| POST /objects/upload/{bucket_id} | 328.64 ms   | 720 ms   | 977 ms   | 588      | 0        |

---

## Comparison with v1

| Metric                 | v1 (SQLite) | v2 (PostgreSQL) |
| ---------------------- | ----------- | --------------- |
| Upload Failure Rate    | 0.14%       | 0%              |
| Average Upload Latency | 1124.74 ms  | 328.64 ms       |
| P95 Upload Latency     | 3800 ms     | 720 ms          |
| Maximum Upload Latency | 7696 ms     | 977 ms          |

---

## Observations

* PostgreSQL eliminated concurrent write-lock failures observed with SQLite.
* Upload latency decreased significantly due to improved transaction concurrency.
* Read-only endpoints remained stable under concurrent access.
* Object download latency remains the primary performance bottleneck and will be investigated in future versions.

---

## Future Optimization Targets

* Multi-disk object placement
* Replication and failover
* Erasure coding
* Redis metadata caching
* Multipart uploads
* Asynchronous file I/O
* Distributed metadata management

---

**Version:** Lattice v2.0

**Metadata Backend:** PostgreSQL

**Storage Backend:** Local Filesystem

**Benchmark Date:** June 2026
