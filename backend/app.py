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
BLOCKED_SLOTS_FILE = 'blocked_slots.json'  # list of "YYYY-MM-DD HH:MM" strings
SETTINGS_FILE = 'settings.json'
ADMIN_PASSWORD = 'rayla_admin_2026'

def get_num_technicians():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                return json.load(f).get('num_technicians', 2)
            except:
                pass
    return 2

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

    num_tech = get_num_technicians()
    bookings = load_json(BOOKINGS_FILE)
    blocked_slots = load_json(BLOCKED_SLOTS_FILE)

    # Count bookings per slot for this date
    slot_counts = {}
    for b in bookings:
        if b.get('date') == date:
            t = b.get('time')
            slot_counts[t] = slot_counts.get(t, 0) + 1

    # Build manually blocked set for this date ("YYYY-MM-DD HH:MM")
    manual_blocked = {entry.split(' ')[1] for entry in blocked_slots if entry.startswith(date + ' ')}

    available = []
    for s in ALL_SLOTS:
        bookings_for_slot = slot_counts.get(s, 0)
        if s not in manual_blocked and bookings_for_slot < num_tech:
            available.append(s)

    return jsonify({"blocked": False, "available_slots": available})

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

    num_tech = get_num_technicians()
    bookings = load_json(BOOKINGS_FILE)
    blocked_slots = load_json(BLOCKED_SLOTS_FILE)

    # Check manual slot block
    slot_key = f"{date} {time}"
    if slot_key in blocked_slots:
        return jsonify({"error": f"The {time} slot on {date} is unavailable. Please choose a different time."}), 409

    # Check capacity: count existing bookings for this date+time
    existing = sum(1 for b in bookings if b.get('date') == date and b.get('time') == time)
    if existing >= num_tech:
        return jsonify({"error": f"The {time} slot on {date} is fully booked. Please choose a different time."}), 409

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
        .btn-success { background: var(--success); color: white; font-size: 0.8rem; padding: 6px 14px; border-radius: 8px; border: none; cursor: pointer; font-family: 'Inter', sans-serif; font-weight: 500; }
        .btn-success:hover { opacity: 0.85; }
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
                        <th>Date Submitted</th>
                        <th>Client</th>
                        <th>Phone</th>
                        <th>Category</th>
                        <th>Treatment</th>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Action</th>
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
                        <td>
                            <form action="/admin/complete" method="POST" onsubmit="return confirm('Mark this appointment as complete and remove it?')">
                                <input type="hidden" name="timestamp" value="{{ b.timestamp }}">
                                <button type="submit" class="btn-success">✓ Done</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="8" class="empty">No bookings yet.</td></tr>
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
    <title>Rayla Admin | Availability</title>
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
        h1 { font-family: 'Playfair Display', serif; font-size: 2rem; margin-bottom: 30px; }
        .section { background: white; border-radius: 14px; box-shadow: 0 2px 15px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 30px; }
        .section-header { padding: 20px 24px; border-bottom: 1px solid #f0f0f0; font-weight: 600; font-size: 1rem; }
        .form-row { padding: 24px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .form-row label { font-size: 0.9rem; color: #666; }
        .form-row input[type=date], .form-row select, .form-row input[type=number] { padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 0.95rem; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-family: 'Inter', sans-serif; font-weight: 500; transition: opacity 0.2s; }
        .btn:hover { opacity: 0.85; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-danger { background: var(--danger); color: white; font-size: 0.8rem; padding: 6px 12px; border-radius: 6px; }
        .tag-list { display: flex; flex-wrap: wrap; gap: 10px; padding: 24px; }
        .tag { padding: 10px 16px; border-radius: 10px; display: flex; align-items: center; gap: 12px; font-size: 0.9rem; font-weight: 500; }
        .tag-day { background: #fde8e8; color: var(--danger); }
        .tag-slot { background: #fff3cd; color: #856404; }
        .empty { padding: 30px 24px; color: #aaa; font-style: italic; }
        .note { padding: 14px 24px; background: #fffbeb; border-left: 4px solid #f59e0b; color: #92400e; font-size: 0.88rem; }
        .settings-row { padding: 24px; display: flex; gap: 16px; align-items: center; }
        .technician-count { font-size: 2rem; font-weight: 700; color: var(--primary); padding: 0 10px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>Rayla Admin</h2>
        <a href="/admin">📋 Bookings</a>
        <a href="/admin/blocked" class="active">🚫 Availability</a>
    </div>
    <div class="main">
        <h1>Manage Availability</h1>

        <!-- Technician Count -->
        <div class="section">
            <div class="section-header">👥 Number of Technicians on Duty</div>
            <div class="note">Each time slot can hold this many simultaneous bookings. Adjust when staff is reduced.</div>
            <form class="settings-row" action="/admin/settings" method="POST">
                <label>Active Technicians:</label>
                <input type="number" name="num_technicians" value="{{ num_tech }}" min="1" max="10" style="width:80px;">
                <button type="submit" class="btn btn-primary">Save</button>
            </form>
        </div>

        <!-- Block Full Day -->
        <div class="section">
            <div class="section-header">📅 Block a Full Day</div>
            <div class="note">Clients won't be able to book any slot on this day.</div>
            <form class="form-row" action="/admin/block" method="POST">
                <label>Date:</label>
                <input type="date" name="date" required>
                <button type="submit" class="btn btn-primary">Mark Day as Packed</button>
            </form>
        </div>

        <!-- Block a Specific Slot -->
        <div class="section">
            <div class="section-header">🕐 Block a Specific Time Slot</div>
            <div class="note">Use this when all technicians are busy for just one particular slot on a day.</div>
            <form class="form-row" action="/admin/block-slot" method="POST">
                <label>Date:</label>
                <input type="date" name="date" required>
                <label>Time:</label>
                <select name="time" required>
                    {% for slot in all_slots %}
                    <option value="{{ slot }}">{{ slot }}</option>
                    {% endfor %}
                </select>
                <button type="submit" class="btn btn-primary">Block Slot</button>
            </form>
        </div>

        <!-- Blocked Days List -->
        <div class="section">
            <div class="section-header">Blocked Full Days ({{ blocked_days|length }})</div>
            {% if blocked_days %}
            <div class="tag-list">
                {% for d in blocked_days %}
                <div class="tag tag-day">
                    📅 {{ d }}
                    <form action="/admin/unblock" method="POST" style="display:inline;">
                        <input type="hidden" name="date" value="{{ d }}">
                        <button type="submit" class="btn btn-danger">Unblock</button>
                    </form>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty">No full days blocked.</div>
            {% endif %}
        </div>

        <!-- Blocked Slots List -->
        <div class="section">
            <div class="section-header">Blocked Time Slots ({{ blocked_slots|length }})</div>
            {% if blocked_slots %}
            <div class="tag-list">
                {% for s in blocked_slots %}
                <div class="tag tag-slot">
                    🕐 {{ s }}
                    <form action="/admin/unblock-slot" method="POST" style="display:inline;">
                        <input type="hidden" name="slot" value="{{ s }}">
                        <button type="submit" class="btn btn-danger">Unblock</button>
                    </form>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty">No individual slots blocked.</div>
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

@app.route('/admin/complete', methods=['POST'])
@requires_auth
def complete_booking():
    timestamp = request.form.get('timestamp')
    if timestamp:
        bookings = load_json(BOOKINGS_FILE)
        bookings = [b for b in bookings if b.get('timestamp') != timestamp]
        save_json(BOOKINGS_FILE, bookings)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/blocked')
@requires_auth
def admin_blocked():
    blocked_days = load_json(BLOCKED_DAYS_FILE)
    blocked_slots = load_json(BLOCKED_SLOTS_FILE)
    num_tech = get_num_technicians()
    return render_template_string(BLOCKED_HTML,
        blocked_days=sorted(blocked_days),
        blocked_slots=sorted(blocked_slots),
        num_tech=num_tech,
        all_slots=ALL_SLOTS)

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

@app.route('/admin/block-slot', methods=['POST'])
@requires_auth
def block_slot():
    date = request.form.get('date')
    time = request.form.get('time')
    if date and time:
        slot_key = f"{date} {time}"
        blocked = load_json(BLOCKED_SLOTS_FILE)
        if slot_key not in blocked:
            blocked.append(slot_key)
            save_json(BLOCKED_SLOTS_FILE, blocked)
    return redirect(url_for('admin_blocked'))

@app.route('/admin/unblock-slot', methods=['POST'])
@requires_auth
def unblock_slot():
    slot = request.form.get('slot')
    if slot:
        blocked = load_json(BLOCKED_SLOTS_FILE)
        blocked = [s for s in blocked if s != slot]
        save_json(BLOCKED_SLOTS_FILE, blocked)
    return redirect(url_for('admin_blocked'))

@app.route('/admin/settings', methods=['POST'])
@requires_auth
def save_settings():
    num_tech = request.form.get('num_technicians')
    if num_tech and num_tech.isdigit():
        save_json(SETTINGS_FILE, {'num_technicians': int(num_tech)})
    return redirect(url_for('admin_blocked'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
