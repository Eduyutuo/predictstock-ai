"""
database.py - Configuración de la base de datos SQLite con SQLAlchemy.

Provee el engine, la sesión y el modelo ORM para los registros de ventas.
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, Date
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./predictstock.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Requerido para SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SalesRecord(Base):
    """Modelo ORM para registros de ventas históricos."""

    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(Date, nullable=False, index=True)
    producto_id = Column(String(50), nullable=False, index=True)
    cantidad_vendida = Column(Integer, nullable=False)
    precio = Column(Float, nullable=False)
    stock_actual = Column(Integer, nullable=False)


def init_db():
    """Crea todas las tablas en la base de datos si no existen."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Generador de sesiones de base de datos para inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
