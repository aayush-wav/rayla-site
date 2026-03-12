import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
FRONT_DIR   = os.path.join(BASE_DIR, '..')    
DATA_DIR    = os.path.join(BASE_DIR, 'data')  
os.makedirs(DATA_DIR, exist_ok=True)

BOOKINGS_FILE     = os.path.join(DATA_DIR, 'bookings.json')
BLOCKED_DAYS_FILE = os.path.join(DATA_DIR, 'blocked_days.json')
BLOCKED_SLOTS_FILE= os.path.join(DATA_DIR, 'blocked_slots.json')
SETTINGS_FILE     = os.path.join(DATA_DIR, 'settings.json')

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'rayla_admin_2026')

ALL_SLOTS = [
    "10:00","10:30","11:00","11:30",
    "12:00","12:30","13:00","13:30",
    "14:00","14:30","15:00","15:30",
    "16:00","16:30","17:00","17:30",
    "18:00","18:30"
]

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory(FRONT_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename in ['style.css', 'script.js', 'favicon.ico']:
        return send_from_directory(FRONT_DIR, filename)
    if filename.startswith('images/'):
        return send_from_directory(FRONT_DIR, filename)
    return ('Not found', 404)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return ('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Rayla Admin"'})
        return f(*args, **kwargs)
    return decorated

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def get_num_technicians():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                return json.load(f).get('num_technicians', 2)
            except:
                pass
    return 2

@app.route('/api/availability')
def get_availability():
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Date required"}), 400

    if date in load_json(BLOCKED_DAYS_FILE):
        return jsonify({"blocked": True, "available_slots": []})

    num_tech     = get_num_technicians()
    bookings     = load_json(BOOKINGS_FILE)
    blocked_slots= load_json(BLOCKED_SLOTS_FILE)

    slot_counts = {}
    for b in bookings:
        if b.get('date') == date:
            t = b.get('time')
            slot_counts[t] = slot_counts.get(t, 0) + 1

    manual_blocked = {e.split(' ')[1] for e in blocked_slots if e.startswith(date + ' ')}

    available = [
        s for s in ALL_SLOTS
        if s not in manual_blocked and slot_counts.get(s, 0) < num_tech
    ]
    return jsonify({"blocked": False, "available_slots": available})

@app.route('/api/booking', methods=['POST'])
def handle_booking():
    data = request.json or {}

    name    = data.get('name')
    phone   = data.get('phone')
    service = data.get('service')
    date    = data.get('date')
    time    = data.get('time')

    if not all([name, phone, service, date, time]):
        return jsonify({"error": "Missing required fields"}), 400

    if date in load_json(BLOCKED_DAYS_FILE):
        return jsonify({"error": "Sorry, this day is fully booked. Please choose another date."}), 409

    num_tech      = get_num_technicians()
    bookings      = load_json(BOOKINGS_FILE)
    blocked_slots = load_json(BLOCKED_SLOTS_FILE)

    if f"{date} {time}" in blocked_slots:
        return jsonify({"error": f"The {time} slot on {date} is unavailable. Please choose another time."}), 409

    existing = sum(1 for b in bookings if b.get('date') == date and b.get('time') == time)
    if existing >= num_tech:
        return jsonify({"error": f"The {time} slot on {date} is fully booked. Please choose another time."}), 409

    data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bookings.append(data)
    save_json(BOOKINGS_FILE, bookings)

    return jsonify({
        "status": "success",
        "message": f"Thank you, {name}! Your {service} appointment is confirmed for {date} at {time}."
    }), 200

