from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True)
    is_admin = Column(Boolean, default=False)
    last_request = Column(DateTime)

class Submission(Base):
    __tablename__ = 'submissions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    content_type = Column(String(50), default='text')  # Добавляем значение по умолчанию
    content = Column(Text)
    media_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)