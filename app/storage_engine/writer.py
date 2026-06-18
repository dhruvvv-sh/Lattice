#Given a bucket ID and an uploaded file, save it to disk and return the file path.
import os
def save_file(bucket_id:int, file):
    bucket_folder = f"storage/bucket_{bucket_id}"
    os.makedirs(bucket_folder,exist_ok=True) # basically if this folder already exists, don't crash, just move on
    filepath = os.path.join(
        bucket_folder,
        file.filename
    )#This combines the folder path and the original filename (e.g., photo.jpg) into a single, clean path (like storage/bucket_105/photo.jpg).
    with open(filepath,"wb") as buffer: #writes this to the disk : WB -> write binary since objects
        buffer.write(file.file.read()) #reads raw binary so that it can be stored in buffer.write permanently
    return filepath
