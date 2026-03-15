from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# -------------------------
# USER SCHEMAS
# -------------------------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


# -------------------------
# LOGIN SCHEMAS
# -------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# -------------------------
# VEHICLE SCHEMAS
# -------------------------
class VehicleCreate(BaseModel):
    vehicle_model: str
    engine_size: float
    fuel_type: str


class VehicleResponse(BaseModel):
    id: int
    vehicle_model: str
    engine_size: float
    fuel_type: str

    class Config:
        from_attributes = True


# -------------------------
# TRIP SCHEMAS (manual entry - existing)
# -------------------------
class TripCreate(BaseModel):
    vehicle_id: int
    start_time: datetime
    end_time: datetime
    total_distance: float
    avg_speed: float
    max_speed: float
    avg_acceleration: float
    trip_duration: float


class TripResponse(BaseModel):
    id: int
    vehicle_id: int
    total_distance: Optional[float] = None
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    avg_acceleration: Optional[float] = None
    trip_duration: Optional[float] = None
    efficiency_score: Optional[int] = None
    recommendation: Optional[str] = None
    is_active: Optional[int] = 0
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None

    class Config:
        from_attributes = True


# -------------------------
# TRIP START SCHEMA (mobile app)
# -------------------------
class TripStartRequest(BaseModel):
    vehicle_id: int
    start_lat: float
    start_lng: float


class TripStartResponse(BaseModel):
    id: int
    vehicle_id: int
    is_active: int

    class Config:
        from_attributes = True


# -------------------------
# GPS LOCATION SCHEMA
# -------------------------
class LocationCreate(BaseModel):
    trip_id: int
    latitude: float
    longitude: float
    speed: float


# -------------------------
# TRIP END SCHEMA
# -------------------------
class TripEndRequest(BaseModel):
    trip_id: int
    end_lat: float
    end_lng: float
    total_distance: float
    avg_speed: float
    max_speed: float
    avg_acceleration: float
    trip_duration: float