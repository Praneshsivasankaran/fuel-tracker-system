const API_URL = "http://127.0.0.1:8000";


// =========================
// LOGIN
// =========================
async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("token", data.access_token);
            window.location.href = "dashboard.html";
        } else {
            document.getElementById("message").innerText = data.detail;
        }

    } catch (error) {
        console.error("Login error:", error);
    }
}


// =========================
// LOGOUT
// =========================
function logout() {
    localStorage.removeItem("token");
    window.location.href = "index.html";
}


// =========================
// LOAD VEHICLES
// =========================
async function loadVehicles() {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "index.html";
        return;
    }

    const response = await fetch(`${API_URL}/vehicles`, {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const vehicles = await response.json();

    const select = document.getElementById("vehicle_select");
    if (!select) return;

    select.innerHTML = "";

    vehicles.forEach(vehicle => {
        const option = document.createElement("option");
        option.value = vehicle.id;
        option.text = `${vehicle.vehicle_model} (ID: ${vehicle.id})`;
        select.appendChild(option);
    });
}


// =========================
// ADD VEHICLE
// =========================
async function addVehicle() {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/vehicles`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            vehicle_model: document.getElementById("vehicle_model").value,
            engine_size: parseFloat(document.getElementById("engine_size").value),
            fuel_type: document.getElementById("fuel_type").value
        })
    });

    const data = await response.json();
    alert("Vehicle Added! ID: " + data.id);

    loadVehicles();
}


// =========================
// ADD TRIP
// =========================
async function addTrip() {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/trips`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            vehicle_id: parseInt(document.getElementById("vehicle_select").value),
            start_time: new Date().toISOString(),
            end_time: new Date().toISOString(),
            total_distance: parseFloat(document.getElementById("distance").value),
            avg_speed: parseFloat(document.getElementById("avg_speed").value),
            max_speed: parseFloat(document.getElementById("max_speed").value),
            avg_acceleration: parseFloat(document.getElementById("avg_acc").value),
            trip_duration: parseFloat(document.getElementById("duration").value)
        })
    });

    const data = await response.json();
    alert("Trip Added! Efficiency Score: " + data.efficiency_score);

    loadTrips();
}


// =========================
// LOAD TRIPS (TABLE VERSION)
// =========================
async function loadTrips() {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/trips`, {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const trips = await response.json();

    const tbody = document.querySelector("#tripTable tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    trips.forEach(trip => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${trip.total_distance}</td>
            <td>${trip.avg_speed}</td>
            <td>${trip.max_speed}</td>
            <td style="color:${trip.efficiency_score >= 80 ? 'green' : 'red'}">
                ${trip.efficiency_score}
            </td>
            <td>${trip.recommendation}</td>
        `;

        tbody.appendChild(row);
    });
}