from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


# -------------------------
# USER MODEL
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)

    vehicles = relationship("Vehicle", back_populates="owner")


# -------------------------
# VEHICLE MODEL
# -------------------------
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_model = Column(String, nullable=False)
    engine_size = Column(Float, nullable=False)
    fuel_type = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="vehicles")
    trips = relationship("Trip", back_populates="vehicle")


# -------------------------
# TRIP MODEL
# -------------------------
class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))

    start_time = Column(DateTime)
    end_time = Column(DateTime)

    total_distance = Column(Float)
    avg_speed = Column(Float)
    max_speed = Column(Float)
    avg_acceleration = Column(Float)
    trip_duration = Column(Float)

    efficiency_score = Column(Integer)
    recommendation = Column(String)

    vehicle = relationship("Vehicle", back_populates="trips")