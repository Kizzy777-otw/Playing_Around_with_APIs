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
    total_litres = sum([r["litres"] for r in user["milk_records"]])
    gross = total_litres * 600

    fee = 2400 if user["plan"] == "weekly" else 2000
    return gross - fee

def next_payment_date(user):
    if not user["milk_records"]:
        return None

    last_date = datetime.strptime(user["milk_records"][-1]["date"], "%Y-%m-%d")

    if user["plan"] == "weekly":
        return last_date + timedelta(days=7)
    else:
        return last_date + timedelta(days=14)

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
            "milk_records": []
        }

        data["users"].append(new_user)
        save_data(data)

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = find_user(username)

        if user and user["password"] == password:
            session["user"] = username
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

    user = find_user(session["user"])

    total_litres = sum([r["litres"] for r in user["milk_records"]])
    earnings = calculate_earnings(user)

    next_pay = next_payment_date(user)

    days_remaining = None
    if next_pay:
        days_remaining = (next_pay - datetime.now()).days

    return render_template(
        "dashboard.html",
        user=user,
        total_litres=total_litres,
        earnings=earnings,
        days_remaining=days_remaining
    )

# ----------------------
# ADD MILK RECORD
# ----------------------

@app.route("/add", methods=["POST"])
def add_record():
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    username = session["user"]

    litres = float(request.form["litres"])
    date = request.form["date"]

    for user in data["users"]:
        if user["username"] == username:
            user["milk_records"].append({
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
    app.run(debug=True)
