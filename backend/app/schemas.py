from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


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
    start_time: Optional[datetime] = None
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


class LocationCreate(BaseModel):
    trip_id: int
    latitude: float
    longitude: float
    speed: float


class TripEndRequest(BaseModel):
    trip_id: int
    end_lat: float
    end_lng: float
    total_distance: float
    avg_speed: float
    max_speed: float
    avg_acceleration: float
    trip_duration: float


class VehicleDatabaseResponse(BaseModel):
    id: int
    brand: str
    model: str
    variant: Optional[str] = None
    engine_size: Optional[float] = None
    fuel_type: Optional[str] = None
    mileage_kmpl: Optional[float] = None
    body_type: Optional[str] = None

    class Config:
        from_attributes = True