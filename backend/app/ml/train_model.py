import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

def generate_training_data(n_samples=5000):
    """Generate synthetic driving data based on real vehicle benchmarks"""
    np.random.seed(42)
    
    # Indian vehicle benchmarks: (engine_size, fuel_type_code, base_mileage_kmpl)
    vehicles = [
        (1.0, 0, 24.0),   # Alto, Celerio
        (1.2, 0, 21.0),   # Swift, i20, Baleno
        (1.2, 0, 18.0),   # Nexon, Punch
        (1.5, 0, 17.5),   # Venue, Creta, City
        (1.5, 1, 23.0),   # Nexon Diesel, Venue Diesel
        (2.0, 0, 13.5),   # XUV700, Thar
        (2.0, 1, 15.5),   # Harrier, Safari
        (2.2, 1, 16.0),   # XUV700 Diesel, Scorpio
        (2.4, 1, 15.0),   # Innova
        (2.7, 0, 10.0),   # Fortuner
    ]
    
    data = []
    
    for _ in range(n_samples):
        # Pick random vehicle
        engine_size, fuel_type, base_mileage = vehicles[np.random.randint(0, len(vehicles))]
        
        # Generate driving parameters
        avg_speed = np.random.uniform(15, 120)
        max_speed = avg_speed * np.random.uniform(1.1, 2.5)
        avg_acceleration = np.random.uniform(0.5, 6.0)
        trip_distance = np.random.uniform(2, 100)
        trip_duration = (trip_distance / avg_speed) * 60  # minutes
        
        # Calculate fuel consumption based on physics
        # Base consumption from benchmark
        base_consumption = trip_distance / base_mileage
        
        # Speed factor: optimal is 40-80 km/h
        if avg_speed < 20:
            speed_factor = 1.4  # heavy traffic, lots of idling
        elif avg_speed < 40:
            speed_factor = 1.15
        elif avg_speed <= 80:
            speed_factor = 1.0  # optimal range
        elif avg_speed <= 100:
            speed_factor = 1.15
        elif avg_speed <= 120:
            speed_factor = 1.35
        else:
            speed_factor = 1.6
        
        # Acceleration factor
        if avg_acceleration > 5:
            accel_factor = 1.35
        elif avg_acceleration > 3:
            accel_factor = 1.2
        elif avg_acceleration > 2:
            accel_factor = 1.1
        else:
            accel_factor = 1.0
        
        # Speed variation factor
        speed_ratio = max_speed / max(avg_speed, 1)
        if speed_ratio > 3:
            variation_factor = 1.2
        elif speed_ratio > 2:
            variation_factor = 1.1
        else:
            variation_factor = 1.0
        
        # Final fuel consumption (litres)
        fuel_consumed = base_consumption * speed_factor * accel_factor * variation_factor
        
        # Add some noise
        fuel_consumed *= np.random.uniform(0.9, 1.1)
        fuel_consumed = max(0.1, fuel_consumed)
        
        data.append({
            'engine_size': engine_size,
            'fuel_type': fuel_type,
            'avg_speed': round(avg_speed, 1),
            'max_speed': round(max_speed, 1),
            'avg_acceleration': round(avg_acceleration, 2),
            'trip_distance': round(trip_distance, 2),
            'trip_duration': round(trip_duration, 2),
            'fuel_consumed': round(fuel_consumed, 3)
        })
    
    return pd.DataFrame(data)


def train_model():
    """Train the fuel prediction model"""
    print("Generating training data...")
    df = generate_training_data(5000)
    
    print(f"Dataset shape: {df.shape}")
    print(f"\nSample data:")
    print(df.head())
    print(f"\nFuel consumed stats:")
    print(df['fuel_consumed'].describe())
    
    # Features and target
    features = ['engine_size', 'fuel_type', 'avg_speed', 'max_speed', 
                'avg_acceleration', 'trip_distance', 'trip_duration']
    X = df[features]
    y = df['fuel_consumed']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Random Forest model
    print("\nTraining Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\nModel Performance:")
    print(f"  MAE: {mae:.4f} litres")
    print(f"  R2 Score: {r2:.4f}")
    
    # Feature importance
    print(f"\nFeature Importance:")
    for feat, imp in sorted(zip(features, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {feat}: {imp:.4f}")
    
    # Save model
    model_path = os.path.join(os.path.dirname(__file__), 'fuel_model.joblib')
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")
    
    # Save training data for reference
    data_path = os.path.join(os.path.dirname(__file__), 'training_data.csv')
    df.to_csv(data_path, index=False)
    print(f"Training data saved to {data_path}")
    
    return model


if __name__ == "__main__":
    train_model()