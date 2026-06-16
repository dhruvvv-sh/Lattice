from sqlalchemy import Column, Integer, String
from app.database import Base
class Bucket(Base):
    __tablename__ = "buckets"
    id = Column(Integer, primary_key = True, index = True)
    name = Column(String, unique=True,index = True)

class Objects(Base):
    __tablename__ = "objects"
    id = Column(Integer,primary_key=True,index = True)
    name = Column(String)
    bucket_id = Column(Integer)