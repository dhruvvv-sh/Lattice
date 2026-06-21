def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def generate_parity(shards):
    """
    Creates two parity shards.
    """

    p1 = xor_bytes(
        xor_bytes(shards[0], shards[1]),
        xor_bytes(shards[2], shards[3])
    )

    p2 = xor_bytes(
        xor_bytes(shards[0], shards[2]),
        xor_bytes(shards[1], shards[3])
    )

    return [p1, p2]


def recover_missing_shard(shards, parity, missing_index):
    recovered = parity

    for i, shard in enumerate(shards):
        if i != missing_index:
            recovered = xor_bytes(recovered, shard)

    return recovered