SHARED_STYLES = """
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    :root{--primary:#36454f;--accent:#f8e1e1;--bg:#f5f7f8;--danger:#e74c3c;--success:#27ae60}
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--primary)}
    .sidebar{position:fixed;top:0;left:0;width:220px;height:100vh;background:var(--primary);color:#fff;padding:30px 20px}
    .sidebar h2{font-family:'Playfair Display',serif;font-size:1.4rem;margin-bottom:30px}
    .sidebar a{display:block;color:rgba(255,255,255,.7);text-decoration:none;padding:10px 12px;border-radius:8px;margin-bottom:5px;font-size:.9rem;transition:all .2s}
    .sidebar a:hover,.sidebar a.active{background:rgba(255,255,255,.15);color:#fff}
    .main{margin-left:220px;padding:40px;transition:margin-left .3s ease}
    h1{font-family:'Playfair Display',serif;font-size:2rem;margin-bottom:30px}
    .section{background:#fff;border-radius:14px;box-shadow:0 2px 15px rgba(0,0,0,.06);overflow:hidden;margin-bottom:30px}
    .section-content{overflow-x:auto}
    .section-header{padding:20px 24px;border-bottom:1px solid #f0f0f0;font-weight:600;font-size:1rem}
    .form-row{padding:24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
    .form-row label{font-size:.9rem;color:#666}
    .form-row input[type=date],.form-row select,.form-row input[type=number]{padding:10px 14px;border:1px solid #ddd;border-radius:8px;font-family:'Inter',sans-serif;font-size:.95rem}
    .btn{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-family:'Inter',sans-serif;font-weight:500;transition:opacity .2s;white-space:nowrap}
    .btn:hover{opacity:.85}
    .btn-primary{background:var(--primary);color:#fff}
    .btn-danger{background:var(--danger);color:#fff;font-size:.8rem;padding:6px 12px;border-radius:6px}
    .btn-success{background:var(--success);color:#fff;font-size:.8rem;padding:6px 14px;border-radius:8px;border:none;cursor:pointer;font-family:'Inter',sans-serif;font-weight:500;white-space:nowrap}
    .btn-success:hover{opacity:.85}
    .tag-list{display:flex;flex-wrap:wrap;gap:10px;padding:24px}
    .tag{padding:10px 16px;border-radius:10px;display:flex;align-items:center;gap:12px;font-size:.9rem;font-weight:500}
    .tag-day{background:#fde8e8;color:var(--danger)}
    .tag-slot{background:#fff3cd;color:#856404}
    .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:35px}
    .card{background:#fff;padding:24px;border-radius:14px;box-shadow:0 2px 15px rgba(0,0,0,.06)}
    .card h3{font-size:.8rem;text-transform:uppercase;color:#999;letter-spacing:1px;margin-bottom:10px}
    .card .value{font-size:2.2rem;font-weight:600}
    table{width:100%;border-collapse:collapse;min-width:600px}
    th{background:#fafafa;text-align:left;padding:12px 20px;font-size:.8rem;text-transform:uppercase;color:#999;letter-spacing:.5px}
    td{padding:14px 20px;border-bottom:1px solid #f5f5f5;font-size:.95rem}
    tr:last-child td{border-bottom:none}
    .badge{padding:4px 12px;border-radius:20px;font-size:.8rem;font-weight:500}
    .badge-service{background:var(--accent);color:var(--primary)}
    .time-badge{background:#e8f4fd;color:#2980b9;padding:3px 10px;border-radius:6px;font-size:.85rem;font-weight:500}
    .empty{padding:30px 24px;color:#aaa;font-style:italic}
    .note{padding:14px 24px;background:#fffbeb;border-left:4px solid #f59e0b;color:#92400e;font-size:.88rem}
    .page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;flex-wrap:wrap;gap:15px}
    @media (max-width:992px){
        .sidebar{width:60px;padding:30px 10px}
        .sidebar h2{display:none}
        .sidebar a{text-align:center;font-size:1.2rem;padding:15px 0}
        .main{margin-left:60px;padding:20px}
    }
    @media (max-width:768px){
        .stats{grid-template-columns:1fr}
        h1{font-size:1.5rem}
    }
</style>
"""

