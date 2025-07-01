from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import os
from pymongo.errors import ConnectionFailure

app = Flask(__name__)
CORS(app)

# ✅ Use Render environment variable and force TLS
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    print("❌ MONGO_URI is not set in environment variables.")
    exit(1)

# ✅ Add TLS fix
if "tls=true" not in MONGO_URI:
    MONGO_URI += "&tls=true"

app.config["MONGO_URI"] = MONGO_URI

try:
    mongo = PyMongo(app)
    mongo.cx.server_info()  # Force connection test
    print("✅ MongoDB connected successfully.")
except ConnectionFailure as e:
    print("❌ MongoDB connection failed:", e)
    exit(1)

appointments_collection = mongo.db.appointments

# 📌 POST /api/appointments/book
@app.route("/api/appointments/book", methods=["POST"])
def book_appointment():
    data = request.get_json()

    required_fields = ["patient_id", "doctor_id", "appointment_time", "reason"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        appointment_time = datetime.fromisoformat(data["appointment_time"])
    except ValueError:
        return jsonify({"error": "Only ISO format is supported by MediConnect. Please use correct format"}), 400

    # Conflict detection
    conflict = appointments_collection.find_one({
        "doctor_id": data["doctor_id"],
        "appointment_time": appointment_time
    })
    if conflict:
        return jsonify({"error": "Please use a different time slot, as this is already booked."}), 409

    result = appointments_collection.insert_one({
        "patient_id": data["patient_id"],
        "doctor_id": data["doctor_id"],
        "appointment_time": appointment_time,
        "reason": data["reason"],
        "status": "confirmed"
    })

    return jsonify({
        "message": "Appointment booked successfully",
        "appointment_id": str(result.inserted_id)
    }), 201


# 📌 GET /api/appointments/patient/<patient_id>
@app.route("/api/appointments/patient/<patient_id>", methods=["GET"])
def get_patient_appointments(patient_id):
    appointments = list(appointments_collection.find({"patient_id": patient_id}))

    if not appointments:
        return jsonify({"message": "Sorry, you haven't booked any appointments with us."}), 404

    result = []
    for a in appointments:
        result.append({
            "appointment_id": str(a["_id"]),
            "doctor_id": a["doctor_id"],
            "appointment_time": a["appointment_time"].isoformat(),
            "reason": a["reason"],
            "status": a["status"]
        })

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True)
