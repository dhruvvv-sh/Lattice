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



#Success ->
#output 
# Writing to: storage\disk1\Sample.pdf.part0
# Stored data shard 0 -> storage\disk1\Sample.pdf.part0
# Writing to: storage\disk2\Sample.pdf.part1
# Stored data shard 1 -> storage\disk2\Sample.pdf.part1
# Writing to: storage\disk3\Sample.pdf.part2
# Stored data shard 2 -> storage\disk3\Sample.pdf.part2
# Writing to: storage\disk4\Sample.pdf.part3
# Stored data shard 3 -> storage\disk4\Sample.pdf.part3
# Parity generated!
# Parity count: 2
# Writing to: storage\disk5\Sample.pdf.part4
# Stored parity shard 0 -> storage\disk5\Sample.pdf.part4
# Writing to: storage\disk6\Sample.pdf.part5
# Stored parity shard 1 -> storage\disk6\Sample.pdf.part5