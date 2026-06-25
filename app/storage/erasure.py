from reedsolo import RSCodec, ReedSolomonError


DATA_SHARDS = 4
PARITY_SHARDS = 2
TOTAL_SHARDS = DATA_SHARDS + PARITY_SHARDS

_codec = RSCodec(PARITY_SHARDS)


def _validate_data_shards(shards):
    if len(shards) != DATA_SHARDS:
        raise ValueError(f"Expected {DATA_SHARDS} data shards")

    shard_size = len(shards[0])

    if any(len(shard) != shard_size for shard in shards):
        raise ValueError("All data shards must be the same size")

    return shard_size


def generate_parity(shards):
    """
    Create Reed-Solomon parity shards for a 4+2 layout.
    """

    shard_size = _validate_data_shards(shards)
    parity = [bytearray(shard_size) for _ in range(PARITY_SHARDS)]

    for offset in range(shard_size):
        stripe = bytes(shard[offset] for shard in shards)
        encoded = _codec.encode(stripe)

        for parity_index in range(PARITY_SHARDS):
            parity[parity_index][offset] = encoded[DATA_SHARDS + parity_index]

    return [bytes(shard) for shard in parity]


def recover_shards(shards, parity):
    """
    Recover missing data/parity shards.

    Missing shards should be represented as None. At most two total shards can
    be missing in the 4+2 layout.
    """

    if len(shards) != DATA_SHARDS:
        raise ValueError(f"Expected {DATA_SHARDS} data shards")
    if len(parity) != PARITY_SHARDS:
        raise ValueError(f"Expected {PARITY_SHARDS} parity shards")

    available = [shard for shard in [*shards, *parity] if shard is not None]

    if not available:
        raise ValueError("At least one shard is required")

    shard_size = len(available[0])

    for shard in available:
        if len(shard) != shard_size:
            raise ValueError("All available shards must be the same size")

    missing_indexes = [
        index
        for index, shard in enumerate([*shards, *parity])
        if shard is None
    ]

    if len(missing_indexes) > PARITY_SHARDS:
        raise ValueError("Too many missing shards to recover")

    recovered = [bytearray(shard_size) for _ in range(TOTAL_SHARDS)]

    for offset in range(shard_size):
        codeword = bytearray(TOTAL_SHARDS)

        for index, shard in enumerate([*shards, *parity]):
            if shard is not None:
                codeword[index] = shard[offset]

        try:
            _, decoded_codeword, _ = _codec.decode(
                codeword,
                erase_pos=missing_indexes,
                only_erasures=True,
            )
        except ReedSolomonError as exc:
            raise ValueError("Unable to recover shards") from exc

        for index, value in enumerate(decoded_codeword):
            recovered[index][offset] = value

    recovered = [bytes(shard) for shard in recovered]

    return recovered[:DATA_SHARDS], recovered[DATA_SHARDS:]


def recover_missing_shard(shards, parity, missing_index):
    """
    Recover one missing data shard from data and parity shards.
    """

    if not isinstance(parity, (list, tuple)):
        raise ValueError("Reed-Solomon recovery requires all parity shards")

    recovered_data, _ = recover_shards(shards, parity)

    return recovered_data[missing_index]
