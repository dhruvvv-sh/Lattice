import os

from app.storage_engine.disk_selector import get_next_disk


def save_file(bucket_id: int, file):

    # Select disk using round robin
    disk = get_next_disk()

    # Create bucket folder inside selected disk
    bucket_folder = f"storage/{disk}/bucket_{bucket_id}"
    os.makedirs(bucket_folder, exist_ok=True)

    # Full file path
    filepath = os.path.join(
        bucket_folder,
        file.filename
    )

    # Save file
    with open(filepath, "wb") as buffer:
        buffer.write(file.file.read())

    # Return both path and disk name
    return filepath, disk