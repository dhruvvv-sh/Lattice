from sqlalchemy import Column, Integer, String
from sqlalchemy import Column,Integer,String,ForeignKey
from app.database import Base
class Bucket(Base):
    __tablename__ = "buckets"
    id = Column(Integer, primary_key = True, index = True)
    name = Column(String, unique=True,index = True)

class Object(Base):
    __tablename__ = "objects"
    id = Column(Integer,primary_key=True,index = True)
    bucket_id = Column(
        Integer,
        ForeignKey("buckets.id")
    )
    object_name = Column(String, nullable=False)

    file_path = Column(String, nullable=False)

    checksum = Column(String, nullable=False)

    disk_name = Column(String, nullable=False)
    
    size = Column(Integer, nullable=False)
