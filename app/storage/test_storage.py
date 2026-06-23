from pathlib import Path

from shard_manager import split_bytes
from disk_manager import write_shard

pdf_path = Path(__file__).parent / "Sample.pdf"

print("Reading:", pdf_path)

with open(pdf_path, "rb") as f:
    data = f.read()

shards = split_bytes(data, 4)

for idx, shard in enumerate(shards):
    path = write_shard("Sample.pdf", idx, shard)
    print(f"Stored shard {idx} -> {path}")


#success ->
# output
# Reading: c:\Users\satish\github\Lattice\app\storage\Sample.pdf
# Writing to: storage\disk1\Sample.pdf.part0
# Stored shard 0 -> storage\disk1\Sample.pdf.part0
# Writing to: storage\disk2\Sample.pdf.part1
# Stored shard 1 -> storage\disk2\Sample.pdf.part1
# Writing to: storage\disk3\Sample.pdf.part2
# Stored shard 2 -> storage\disk3\Sample.pdf.part2
# Writing to: storage\disk4\Sample.pdf.part3
# Stored shard 3 -> storage\disk4\Sample.pdf.part3