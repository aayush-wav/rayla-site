from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# File to store bookings
BOOKINGS_FILE = 'bookings.json'

def save_booking(data):
    bookings = []
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as f:
            try:
                bookings = json.load(f)
            except json.JSONDecodeError:
                bookings = []
    
    # Add timestamp
    data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bookings.append(data)
    
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(bookings, f, indent=4)

@app.route('/api/booking', methods=['POST'])
def handle_booking():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400
    
    # Extract fields
    name = data.get('name')
    email = data.get('email')
    service = data.get('service')
    date = data.get('date')
    
    if not all([name, email, service, date]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Save to file
    save_booking(data)
    
    print(f"New booking received: {name} for {service} on {date}")
    
    return jsonify({
        "status": "success",
        "message": f"Thank you, {name}! Your booking for {service} on {date} has been recorded."
    }), 200

if __name__ == '__main__':
    # Start the server on port 5000
    app.run(debug=True, port=5000)
