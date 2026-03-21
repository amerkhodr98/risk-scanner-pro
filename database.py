from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

# ==============================
# DATABASE SETUP
# ==============================
engine = create_engine(
    'sqlite:///risk.db',
    connect_args={"check_same_thread": False}
)

Base = declarative_base()

# ==============================
# TABLE
# ==============================
class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)

    # BASIC INFO
    country = Column(String)
    company = Column(String)
    route = Column(String)

    # SHIPMENT DATA
    weight = Column(Integer)
    hour = Column(Integer)

    # RISK
    risk_score = Column(Integer)

    # TRACKING SYSTEM
    vehicle_id = Column(String)   # registreringsnummer
    notes = Column(String)        # anteckningar
    timestamp = Column(String)    # datum/tid

# ==============================
# CREATE DATABASE (SAFE VERSION)
# ==============================
def init_db():
    Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