SIDEBAR_BOOKINGS = """
<div class="sidebar">
    <h2>Rayla Admin</h2>
    <a href="/admin" class="{a}">📋 Bookings</a>
    <a href="/admin/blocked" class="{b}">🚫 Availability</a>
</div>
"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Rayla Admin | Bookings</title>
""" + SHARED_STYLES + """
</head><body>
""" + SIDEBAR_BOOKINGS.format(a='active', b='') + """
<div class="main">
    <div class="page-header">
        <h1>Bookings</h1>
        <button class="btn btn-primary" onclick="location.reload()">↻ Refresh</button>
    </div>
    <div class="stats">
        <div class="card"><h3>Appointments</h3><div class="value">{{ total }}</div></div>
        <div class="card"><h3>Technicians</h3><div class="value">{{ num_tech }}</div></div>
        <div class="card"><h3>Availability</h3><div class="value" style="font-size:1.2rem;line-height:1.4">{{ blocked_days }} Days Blocked<br>{{ blocked_slots }} Slots Blocked</div></div>
    </div>
    <div class="section">
        <div class="section-header">All Appointments</div>
        <div class="section-content">
            <table>
                <thead><tr>
                    <th>Submitted</th><th>Client</th><th>Phone</th>
                    <th>Category</th><th>Treatment</th><th>Date</th><th>Time</th><th>Action</th>
                </tr></thead>
                <tbody>
                {% for b in bookings %}
                <tr>
                    <td style="color:#aaa;font-size:.85rem">{{ b.timestamp }}</td>
                    <td><strong>{{ b.name }}</strong></td>
                    <td>{{ b.phone if b.phone else b.email if b.email else '—' }}</td>
                    <td><span class="badge badge-service">{{ b.service }}</span></td>
                    <td style="color:#555;font-style:italic">{{ b.sub_service if b.sub_service else '—' }}</td>
                    <td>{{ b.date }}</td>
                    <td><span class="time-badge">{{ b.time if b.time else '—' }}</span></td>
                    <td>
                        <form action="/admin/complete" method="POST"
                              onsubmit="return confirm('Mark appointment as complete and remove it?')">
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
</div></body></html>
"""

BLOCKED_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Rayla Admin | Availability</title>
""" + SHARED_STYLES + """
</head><body>
""" + SIDEBAR_BOOKINGS.format(a='', b='active') + """
<div class="main">
    <h1>Manage Availability</h1>

    <div class="section">
        <div class="section-header">👥 Technicians on Duty</div>
        <div class="note">Each time slot accepts this many simultaneous bookings.</div>
        <form class="form-row" action="/admin/settings" method="POST">
            <label>Active Technicians:</label>
            <input type="number" name="num_technicians" value="{{ num_tech }}" min="1" max="10" style="width:80px">
            <button type="submit" class="btn btn-primary">Save</button>
        </form>
    </div>

    <div class="section">
        <div class="section-header">📅 Block a Full Day</div>
        <div class="note">Clients cannot book any slot on this day.</div>
        <form class="form-row" action="/admin/block" method="POST">
            <label>Date:</label>
            <input type="date" name="date" required>
            <button type="submit" class="btn btn-primary">Mark Day as Packed</button>
        </form>
    </div>

    <div class="section">
        <div class="section-header">🕐 Block a Specific Time Slot</div>
        <div class="note">Use when all technicians are busy for one particular slot.</div>
        <form class="form-row" action="/admin/block-slot" method="POST">
            <label>Date:</label>
            <input type="date" name="date" required>
            <label>Time:</label>
            <select name="time" required>
                {% for slot in all_slots %}<option value="{{ slot }}">{{ slot }}</option>{% endfor %}
            </select>
            <button type="submit" class="btn btn-primary">Block Slot</button>
        </form>
    </div>

    <div class="section">
        <div class="section-header">Blocked Full Days ({{ blocked_days|length }})</div>
        {% if blocked_days %}
        <div class="tag-list">
            {% for d in blocked_days %}
            <div class="tag tag-day">📅 {{ d }}
                <form action="/admin/unblock" method="POST" style="display:inline">
                    <input type="hidden" name="date" value="{{ d }}">
                    <button type="submit" class="btn btn-danger">Unblock</button>
                </form>
            </div>{% endfor %}
        </div>
        {% else %}<div class="empty">No full days blocked.</div>{% endif %}
    </div>

    <div class="section">
        <div class="section-header">Blocked Time Slots ({{ blocked_slots|length }})</div>
        {% if blocked_slots %}
        <div class="tag-list">
            {% for s in blocked_slots %}
            <div class="tag tag-slot">🕐 {{ s }}
                <form action="/admin/unblock-slot" method="POST" style="display:inline">
                    <input type="hidden" name="slot" value="{{ s }}">
                    <button type="submit" class="btn btn-danger">Unblock</button>
                </form>
            </div>{% endfor %}
        </div>
        {% else %}<div class="empty">No individual slots blocked.</div>{% endif %}
    </div>
