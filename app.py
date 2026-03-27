from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
from datetime import datetime, timedelta
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATA_FILE = "data/users.json"

# ----------------------
# Helpers
# ----------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def find_user(username):
    data = load_data()
    for user in data["users"]:
        if user["username"] == username:
            return user
    return None

def calculate_earnings(user):
    total_litres = sum([r["litres"] for r in user.get("milk_records", [])])
    gross = total_litres * 600

    fee = 2400 if user.get("plan") == "weekly" else 2000
    return gross - fee

def next_payment_date(user):
    if not user.get("milk_records"):
        return None

    last_date = datetime.strptime(user["milk_records"][-1]["date"], "%Y-%m-%d")

    if user.get("plan") == "weekly":
        return last_date + timedelta(days=7)
    else:
        return last_date + timedelta(days=14)


def payment_status_for_record(record):
    try:
        record_date = datetime.strptime(record.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        return "unknown"

    today = datetime.now().date()
    if record_date <= today:
        return "received"
    return "pending"


def ensure_manager_exists():
    data = load_data()
    manager = next((u for u in data["users"] if u.get("role") == "manager"), None)
    if not manager:
        data["users"].append({
            "username": "Manager",
            "password": "12345",
            "plan": "weekly",
            "role": "manager",
            "milk_records": []
        })
        save_data(data)


def get_user_by_username(username):
    data = load_data()
    return next((u for u in data["users"] if u.get("username") == username), None)

# ----------------------
# Routes
# ----------------------

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

# ----------------------
# AUTH
# ----------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = load_data()

        username = request.form["username"]
        password = request.form["password"]
        plan = request.form["plan"]

        if find_user(username):
            return "User already exists"

        new_user = {
            "username": username,
            "password": password,
            "plan": plan,
            "role": "farmer",
            "milk_records": []
        }

        data["users"].append(new_user)
        save_data(data)

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    ensure_manager_exists()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Manager fixed credentials
        if username == "Manager" and password == "12345":
            session["user"] = "Manager"
            session["role"] = "manager"
            return redirect("/dashboard")

        user = find_user(username)

        if user and user["password"] == password:
            session["user"] = username
            session["role"] = user.get("role", "farmer")
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ----------------------
# DASHBOARD
# ----------------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    role = session.get("role", "farmer")

    if role == "manager":
        users = load_data()["users"]
        for u in users:
            u["total_litres"] = sum([r["litres"] for r in u.get("milk_records", [])])
            u["earnings"] = calculate_earnings(u)
            next_pay = next_payment_date(u)
            u["next_payment_date"] = next_pay.strftime("%Y-%m-%d") if next_pay else None
            u["days_remaining"] = (next_pay - datetime.now()).days if next_pay else None
            for r in u.get("milk_records", []):
                r["status"] = payment_status_for_record(r)

        due_users = [u for u in users if u["days_remaining"] is not None]
        next_due_user = min(due_users, key=lambda u: u["days_remaining"]) if due_users else None

        return render_template("dashboard.html", manager=True, users=users, next_due_user=next_due_user)

    user = find_user(session["user"])
    if not user:
        return redirect("/logout")

    total_litres = sum([r["litres"] for r in user.get("milk_records", [])])
    earnings = calculate_earnings(user)

    next_pay = next_payment_date(user)
    next_payment_date_str = next_pay.strftime("%Y-%m-%d") if next_pay else None

    days_remaining = None
    if next_pay:
        days_remaining = (next_pay - datetime.now()).days

    for r in user.get("milk_records", []):
        r["status"] = payment_status_for_record(r)

    return render_template(
        "dashboard.html",
        manager=False,
        user=user,
        total_litres=total_litres,
        earnings=earnings,
        days_remaining=days_remaining,
        next_payment_date=next_payment_date_str
    )

# ----------------------
# ADD MILK RECORD
# ----------------------

@app.route("/add", methods=["POST"])
def add_record():
    if "user" not in session:
        return redirect("/login")

    if session.get("role") == "manager":
        return "Manager cannot add milk records via this endpoint", 403

    data = load_data()
    username = session["user"]

    litres = float(request.form["litres"])
    date = request.form["date"]

    for user in data["users"]:
        if user["username"] == username:
            user.setdefault("milk_records", []).append({
                "litres": litres,
                "date": date
            })

    save_data(data)
    return redirect("/dashboard")

# ----------------------
# API: Currency Conversion
# ----------------------

@app.route("/convert")
def convert():
    try:
        url = "https://open.er-api.com/v6/latest/RWF"
        response = requests.get(url).json()

        usd_rate = response["rates"]["USD"]

        user = find_user(session["user"])
        earnings = calculate_earnings(user)

        usd_value = earnings * usd_rate

        return jsonify({
            "rwf": earnings,
            "usd": round(usd_value, 2)
        })
    except:
        return jsonify({"error": "API unavailable"})

# ----------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
