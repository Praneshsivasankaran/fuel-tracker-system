# ⚙️ Fuel Tracker System — Backend API

A scalable **FastAPI backend** for a smart driving analytics system that processes real-time GPS trip data, predicts fuel consumption using Machine Learning, and powers dashboard analytics, charts, and map visualizations.

---

## 🚀 Overview

This backend is designed to support a full-stack mobile application by handling:

- Real-time trip tracking
- Driving behavior analysis
- Machine learning predictions
- Analytics data for charts & dashboards

It is built with production-ready architecture using FastAPI, PostgreSQL, and scikit-learn.

---

## ✨ Features

### 🔐 Authentication
- JWT-based user authentication
- Secure login and registration system

### 🚘 Vehicle Management
- Add, list, and delete user vehicles
- Pre-seeded Indian vehicle database (87+ vehicles)

### 📍 Trip Tracking
- Start and end trips
- Real-time GPS location updates
- Route data storage for map visualization

### ⛽ Machine Learning Prediction
- Predict fuel consumption after each trip
- Uses Gradient Boosting Regressor
- High accuracy model (R² = 0.94)

### 📊 Driving Analytics
- Driving efficiency score (0–100)
- Speed and acceleration analysis
- Trip history and performance tracking
- Data structured for frontend charts

### 🧠 Smart Scoring Algorithm
- Evaluates:
  - Speed patterns
  - Acceleration behavior
  - Speed variation
- Compares against official mileage benchmarks

---

## 🛠 Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT
- **Machine Learning:** scikit-learn
- **Deployment:** Render

---

## 🧠 Machine Learning Model

- **Algorithm:** Gradient Boosting Regressor  
- **Training Samples:** 1600+  
- **Features Used:**
  - Average Speed
  - Max Speed
  - Acceleration
  - Trip Distance & Duration
  - Idle Ratio
- **Performance:**
  - R² Score: 0.94  
  - MAE: 0.32L  

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | Authenticate user |
| GET | `/me` | Get current user |
| POST | `/vehicles` | Add vehicle |
| GET | `/vehicles` | List vehicles |
| DELETE | `/vehicles/{id}` | Delete vehicle |
| POST | `/trip/start` | Start trip |
| POST | `/trip/location` | Send GPS data |
| POST | `/trip/end` | End trip + prediction |
| GET | `/trip/{id}/route` | Get trip route |
| GET | `/trips` | List trips |
| DELETE | `/trips/{id}` | Delete trip |
| GET | `/analytics` | Get analytics data |
| GET | `/vehicle-database` | Vehicle data |
| GET | `/vehicle-database/brands` | Vehicle brands |

---

## 📊 Analytics & Insights

The backend provides structured data for frontend dashboards and charts:

- Speed trends
- Distance analysis
- Fuel efficiency insights
- Driving score visualization
- Benchmark comparison with official mileage

These APIs are optimized for integration with chart libraries and analytics dashboards.

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Praneshsivasankaran/fuel-tracker-system.git
cd fuel-tracker-system
