from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import os
from pymongo.errors import ConnectionFailure

app = Flask(__name__)
CORS(app)

#URI is set in the Render's Evnironment
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    print("MONGO_URI is not set in environment variables.")
    exit(1)

# Resolving TLS issue of MONGO DB
if "tls=true" not in MONGO_URI:
    MONGO_URI += "&tls=true"

app.config["MONGO_URI"] = MONGO_URI

#Checking if the DB connecetion is successful, if not then exit and don't proceed further
try:
    mongo = PyMongo(app)
    mongo.cx.server_info()
    print("Connection with MongoDB is successful.")
except ConnectionFailure as e:
    print("Connection with MongoDB is failing:", e)
    exit(1)

appointments_collection = mongo.db.appointments

#Creating POST API where the patients can add the timeslot with doctors
@app.route("/api/appointments/book", methods=["POST"])
def book_patient_appointment():
    data = request.get_json()

    required_fields = ["patient_id", "doctor_id", "appointment_time", "reason"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "You haven't added all fields"}), 400

    try:
        appointment_time = datetime.fromisoformat(data["appointment_time"])
    except ValueError:
        return jsonify({"error": "Only ISO format is supported by MediConnect. Please use correct format"}), 400

    # Checking if the doctor has other appointment
    doctor_availability = appointments_collection.find_one({
        "doctor_id": data["doctor_id"],
        "appointment_time": appointment_time
    })
    if doctor_availability:
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


# Creating GET API where Patient's information can be fetched
@app.route("/api/appointments/patient/<patient_id>", methods=["GET"])
def get_patient_appointments(patient_id):
    booked_appointments = list(appointments_collection.find({"patient_id": patient_id}))

    if not booked_appointments:
        return jsonify({"message": "Sorry, you haven't booked any appointments with us."}), 404

    result = []
    for a in booked_appointments:
        result.append({
            "appointment_id": str(a["_id"]),
            "doctor_id": a["doctor_id"],
            "appointment_time": a["appointment_time"].isoformat(),
            "reason": a["reason"],
            "status": a["status"]
        })

    return jsonify(result), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

