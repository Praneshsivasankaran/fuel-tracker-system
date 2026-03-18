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

    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == trip.vehicle_id).first()

    benchmark = None
    if vehicle:
        benchmark = db.query(models.VehicleDatabase).filter(
            models.VehicleDatabase.fuel_type == vehicle.fuel_type,
            models.VehicleDatabase.engine_size == vehicle.engine_size
        ).first()

    score = 100
    recommendations = []

    if data.avg_speed > 0:
        if data.avg_speed > 100:
            score -= 25
            recommendations.append("Avg speed too high. Stay under 100 km/h for better fuel efficiency.")
        elif data.avg_speed > 80:
            score -= 10
            recommendations.append("Try to maintain speed between 40-80 km/h for optimal mileage.")
        elif data.avg_speed < 20:
            score -= 5
            recommendations.append("Very low avg speed detected. Heavy traffic reduces efficiency.")

    if data.max_speed > 120:
        score -= 20
        recommendations.append("Max speed exceeded 120 km/h. High speeds drastically reduce fuel efficiency.")
    elif data.max_speed > 100:
        score -= 10
        recommendations.append("Reduce top speed. Every 10 km/h above 80 increases fuel consumption by 10%.")

    if data.avg_acceleration > 5:
        score -= 25
        recommendations.append("Very harsh acceleration detected. Accelerate gradually to save fuel.")
    elif data.avg_acceleration > 3:
        score -= 15
        recommendations.append("Moderate harsh acceleration. Smoother acceleration improves mileage by 15-20%.")
    elif data.avg_acceleration > 2:
        score -= 5
        recommendations.append("Slight aggressive acceleration. Minor improvement possible.")

    if data.avg_speed > 0:
        speed_ratio = data.max_speed / data.avg_speed
        if speed_ratio > 3:
            score -= 10
            recommendations.append("Speed variation too high. Maintain consistent speed for better efficiency.")
        elif speed_ratio > 2:
            score -= 5
            recommendations.append("Moderate speed variation. Try cruise control on highways.")

    benchmark_mileage = None
    if benchmark:
        benchmark_mileage = benchmark.mileage_kmpl
        efficiency_factor = score / 100
        estimated_mileage = benchmark_mileage * efficiency_factor
        if estimated_mileage < benchmark_mileage * 0.6:
            recommendations.append(f"Your driving may achieve only {estimated_mileage:.1f} km/l vs {benchmark_mileage} km/l benchmark.")
        elif estimated_mileage < benchmark_mileage * 0.8:
            recommendations.append(f"Estimated {estimated_mileage:.1f} km/l. Benchmark is {benchmark_mileage} km/l. Room for improvement.")
        else:
            recommendations.append(f"Good! Estimated {estimated_mileage:.1f} km/l close to {benchmark_mileage} km/l benchmark.")

    score = max(0, min(100, score))

    if not recommendations:
        recommendation = "Excellent driving! Optimal fuel efficiency maintained."
    elif score >= 80:
        recommendation = "Good driving. " + recommendations[0]
    elif score >= 60:
        recommendation = "Average driving. " + " | ".join(recommendations[:2])
    else:
        recommendation = "Poor efficiency. " + " | ".join(recommendations[:2])

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

