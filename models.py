import os
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_number = Column(String)
    payment_datetime = Column(DateTime)
    total_amount = Column(Float)
    transferred_amount = Column(Float)
    commission = Column(Float)
    service_provider = Column(String)
    service_type = Column(String)
    payer_name = Column(String)
    address = Column(String)
    bank_terminal = Column(String)
    payment_status = Column(String)
    raw_file_path = Column(String, nullable=True)
    extracted_at = Column(DateTime, default=datetime.utcnow)


db_url = os.environ.get("DATABASE_URL", "sqlite:///komunalka.db")
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return Session()
