# agritrak Flask app that handles user authentication,dashboard and milk recording management

from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
from datetime import datetime, timedelta
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATA_FILE = "data/users.json"


# for saving data, loading and calculations

def load_data():
    # Loading user's data from json
    if not os.path.exists(DATA_FILE):
        return {"users": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    # saving user's data to json file
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def find_user(username):
    # finding user using usrname
    data = load_data()
    for user in data["users"]:
        if user["username"] == username:
            return user
    return None

def calculate_earnings(user):
    # calculating the user's earnings
    total_litres = sum([r["litres"] for r in user.get("milk_records", [])])
    gross = total_litres * 600
    fee = 2400 if user.get("plan") == "weekly" else 2000
    return gross - fee

def next_payment_date(user):
    # calculating the user's next payment date
    if not user.get("milk_records"):
        return None
    last_date = datetime.strptime(user["milk_records"][-1]["date"], "%Y-%m-%d")
    if user.get("plan") == "weekly":
        return last_date + timedelta(days=7)
    else:
        return last_date + timedelta(days=14)

def payment_status_for_record(record):
    # etermine payment status for a milk record
    try:
        record_date = datetime.strptime(record.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        return "unknown"
    today = datetime.now().date()
    if record_date <= today:
        return "received"
    return "pending"

def ensure_manager_exists():
    #ensure Manager exists
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
    # get username for user
    data = load_data()
    return next((u for u in data["users"] if u.get("username") == username), None)

# flask endpoints

@app.route("/")
def home():
    # user redirect to login or dashboard
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

#authorization and authentication 

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

        #fixed credentials for manager
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

#the dashboard

@app.route("/dashboard")
@app.route("/dashboard/<username>")
def dashboard(username=None):
    if "user" not in session:
        return redirect("/login")

    role = session.get("role", "farmer")

    if username and role != "manager":
        return "Access denied", 403

    target_user = None
    if username:
        target_user = find_user(username)
        if not target_user:
            return "User not found", 404
    else:
        target_user = find_user(session["user"])
        if not target_user:
            return redirect("/logout")

    import socket
    server_id = socket.gethostname()

    if role == "manager" and not username:
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

        return render_template("dashboard.html", manager=True, users=users, next_due_user=next_due_user, server_id=server_id)

    # view of farmer, or even manager viewing farmer
    total_litres = sum([r["litres"] for r in target_user.get("milk_records", [])])
    earnings = calculate_earnings(target_user)
    next_pay = next_payment_date(target_user)
    next_payment_date_str = next_pay.strftime("%Y-%m-%d") if next_pay else None

    days_remaining = None
    if next_pay:
        days_remaining = (next_pay - datetime.now()).days

    for r in target_user.get("milk_records", []):
        r["status"] = payment_status_for_record(r)

    return render_template(
        "dashboard.html",
        manager=False,
        user=target_user,
        total_litres=total_litres,
        earnings=earnings,
        days_remaining=days_remaining,
        next_payment_date=next_payment_date_str,
        server_id=server_id
    )

#record of adding milk

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

#detail of records

@app.route("/record/<int:record_index>")
@app.route("/record/<username>/<int:record_index>")
def view_record(record_index, username=None):
    if "user" not in session:
        return redirect("/login")

    role = session.get("role", "farmer")
    current_user = session["user"]
    
    # must only be manager for viewing someone else's record
    if username and username != current_user and role != "manager":
        return "Access denied", 403

    # Determine which user's records to view
    if username:
        user = find_user(username)
        if not user:
            return "User not found", 404
    else:
        user = find_user(current_user)
        if not user:
            return redirect("/logout")

    milk_records = user.get("milk_records", [])
    if record_index < 0 or record_index >= len(milk_records):
        return "Record not found", 404

    record = milk_records[record_index]
    record["status"] = payment_status_for_record(record)

    earnings_for_record = record["litres"] * 600

    next_pay = next_payment_date(user)
    next_payment_date_str = next_pay.strftime("%Y-%m-%d") if next_pay else None
    days_remaining = None
    if next_pay:
        days_remaining = (next_pay - datetime.now()).days

    return render_template(
        "record_detail.html",
        record=record,
        user=user,
        earnings_for_record=earnings_for_record,
        next_payment_date=next_payment_date_str,
        days_remaining=days_remaining
    )


# the API currency conversion part


@app.route("/convert")
def convert():
    # endpoint for currency conversion RWF to USD
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
    except Exception as e:
        # handling error in case of API failure
        return jsonify({"error": "API unavailable", "details": str(e)})



if __name__ == "__main__":
    # running the flask app in debug mode 
    app.run(host="0.0.0.0", port=5000, debug=True)
