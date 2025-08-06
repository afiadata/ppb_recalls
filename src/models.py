from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import Text 

Base = declarative_base()

class Recall(Base):
    __tablename__ = 'recalls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer)
    product_name = Column(Text)
    inn_name = Column(Text)
    manufacturer = Column(Text)
    reason = Column(Text) 
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    
    