"""
Модели базы данных для салона красоты.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from db_config import Base

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    telegram_id = Column(Integer, unique=True)
    
    bookings = relationship("Booking", back_populates="client")

class Service(Base):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    duration = Column(Integer, nullable=False)  # в минутах
    price = Column(Integer, nullable=False)
    
    bookings = relationship("Booking", back_populates="service")

class Master(Base):
    __tablename__ = 'masters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    specialization = Column(String)
    
    schedules = relationship("Schedule", back_populates="master")
    bookings = relationship("Booking", back_populates="master")

class Schedule(Base):
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey('masters.id'), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(String, nullable=False)  # Формат HH:MM
    end_time = Column(String, nullable=False)   # Формат HH:MM
    
    master = relationship("Master", back_populates="schedules")

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    master_id = Column(Integer, ForeignKey('masters.id'), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(String, nullable=False)  # Формат HH:MM
    end_time = Column(String, nullable=False)   # Формат HH:MM
    status = Column(String, default='confirmed')  # confirmed, cancelled
    
    client = relationship("Client", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    master = relationship("Master", back_populates="bookings")