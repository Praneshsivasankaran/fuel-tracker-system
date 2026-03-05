from pydantic import BaseModel, EmailStr
from datetime import datetime


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
# DRIVING DATA SCHEMAS
# -------------------------
class DrivingDataCreate(BaseModel):
    vehicle_id: int
    speed: float
    acceleration: float
    distance: float
    fuel_used: float


class DrivingDataResponse(BaseModel):
    id: int
    speed: float
    acceleration: float
    distance: float
    fuel_used: float

    class Config:
        from_attributes = True

# -------------------------
# TRIP SCHEMAS
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
    total_distance: float
    avg_speed: float
    max_speed: float
    avg_acceleration: float
    trip_duration: float
    efficiency_score: int
    recommendation: str

    class Config:
        from_attributes = True