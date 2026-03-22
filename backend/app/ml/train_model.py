import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

def generate_training_data():
    np.random.seed(42)
    data = []
    
    # More realistic data with vehicle categories
    vehicle_configs = [
        # Cars
        {"engine_range": (0.8, 3.0), "fuel_type": "Petrol", "base_consumption": 6.0, "category": "Car"},
        {"engine_range": (1.3, 2.5), "fuel_type": "Diesel", "base_consumption": 4.5, "category": "Car"},
        # Bikes
        {"engine_range": (0.1, 0.4), "fuel_type": "Petrol", "base_consumption": 1.8, "category": "Bike"},
        # Scooters
        {"engine_range": (0.1, 0.15), "fuel_type": "Petrol", "base_consumption": 1.5, "category": "Scooter"},
    ]
    
    for config in vehicle_configs:
        for _ in range(400):
            engine_size = round(np.random.uniform(*config["engine_range"]), 3)
            fuel_type = config["fuel_type"]
            category = config["category"]
            
            avg_speed = round(np.random.uniform(10, 100), 1)
            max_speed = round(avg_speed * np.random.uniform(1.1, 2.5), 1)
            avg_acceleration = round(np.random.uniform(0.5, 6.0), 2)
            trip_distance = round(np.random.uniform(1, 80), 2)
            trip_duration = round(trip_distance / max(avg_speed, 1) * 60 * np.random.uniform(0.9, 1.4), 2)
            
            # Speed efficiency factor
            if avg_speed < 20:
                speed_factor = 1.3  # city traffic, bad
            elif avg_speed < 40:
                speed_factor = 1.1
            elif avg_speed < 70:
                speed_factor = 0.85  # sweet spot
            elif avg_speed < 90:
                speed_factor = 1.0
            else:
                speed_factor = 1.4  # highway overspeeding
            
            # Acceleration factor
            accel_factor = 1.0 + (avg_acceleration - 2) * 0.12
            accel_factor = max(0.8, min(accel_factor, 1.6))
            
            # Speed variation factor
            speed_ratio = max_speed / max(avg_speed, 1)
            variation_factor = 1.0 + (speed_ratio - 1.5) * 0.08
            
            # Engine size factor
            engine_factor = engine_size / 1.5 if category == "Car" else engine_size / 0.15
            engine_factor = max(0.5, min(engine_factor, 2.5))
            
            # Fuel type factor
            fuel_factor = 1.0 if fuel_type == "Petrol" else 0.82
            
            # Base consumption per km
            base_per_km = config["base_consumption"] / 100
            
            # Final fuel calculation
            fuel_used = (base_per_km * trip_distance * engine_factor * speed_factor * 
                        accel_factor * variation_factor * fuel_factor)
            fuel_used = round(fuel_used * np.random.uniform(0.88, 1.12), 2)
            fuel_used = max(0.05, fuel_used)
            
            # Idle time estimate
            idle_ratio = max(0, (trip_duration - (trip_distance / max(avg_speed, 1) * 60)) / max(trip_duration, 1))
            
            data.append({
                "engine_size": engine_size,
                "fuel_type": 1 if fuel_type == "Petrol" else 0,
                "avg_speed": avg_speed,
                "max_speed": max_speed,
                "avg_acceleration": avg_acceleration,
                "trip_distance": trip_distance,
                "trip_duration": trip_duration,
                "speed_ratio": round(speed_ratio, 2),
                "idle_ratio": round(idle_ratio, 3),
                "speed_squared": round(avg_speed ** 2 / 1000, 2),
                "fuel_used": fuel_used,
            })
    
    return pd.DataFrame(data)

def train():
    print("Generating enhanced training data...")
    df = generate_training_data()
    df.to_csv(os.path.join(os.path.dirname(__file__), "training_data.csv"), index=False)
    print(f"Generated {len(df)} samples")
    
    features = ["engine_size", "fuel_type", "avg_speed", "max_speed", 
                "avg_acceleration", "trip_distance", "trip_duration",
                "speed_ratio", "idle_ratio", "speed_squared"]
    
    X = df[features]
    y = df["fuel_used"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        min_samples_split=5,
        min_samples_leaf=3,
        subsample=0.9,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    # Cross validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    
    print(f"\nModel Performance:")
    print(f"  R2 Score: {r2:.4f}")
    print(f"  MAE: {mae:.4f} litres")
    print(f"  Cross-Val R2: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    # Feature importance
    print(f"\nFeature Importance:")
    importance = sorted(zip(features, model.feature_importances_), key=lambda x: x[1], reverse=True)
    for feat, imp in importance:
        print(f"  {feat}: {imp:.4f}")
    
    model_path = os.path.join(os.path.dirname(__file__), "fuel_model.joblib")
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    train()