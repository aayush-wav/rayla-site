from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# --- Configuration ---
BOOKINGS_FILE = 'bookings.json'
BLOCKED_DAYS_FILE = 'blocked_days.json'
ADMIN_PASSWORD = 'rayla_admin_2026'

# Salon hours — 30-min slots from 10:00 to 19:00
ALL_SLOTS = [
    "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30",
    "18:00", "18:30"
]

# --- Auth ---
def check_auth(username, password):
    return username == 'admin' and password == ADMIN_PASSWORD

def authenticate():
    return jsonify({"message": "Authentication required"}), 401, {
        'WWW-Authenticate': 'Basic realm="Login Required"'
    }

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- Data helpers ---
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# --- Public API ---

@app.route('/api/availability')
def get_availability():
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Date required"}), 400

    blocked_days = load_json(BLOCKED_DAYS_FILE)
    if date in blocked_days:
        return jsonify({"blocked": True, "available_slots": []})

    bookings = load_json(BOOKINGS_FILE)
    booked_times = {b['time'] for b in bookings if b.get('date') == date}
    available = [s for s in ALL_SLOTS if s not in booked_times]

    return jsonify({"blocked": False, "available_slots": available, "booked_slots": list(booked_times)})

@app.route('/api/booking', methods=['POST'])
def handle_booking():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    name = data.get('name')
    phone = data.get('phone')
    service = data.get('service')
    date = data.get('date')
    time = data.get('time')

    if not all([name, phone, service, date, time]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if day is blocked
    blocked_days = load_json(BLOCKED_DAYS_FILE)
    if date in blocked_days:
        return jsonify({"error": "Sorry, this day is fully booked. Please choose another date."}), 409

    # Check if time slot is taken
    bookings = load_json(BOOKINGS_FILE)
    for b in bookings:
        if b.get('date') == date and b.get('time') == time:
            return jsonify({"error": f"The {time} slot on {date} is already taken. Please choose a different time."}), 409

    data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bookings.append(data)
    save_json(BOOKINGS_FILE, bookings)

    return jsonify({
        "status": "success",
        "message": f"Thank you, {name}! Your {service} appointment is confirmed for {date} at {time}."
    }), 200

# --- Admin Panel ---

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Rayla Admin | Bookings</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #36454f; --accent: #f8e1e1; --bg: #f5f7f8; --danger: #e74c3c; --success: #27ae60; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--primary); }
        .sidebar { position: fixed; top: 0; left: 0; width: 220px; height: 100vh; background: var(--primary); color: white; padding: 30px 20px; }
        .sidebar h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; margin-bottom: 30px; }
        .sidebar a { display: block; color: rgba(255,255,255,0.7); text-decoration: none; padding: 10px 12px; border-radius: 8px; margin-bottom: 5px; font-size: 0.9rem; transition: all 0.2s; }
        .sidebar a:hover, .sidebar a.active { background: rgba(255,255,255,0.15); color: white; }
        .main { margin-left: 220px; padding: 40px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        h1 { font-family: 'Playfair Display', serif; font-size: 2rem; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 35px; }
        .card { background: white; padding: 24px; border-radius: 14px; box-shadow: 0 2px 15px rgba(0,0,0,0.06); }
        .card h3 { font-size: 0.8rem; text-transform: uppercase; color: #999; letter-spacing: 1px; margin-bottom: 10px; }
        .card .value { font-size: 2.2rem; font-weight: 600; }
        .section { background: white; border-radius: 14px; box-shadow: 0 2px 15px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 30px; }
        .section-header { padding: 20px 24px; border-bottom: 1px solid #f0f0f0; font-weight: 600; font-size: 1rem; display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #fafafa; text-align: left; padding: 12px 20px; font-size: 0.8rem; text-transform: uppercase; color: #999; letter-spacing: 0.5px; }
        td { padding: 14px 20px; border-bottom: 1px solid #f5f5f5; font-size: 0.95rem; }
        tr:last-child td { border-bottom: none; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; }
        .badge-service { background: var(--accent); color: var(--primary); }
        .badge-blocked { background: #fde8e8; color: var(--danger); }
        .block-form { padding: 20px 24px; display: flex; gap: 12px; align-items: center; }
        .block-form input[type=date] { padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-family: 'Inter', sans-serif; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-family: 'Inter', sans-serif; font-weight: 500; transition: opacity 0.2s; }
        .btn:hover { opacity: 0.85; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-danger { background: var(--danger); color: white; font-size: 0.8rem; padding: 6px 12px; }
        .blocked-list { display: flex; flex-wrap: wrap; gap: 10px; padding: 20px 24px; }
        .blocked-tag { background: #fde8e8; color: var(--danger); padding: 8px 14px; border-radius: 8px; display: flex; align-items: center; gap: 10px; font-size: 0.9rem; }
        .blocked-tag form { display: inline; }
        .empty { padding: 30px 24px; color: #aaa; font-style: italic; }
        .time-badge { background: #e8f4fd; color: #2980b9; padding: 3px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 500; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>Rayla Admin</h2>
        <a href="/admin" class="active">📋 Bookings</a>
        <a href="/admin/blocked">🚫 Block Days</a>
    </div>
    <div class="main">
        <div class="page-header">
            <h1>Bookings</h1>
            <button class="btn btn-primary" onclick="location.reload()">↻ Refresh</button>
        </div>

        <div class="stats">
            <div class="card">
                <h3>Total Bookings</h3>
                <div class="value">{{ total }}</div>
            </div>
            <div class="card">
                <h3>Blocked Days</h3>
                <div class="value">{{ blocked_count }}</div>
            </div>
            <div class="card">
                <h3>Latest Booking</h3>
                <div class="value" style="font-size: 1rem; line-height: 1.4;">{{ latest }}</div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">All Appointments</div>
            <table>
                <thead>
                    <tr>
                        <th>Submitted</th>
                        <th>Client</th>
                        <th>Phone</th>
                        <th>Category</th>
                        <th>Treatment</th>
                        <th>Date</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    {% for b in bookings %}
                    <tr>
                        <td style="color:#aaa; font-size:0.85rem;">{{ b.timestamp }}</td>
                        <td><strong>{{ b.name }}</strong></td>
                        <td>{{ b.phone if b.phone else b.email if b.email else '—' }}</td>
                        <td><span class="badge badge-service">{{ b.service }}</span></td>
                        <td style="color:#555; font-style:italic;">{{ b.sub_service if b.sub_service else '—' }}</td>
                        <td>{{ b.date }}</td>
                        <td><span class="time-badge">{{ b.time if b.time else '—' }}</span></td>
                    </tr>
                    {% else %}
                    <tr><td colspan="7" class="empty">No bookings yet.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

BLOCKED_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Rayla Admin | Block Days</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #36454f; --accent: #f8e1e1; --bg: #f5f7f8; --danger: #e74c3c; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--primary); }
        .sidebar { position: fixed; top: 0; left: 0; width: 220px; height: 100vh; background: var(--primary); color: white; padding: 30px 20px; }
        .sidebar h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; margin-bottom: 30px; }
        .sidebar a { display: block; color: rgba(255,255,255,0.7); text-decoration: none; padding: 10px 12px; border-radius: 8px; margin-bottom: 5px; font-size: 0.9rem; transition: all 0.2s; }
        .sidebar a:hover, .sidebar a.active { background: rgba(255,255,255,0.15); color: white; }
        .main { margin-left: 220px; padding: 40px; }
        h1 { font-family: 'Playfair Display', serif; font-size: 2rem; margin-bottom: 30px; }
        .section { background: white; border-radius: 14px; box-shadow: 0 2px 15px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 30px; }
        .section-header { padding: 20px 24px; border-bottom: 1px solid #f0f0f0; font-weight: 600; }
        .block-form { padding: 24px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .block-form label { font-size: 0.9rem; color: #666; margin-right: 8px; }
        .block-form input[type=date] { padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 0.95rem; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-family: 'Inter', sans-serif; font-weight: 500; transition: opacity 0.2s; }
        .btn:hover { opacity: 0.85; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-danger { background: var(--danger); color: white; font-size: 0.8rem; padding: 6px 12px; border-radius: 6px; }
        .blocked-list { display: flex; flex-wrap: wrap; gap: 10px; padding: 24px; }
        .blocked-tag { background: #fde8e8; color: var(--danger); padding: 10px 16px; border-radius: 10px; display: flex; align-items: center; gap: 12px; font-size: 0.95rem; font-weight: 500; }
        .empty { padding: 30px 24px; color: #aaa; font-style: italic; }
        .note { padding: 16px 24px; background: #fffbeb; border-left: 4px solid #f59e0b; color: #92400e; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>Rayla Admin</h2>
        <a href="/admin">📋 Bookings</a>
        <a href="/admin/blocked" class="active">🚫 Block Days</a>
    </div>
    <div class="main">
        <h1>Manage Blocked Days</h1>

        <div class="section">
            <div class="section-header">Block a Full Day</div>
            <div class="note">When a day is blocked, no new client bookings can be made for that date.</div>
            <form class="block-form" action="/admin/block" method="POST">
                <label for="block-date">Select Date:</label>
                <input type="date" id="block-date" name="date" required>
                <button type="submit" class="btn btn-primary">Mark as Packed</button>
            </form>
        </div>

        <div class="section">
            <div class="section-header">Currently Blocked Days ({{ blocked_days|length }})</div>
            {% if blocked_days %}
            <div class="blocked-list">
                {% for d in blocked_days %}
                <div class="blocked-tag">
                    📅 {{ d }}
                    <form action="/admin/unblock" method="POST" style="display:inline;">
                        <input type="hidden" name="date" value="{{ d }}">
                        <button type="submit" class="btn btn-danger">Unblock</button>
                    </form>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty">No days currently blocked.</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/admin')
@requires_auth
def admin_dashboard():
    bookings = load_json(BOOKINGS_FILE)
    blockings = load_json(BLOCKED_DAYS_FILE)
    bookings_display = list(reversed(bookings))
    total = len(bookings)
    latest = bookings_display[0]['timestamp'] if total > 0 else "No bookings yet"
    return render_template_string(ADMIN_HTML, bookings=bookings_display, total=total,
                                  blocked_count=len(blockings), latest=latest)

@app.route('/admin/blocked')
@requires_auth
def admin_blocked():
    blocked_days = load_json(BLOCKED_DAYS_FILE)
    return render_template_string(BLOCKED_HTML, blocked_days=sorted(blocked_days))

@app.route('/admin/block', methods=['POST'])
@requires_auth
def block_day():
    date = request.form.get('date')
    if date:
        blocked = load_json(BLOCKED_DAYS_FILE)
        if date not in blocked:
            blocked.append(date)
            save_json(BLOCKED_DAYS_FILE, blocked)
    return redirect(url_for('admin_blocked'))

@app.route('/admin/unblock', methods=['POST'])
@requires_auth
def unblock_day():
    date = request.form.get('date')
    if date:
        blocked = load_json(BLOCKED_DAYS_FILE)
        blocked = [d for d in blocked if d != date]
        save_json(BLOCKED_DAYS_FILE, blocked)
    return redirect(url_for('admin_blocked'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
