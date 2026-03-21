from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///risk.db', connect_args={"check_same_thread": False})
Base = declarative_base()

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)

    # Basic info
    country = Column(String)
    company = Column(String)
    route = Column(String)

    # Shipment data
    weight = Column(Integer)
    hour = Column(Integer)

    # Risk
    risk_score = Column(Integer)

    # Tracking
    vehicle_id = Column(String)   # registreringsnummer
    notes = Column(String)        # anteckningar
    timestamp = Column(String)    # tid

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
