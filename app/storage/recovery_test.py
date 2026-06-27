# app/storage/recovery_test.py

from app.storage.disk_manager import read_shard
from app.storage.erasure import recover_missing_shard


def main():
    d0 = read_shard("Sample.pdf", 0)
    d1 = read_shard("Sample.pdf", 1)
    d2 = None
    d3 = read_shard("Sample.pdf", 3)

    p1 = read_shard("Sample.pdf", 4)
    p2 = read_shard("Sample.pdf", 5)

    recovered = recover_missing_shard(
        [d0, d1, d2, d3],
        [p1, p2],
        missing_index=2
    )

    with open("recovered_part2.bin", "wb") as f:
        f.write(recovered)

    print("Recovered shard size:", len(recovered))


if __name__ == "__main__":
    main()