</div></body></html>
"""

@app.route('/admin')
@requires_auth
def admin_dashboard():
    bookings = load_json(BOOKINGS_FILE)
    blocked_days = load_json(BLOCKED_DAYS_FILE)
    blocked_slots = load_json(BLOCKED_SLOTS_FILE)
    display  = list(reversed(bookings))
    total    = len(bookings)
    num_tech = get_num_technicians()
    
    return render_template_string(ADMIN_HTML, 
                                  bookings=display, 
                                  total=total,
                                  num_tech=num_tech,
                                  blocked_days=len(blocked_days),
                                  blocked_slots=len(blocked_slots))

@app.route('/admin/complete', methods=['POST'])
@requires_auth
def complete_booking():
    ts = request.form.get('timestamp')
    if ts:
        bookings = [b for b in load_json(BOOKINGS_FILE) if b.get('timestamp') != ts]
        save_json(BOOKINGS_FILE, bookings)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/blocked')
@requires_auth
def admin_blocked():
    return render_template_string(BLOCKED_HTML,
        blocked_days=sorted(load_json(BLOCKED_DAYS_FILE)),
        blocked_slots=sorted(load_json(BLOCKED_SLOTS_FILE)),
        num_tech=get_num_technicians(),
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
        save_json(BLOCKED_DAYS_FILE, [d for d in load_json(BLOCKED_DAYS_FILE) if d != date])
    return redirect(url_for('admin_blocked'))

@app.route('/admin/block-slot', methods=['POST'])
@requires_auth
def block_slot():
    date = request.form.get('date')
    time = request.form.get('time')
    if date and time:
        key     = f"{date} {time}"
        blocked = load_json(BLOCKED_SLOTS_FILE)
        if key not in blocked:
            blocked.append(key)
            save_json(BLOCKED_SLOTS_FILE, blocked)
    return redirect(url_for('admin_blocked'))

@app.route('/admin/unblock-slot', methods=['POST'])
@requires_auth
def unblock_slot():
    slot = request.form.get('slot')
    if slot:
        save_json(BLOCKED_SLOTS_FILE, [s for s in load_json(BLOCKED_SLOTS_FILE) if s != slot])
    return redirect(url_for('admin_blocked'))

@app.route('/admin/settings', methods=['POST'])
@requires_auth
def save_settings():
    n = request.form.get('num_technicians', '')
    if n.isdigit():
        save_json(SETTINGS_FILE, {'num_technicians': int(n)})
    return redirect(url_for('admin_blocked'))

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port  = int(os.environ.get('PORT', 5000))

    if debug:
        app.run(debug=True, port=port)
    else:
        try:
            from waitress import serve
            print(f"Starting production server on http://0.0.0.0:{port}")
            serve(app, host='0.0.0.0', port=port)
        except ImportError:
            print("waitress not installed, falling back to Flask dev server.")
            app.run(host='0.0.0.0', port=port)
