# Lattice Storage Simulation Outputs

This file records the current storage verification results for the Reed-Solomon layer and the API-integrated sharded storage path.

---

# Reed-Solomon 4+2 Verification

Test data:

```text
b"abcdefghijklmnopqrstuvwxyz0123456789"
```

Shard layout:

```text
4 data shards + 2 parity shards
```

Output:

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

Interpretation:

* A single missing data shard can be recovered.
* Two missing data shards can be recovered.
* A missing data shard plus a missing parity shard can be recovered.
* Two missing parity shards can be rebuilt from complete data shards.
* Three missing shards correctly fail because `4+2` Reed-Solomon can recover only two erasures.
* Reconstructed data can be trimmed back to the original object size after shard padding.

---

# Sample PDF Shard Flow

The sample PDF flow writes four data shards and two parity shards:

```text
Writing to: storage/disk1/Sample.pdf.part0
Stored data shard 0 -> storage/disk1/Sample.pdf.part0

Writing to: storage/disk2/Sample.pdf.part1
Stored data shard 1 -> storage/disk2/Sample.pdf.part1

Writing to: storage/disk3/Sample.pdf.part2
Stored data shard 2 -> storage/disk3/Sample.pdf.part2

Writing to: storage/disk4/Sample.pdf.part3
Stored data shard 3 -> storage/disk4/Sample.pdf.part3

Parity generated!
Parity count: 2

Writing to: storage/disk5/Sample.pdf.part4
Stored parity shard 0 -> storage/disk5/Sample.pdf.part4

Writing to: storage/disk6/Sample.pdf.part5
Stored parity shard 1 -> storage/disk6/Sample.pdf.part5
```

Recovery simulation:

```text
Recovered shard size: 41402
```

Integrity verification:

```text
Original : 4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc
Recovered: 4aa645665dc00977940383881064d8e35e401dfce9158a5e3686b2d94cd09dcc
```

Result:

```text
Shard successfully reconstructed from Reed-Solomon parity.
SHA-256 hashes match.
```

---

# API-Integrated Sharded Storage

The FastAPI object path now uses the sharded storage engine for uploads and downloads.

Verified behavior:

```text
upload object
create 4 data shards
create 2 parity shards
persist object_shards rows
persist object_placement_manifests row
delete one data shard
delete one parity shard
download object successfully
delete object
clean shard files and metadata
```

Current automated result:

```text
10 passed
```

---

# Cluster and Placement Verification

The cluster-manager and placement tests verify:

```text
register storage nodes
register storage targets
filter unhealthy targets
filter offline nodes
generate PlacementDecision objects
generate placement manifest JSON
support custom placement strategies
```

The default local cluster still maps to local disk directories, but placement now operates on `StorageTarget` objects rather than direct disk indexes.
