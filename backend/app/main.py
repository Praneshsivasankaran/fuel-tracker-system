from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app import models, schemas
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fuel Tracking Application")

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
def root():
    return {"message": "Fuel Tracker Backend Running Successfully"}

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.TokenResponse)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }

@app.post("/vehicles", response_model=schemas.VehicleResponse)
def add_vehicle(vehicle: schemas.VehicleCreate,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    new_vehicle = models.Vehicle(
        vehicle_model=vehicle.vehicle_model,
        engine_size=vehicle.engine_size,
        fuel_type=vehicle.fuel_type,
        user_id=current_user.id
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

@app.get("/vehicles", response_model=list[schemas.VehicleResponse])
def get_my_vehicles(db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    return db.query(models.Vehicle).filter(models.Vehicle.user_id == current_user.id).all()

@app.post("/trips", response_model=schemas.TripResponse)
def add_trip(trip: schemas.TripCreate,
             db: Session = Depends(get_db),
             current_user: models.User = Depends(get_current_user)):
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.id == trip.vehicle_id,
        models.Vehicle.user_id == current_user.id
    ).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    score = 100
    recommendation = "Good driving behavior."
    if trip.max_speed > 100:
        score -= 20
        recommendation = "Reduce overspeeding."
    if trip.avg_acceleration > 3:
        score -= 20
        recommendation = "Avoid harsh acceleration."
    new_trip = models.Trip(
        vehicle_id=trip.vehicle_id,
        start_time=trip.start_time,
        end_time=trip.end_time,
        total_distance=trip.total_distance,
        avg_speed=trip.avg_speed,
        max_speed=trip.max_speed,
        avg_acceleration=trip.avg_acceleration,
        trip_duration=trip.trip_duration,
        efficiency_score=score,
        recommendation=recommendation
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    return new_trip

@app.get("/trips", response_model=list[schemas.TripResponse])
def get_trips(db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    return (
        db.query(models.Trip)
        .join(models.Vehicle)
        .filter(models.Vehicle.user_id == current_user.id)
        .all()
    )

@app.post("/trip/start", response_model=schemas.TripStartResponse)
def start_trip(data: schemas.TripStartRequest,
               db: Session = Depends(get_db),
               current_user: models.User = Depends(get_current_user)):
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.id == data.vehicle_id,
        models.Vehicle.user_id == current_user.id
    ).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    trip = models.Trip(
        vehicle_id=data.vehicle_id,
        start_time=datetime.utcnow(),
        start_lat=data.start_lat,
        start_lng=data.start_lng,
        is_active=1
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@app.post("/trip/location")
def add_location(data: schemas.LocationCreate,
                 db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.id == data.trip_id).first()
    if not trip or trip.is_active != 1:
        raise HTTPException(status_code=400, detail="Trip not active")
    location = models.TripLocation(
        trip_id=data.trip_id,
        latitude=data.latitude,
        longitude=data.longitude,
        speed=data.speed
    )
    db.add(location)
    db.commit()
    return {"status": "location saved"}

@app.post("/trip/end", response_model=schemas.TripResponse)
def end_trip(data: schemas.TripEndRequest,
             db: Session = Depends(get_db),
             current_user: models.User = Depends(get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.id == data.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    score = 100
    recommendation = "Good driving behavior."
    if data.max_speed > 100:
        score -= 20
        recommendation = "Reduce overspeeding."
    if data.avg_acceleration > 3:
        score -= 20
        recommendation = "Avoid harsh acceleration."
    trip.end_time = datetime.utcnow()
    trip.end_lat = data.end_lat
    trip.end_lng = data.end_lng
    trip.total_distance = data.total_distance
    trip.avg_speed = data.avg_speed
    trip.max_speed = data.max_speed
    trip.avg_acceleration = data.avg_acceleration
    trip.trip_duration = data.trip_duration
    trip.efficiency_score = score
    trip.recommendation = recommendation
    trip.is_active = 0
    db.commit()
    db.refresh(trip)
    return trip
