from pydantic import BaseModel

class BucketCreate(BaseModel):
    name:str

class ObjectCreate(BaseModel):
    name:str
    bucket_id : int