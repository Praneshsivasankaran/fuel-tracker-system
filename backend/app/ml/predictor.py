import joblib
import os
import numpy as np

model_path = os.path.join(os.path.dirname(__file__), 'fuel_model.joblib')
model = joblib.load(model_path)

def predict_fuel(engine_size, fuel_type, avg_speed, max_speed, avg_acceleration, trip_distance, trip_duration):
    """Predict fuel consumption in litres"""
    fuel_type_code = 1 if fuel_type.lower() == 'diesel' else 0
    
    features = np.array([[
        engine_size,
        fuel_type_code,
        avg_speed,
        max_speed,
        avg_acceleration,
        trip_distance,
        trip_duration
    ]])
    
    prediction = model.predict(features)[0]
    return round(max(0.01, prediction), 3)