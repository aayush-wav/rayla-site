# Nails by Rayla Backend

A lightweight Python/Flask backend for handling booking requests.

## Setup

1. Make sure you have Python installed.
2. Install the requirements:
   ```bash
   pip install flask flask-cors
   ```

## Running the Server

From the project root:
```bash
python backend/app.py
```

The server will start at `http://localhost:5000`.

## Functionality

- **Endpoint**: `POST /api/booking`
- **Storage**: Bookings are saved to `backend/bookings.json`.
- **Validation**: Ensures all required fields (name, email, service, date) are present.
