from pathlib import Path

from shard_manager import split_bytes
from disk_manager import write_shard
from erasure import generate_parity

pdf_path = Path(__file__).parent / "Sample.pdf"

with open(pdf_path, "rb") as f:
    data = f.read()

# Create 4 data shards
shards = split_bytes(data, 4)

# Store data shards
for idx, shard in enumerate(shards):
    path = write_shard("Sample.pdf", idx, shard)
    print(f"Stored data shard {idx} -> {path}")

# Create parity
parity_shards = generate_parity(shards)

print("Parity generated!")
print("Parity count:", len(parity_shards))

# Store parity shards
for idx, parity in enumerate(parity_shards):
    disk_index = idx + 4

    path = write_shard("Sample.pdf", disk_index, parity)

    print(f"Stored parity shard {idx} -> {path}")