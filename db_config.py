"""
Модуль конфигурации базы данных SQLite.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from sqlalchemy.orm import Session

# Конфигурация подключения к базе данных SQLite
DATABASE_URL = "sqlite:///beauty_salon.db"

# Создаем движок SQLAlchemy для SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Необходимо для SQLite
    echo=False  # Включить для отладки SQL-запросов
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс для всех моделей
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Генератор сессий базы данных.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()