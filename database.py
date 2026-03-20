from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(
    'sqlite:///risk.db',
    connect_args={"check_same_thread": False}
)

Base = declarative_base()

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)
    country = Column(String)
    weight = Column(Integer)
    route = Column(String)
    company = Column(String)
    risk_score = Column(Integer)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
