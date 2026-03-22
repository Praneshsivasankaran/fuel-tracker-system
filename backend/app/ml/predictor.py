import joblib
import numpy as np
import os

model_path = os.path.join(os.path.dirname(__file__), "fuel_model.joblib")
model = joblib.load(model_path)

def predict_fuel(engine_size, fuel_type, avg_speed, max_speed, avg_acceleration, trip_distance, trip_duration):
    fuel_encoded = 1 if fuel_type == "Petrol" else 0
    speed_ratio = max_speed / max(avg_speed, 1)
    idle_ratio = max(0, (trip_duration - (trip_distance / max(avg_speed, 1) * 60)) / max(trip_duration, 1))
    speed_squared = avg_speed ** 2 / 1000
    
    features = np.array([[
        engine_size, fuel_encoded, avg_speed, max_speed,
        avg_acceleration, trip_distance, trip_duration,
        speed_ratio, idle_ratio, speed_squared
    ]])
    
    prediction = model.predict(features)[0]
    return round(max(0.01, prediction), 2)