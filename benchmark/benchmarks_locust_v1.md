# Lattice v1 Performance Benchmark

## Test Environment

| Parameter         | Value                     |
| ----------------- | ------------------------- |
| Framework         | FastAPI                   |
| Database          | SQLite                    |
| Storage Backend   | Local Filesystem          |
| Load Testing Tool | Locust                    |
| Concurrent Users  | 100                       |
| Spawn Rate        | 20 users/sec              |
| Benchmark Type    | Mixed Read/Write Workload |

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
| Total Requests  | 6283              |
| Failures        | 9                 |
| Failure Rate    | 0.14%             |
| Average Latency | 631.94 ms         |
| Median Latency  | 530 ms            |
| 95th Percentile | 1700 ms           |
| 99th Percentile | 3200 ms           |
| Maximum Latency | 7696 ms           |
| Throughput      | 46.4 Requests/sec |

---

## Endpoint Performance

| Endpoint                         | Avg Latency | 95th %ile | Max     | Requests | Failures |
| -------------------------------- | ----------- | --------- | ------- | -------- | -------- |
| GET /buckets/                    | 456.43 ms   | 1100 ms   | 2733 ms | 1315     | 0        |
| GET /objects/                    | 549.23 ms   | 1300 ms   | 2613 ms | 3730     | 0        |
| GET /objects/{object_id}         | 1007.77 ms  | 3000 ms   | 4567 ms | 605      | 0        |
| POST /objects/upload/{bucket_id} | 1124.74 ms  | 3800 ms   | 7696 ms | 633      | 9        |

---

## Observations

* Read-only endpoints remained stable under concurrent access.
* Upload operations introduced noticeable latency due to concurrent file writes and metadata persistence.
* Mixed read/write workloads reduced throughput compared to read-only benchmarks.
* Overall failure rate remained below 1%, indicating acceptable stability for the initial implementation.

---

## Future Optimization Targets

Status note: the PostgreSQL migration listed below was completed in Lattice v2.0. The remaining items are still useful optimization targets.

* Migrate metadata storage from SQLite to PostgreSQL. Completed in v2.0.
* Introduce Redis caching for metadata lookups.
* Implement multipart uploads for large files.
* Add asynchronous file I/O where applicable.
* Benchmark with larger files and higher concurrency levels.
* Compare performance across V1, V2, and V3 implementations.

---

**Version:** Lattice v1.0

**Date:** June 2026