@app.get("/trip/{trip_id}/route")
def get_trip_route(trip_id: int,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    locations = db.query(models.TripLocation).filter(
        models.TripLocation.trip_id == trip_id
    ).order_by(models.TripLocation.timestamp).all()
    return {
        "trip_id": trip_id,
        "start_lat": trip.start_lat,
        "start_lng": trip.start_lng,
        "end_lat": trip.end_lat,
        "end_lng": trip.end_lng,
        "locations": [
            {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "speed": loc.speed,
                "timestamp": str(loc.timestamp)
            }
            for loc in locations
        ]
    }

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    trips = (
        db.query(models.Trip)
        .join(models.Vehicle)
        .filter(models.Vehicle.user_id == current_user.id)
        .filter(models.Trip.is_active == 0)
        .all()
    )
    total_trips = len(trips)
    if total_trips == 0:
        return {
            "total_trips": 0,
            "total_distance": 0,
            "avg_speed": 0,
            "avg_efficiency": 0,
            "max_speed_ever": 0,
            "total_duration": 0,
            "trips_data": []
        }
    total_distance = sum(t.total_distance or 0 for t in trips)
    total_duration = sum(t.trip_duration or 0 for t in trips)
    avg_speed = sum(t.avg_speed or 0 for t in trips) / total_trips
    avg_efficiency = sum(t.efficiency_score or 0 for t in trips) / total_trips
    max_speed_ever = max(t.max_speed or 0 for t in trips)
    trips_data = []
    for t in trips:
        trips_data.append({
            "id": t.id,
            "distance": t.total_distance or 0,
            "avg_speed": t.avg_speed or 0,
            "max_speed": t.max_speed or 0,
            "efficiency_score": t.efficiency_score or 0,
            "duration": t.trip_duration or 0,
            "date": str(t.start_time) if t.start_time else ""
        })
    return {
        "total_trips": total_trips,
        "total_distance": round(total_distance, 2),
        "avg_speed": round(avg_speed, 1),
        "avg_efficiency": round(avg_efficiency, 1),
        "max_speed_ever": round(max_speed_ever, 1),
        "total_duration": round(total_duration, 1),
        "trips_data": trips_data
    }

@app.get("/vehicle-database", response_model=list[schemas.VehicleDatabaseResponse])
def get_vehicle_database(db: Session = Depends(get_db),
                         brand: str = None):
    query = db.query(models.VehicleDatabase)
    if brand:
        query = query.filter(models.VehicleDatabase.brand == brand)
    return query.order_by(models.VehicleDatabase.brand, models.VehicleDatabase.model).all()

@app.get("/vehicle-database/brands")
def get_brands(db: Session = Depends(get_db)):
    brands = db.query(models.VehicleDatabase.brand).distinct().order_by(models.VehicleDatabase.brand).all()
    return [b[0] for b in brands]

@app.get("/vehicle-database/{vehicle_db_id}")
def get_vehicle_benchmark(vehicle_db_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(models.VehicleDatabase).filter(models.VehicleDatabase.id == vehicle_db_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found in database")
    return vehicle

@app.post("/vehicle-database/seed")
def seed_vehicle_database(db: Session = Depends(get_db)):
    existing = db.query(models.VehicleDatabase).count()
    if existing > 0:
        return {"message": f"Database already has {existing} vehicles"}
    vehicles = [
        {"brand": "Maruti Suzuki", "model": "Alto K10", "variant": "VXi", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 24.39, "body_type": "Hatchback"},
        {"brand": "Maruti Suzuki", "model": "Swift", "variant": "ZXi", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 22.38, "body_type": "Hatchback"},
        {"brand": "Maruti Suzuki", "model": "Swift", "variant": "ZDi", "engine_size": 1.3, "fuel_type": "Diesel", "mileage_kmpl": 28.4, "body_type": "Hatchback"},
        {"brand": "Maruti Suzuki", "model": "Baleno", "variant": "Zeta", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 22.35, "body_type": "Hatchback"},
        {"brand": "Maruti Suzuki", "model": "Wagon R", "variant": "ZXi", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 24.35, "body_type": "Hatchback"},
        {"brand": "Maruti Suzuki", "model": "Dzire", "variant": "ZXi", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 22.61, "body_type": "Sedan"},
        {"brand": "Maruti Suzuki", "model": "Ertiga", "variant": "ZXi", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 20.51, "body_type": "MPV"},
        {"brand": "Maruti Suzuki", "model": "Brezza", "variant": "ZXi", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 20.15, "body_type": "SUV"},
        {"brand": "Maruti Suzuki", "model": "Grand Vitara", "variant": "Alpha", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 21.11, "body_type": "SUV"},
        {"brand": "Maruti Suzuki", "model": "Celerio", "variant": "ZXi", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 25.24, "body_type": "Hatchback"},
        {"brand": "Hyundai", "model": "i20", "variant": "Asta", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 20.35, "body_type": "Hatchback"},
        {"brand": "Hyundai", "model": "i20", "variant": "Asta", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 25.2, "body_type": "Hatchback"},
        {"brand": "Hyundai", "model": "Grand i10 Nios", "variant": "Sportz", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 20.7, "body_type": "Hatchback"},
        {"brand": "Hyundai", "model": "Venue", "variant": "SX", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 17.5, "body_type": "SUV"},
        {"brand": "Hyundai", "model": "Venue", "variant": "SX", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 23.4, "body_type": "SUV"},
        {"brand": "Hyundai", "model": "Creta", "variant": "SX", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 16.8, "body_type": "SUV"},
        {"brand": "Hyundai", "model": "Creta", "variant": "SX", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 21.8, "body_type": "SUV"},
        {"brand": "Hyundai", "model": "Verna", "variant": "SX", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 18.6, "body_type": "Sedan"},
        {"brand": "Hyundai", "model": "Tucson", "variant": "Signature", "engine_size": 2.0, "fuel_type": "Petrol", "mileage_kmpl": 14.2, "body_type": "SUV"},
        {"brand": "Hyundai", "model": "Aura", "variant": "SX", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 20.5, "body_type": "Sedan"},
        {"brand": "Tata", "model": "Nexon", "variant": "XZ+", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 17.4, "body_type": "SUV"},
        {"brand": "Tata", "model": "Nexon", "variant": "XZ+", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 23.2, "body_type": "SUV"},
        {"brand": "Tata", "model": "Punch", "variant": "Creative", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 18.97, "body_type": "SUV"},
        {"brand": "Tata", "model": "Altroz", "variant": "XZ+", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 22.0, "body_type": "Hatchback"},
        {"brand": "Tata", "model": "Altroz", "variant": "XZ+", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 25.11, "body_type": "Hatchback"},
        {"brand": "Tata", "model": "Harrier", "variant": "XZ+", "engine_size": 2.0, "fuel_type": "Diesel", "mileage_kmpl": 16.35, "body_type": "SUV"},
        {"brand": "Tata", "model": "Safari", "variant": "XZ+", "engine_size": 2.0, "fuel_type": "Diesel", "mileage_kmpl": 14.5, "body_type": "SUV"},
        {"brand": "Tata", "model": "Tiago", "variant": "XZ+", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 23.84, "body_type": "Hatchback"},
        {"brand": "Tata", "model": "Tigor", "variant": "XZ+", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 20.3, "body_type": "Sedan"},
        {"brand": "Honda", "model": "City", "variant": "ZX", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 18.4, "body_type": "Sedan"},
        {"brand": "Honda", "model": "City", "variant": "ZX", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 24.1, "body_type": "Sedan"},
        {"brand": "Honda", "model": "Amaze", "variant": "VX", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 18.6, "body_type": "Sedan"},
        {"brand": "Honda", "model": "Elevate", "variant": "ZX", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 15.31, "body_type": "SUV"},
        {"brand": "Toyota", "model": "Innova Crysta", "variant": "ZX", "engine_size": 2.4, "fuel_type": "Diesel", "mileage_kmpl": 15.1, "body_type": "MPV"},
        {"brand": "Toyota", "model": "Fortuner", "variant": "4x2", "engine_size": 2.7, "fuel_type": "Petrol", "mileage_kmpl": 10.0, "body_type": "SUV"},
        {"brand": "Toyota", "model": "Glanza", "variant": "V", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 22.35, "body_type": "Hatchback"},
        {"brand": "Toyota", "model": "Urban Cruiser Hyryder", "variant": "V", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 21.1, "body_type": "SUV"},
        {"brand": "Kia", "model": "Seltos", "variant": "HTX", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 16.8, "body_type": "SUV"},
        {"brand": "Kia", "model": "Seltos", "variant": "HTX", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 20.7, "body_type": "SUV"},
        {"brand": "Kia", "model": "Sonet", "variant": "HTX", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 18.2, "body_type": "SUV"},
        {"brand": "Kia", "model": "Sonet", "variant": "HTX", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 24.1, "body_type": "SUV"},
        {"brand": "Kia", "model": "Carens", "variant": "Prestige", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 16.5, "body_type": "MPV"},
        {"brand": "Mahindra", "model": "XUV700", "variant": "AX7", "engine_size": 2.0, "fuel_type": "Petrol", "mileage_kmpl": 13.0, "body_type": "SUV"},
        {"brand": "Mahindra", "model": "XUV700", "variant": "AX7", "engine_size": 2.2, "fuel_type": "Diesel", "mileage_kmpl": 16.0, "body_type": "SUV"},
        {"brand": "Mahindra", "model": "Thar", "variant": "LX", "engine_size": 2.0, "fuel_type": "Petrol", "mileage_kmpl": 15.2, "body_type": "SUV"},
        {"brand": "Mahindra", "model": "Thar", "variant": "LX", "engine_size": 2.2, "fuel_type": "Diesel", "mileage_kmpl": 15.2, "body_type": "SUV"},
        {"brand": "Mahindra", "model": "Scorpio N", "variant": "Z8L", "engine_size": 2.0, "fuel_type": "Petrol", "mileage_kmpl": 11.99, "body_type": "SUV"},
        {"brand": "Mahindra", "model": "Scorpio N", "variant": "Z8L", "engine_size": 2.2, "fuel_type": "Diesel", "mileage_kmpl": 16.55, "body_type": "SUV"},
        {"brand": "Mahindra", "model": "XUV300", "variant": "W8", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 17.0, "body_type": "SUV"},
        {"brand": "Mahindra", "model": "Bolero", "variant": "B6", "engine_size": 1.5, "fuel_type": "Diesel", "mileage_kmpl": 16.0, "body_type": "SUV"},
        {"brand": "MG", "model": "Hector", "variant": "Sharp", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 14.1, "body_type": "SUV"},
        {"brand": "MG", "model": "Astor", "variant": "Sharp", "engine_size": 1.5, "fuel_type": "Petrol", "mileage_kmpl": 15.6, "body_type": "SUV"},
        {"brand": "Volkswagen", "model": "Taigun", "variant": "Topline", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 19.4, "body_type": "SUV"},
        {"brand": "Volkswagen", "model": "Virtus", "variant": "Topline", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 19.4, "body_type": "Sedan"},
        {"brand": "Skoda", "model": "Kushaq", "variant": "Style", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 20.0, "body_type": "SUV"},
        {"brand": "Skoda", "model": "Slavia", "variant": "Style", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 20.0, "body_type": "Sedan"},
        {"brand": "Renault", "model": "Kiger", "variant": "RXZ", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 20.5, "body_type": "SUV"},
        {"brand": "Renault", "model": "Kwid", "variant": "Climber", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 22.3, "body_type": "Hatchback"},
        {"brand": "Nissan", "model": "Magnite", "variant": "XV", "engine_size": 1.0, "fuel_type": "Petrol", "mileage_kmpl": 20.0, "body_type": "SUV"},
        {"brand": "Citroen", "model": "C3", "variant": "Shine", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 19.8, "body_type": "Hatchback"},
        {"brand": "Citroen", "model": "C3 Aircross", "variant": "Shine", "engine_size": 1.2, "fuel_type": "Petrol", "mileage_kmpl": 18.7, "body_type": "SUV"},
    ]
    for v in vehicles:
        db.add(models.VehicleDatabase(**v))
    db.commit()
    return {"message": f"Seeded {len(vehicles)} vehicles successfully"}