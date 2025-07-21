import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re
print(re)

def is_valid_email(email):
    """Check if the email is valid."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Fetch all users
users = cursor.execute("SELECT id, password FROM users").fetchall()

for user in users:
    user_id = user[0]
    plain_text_password = user[1]

    # Check if password is already hashed (hashed passwords start with 'pbkdf2:sha256')
    if not plain_text_password.startswith("pbkdf2:sha256"):
        hashed_password = generate_password_hash(plain_text_password, method="pbkdf2:sha256", salt_length=16)

        cursor.execute("UPDATE users SET password=? WHERE id=?", (hashed_password, user_id))
        print(f"Updated password for user ID {user_id}")

conn.commit()
conn.close()

print("Passwords updated successfully!")
app = Flask(__name__)
db_path = os.getenv("DATABASE_PATH", "db/database.db")
app.secret_key = "your_secret_key"

# Database initialization
def init_db():
    conn = sqlite3.connect("db_path")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
        # Create exercise_stats table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exercise TEXT,
            reps INTEGER,
            sets INTEGER,
            weight REAL,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not is_valid_email(email):
            return "Invalid email format!"
        
        if password != confirm_password:
            return "Passwords do not match!"
        
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)", 
                           (first_name, last_name, email, hashed_password))
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Email already registered!"
        except Exception as e:
            return f"Registration failed due to an error: {e}"
        finally:
            conn.close()
    print(request.method)
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user[4], password):
            session["user_id"] = user[0]
            return redirect(url_for("dashboard"))
        return "Do you even lift, bro? Invalid credentials!"

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    from datetime import date
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get the selected date from the dropdown, defaulting to today's date
    selected_date = request.form.get("selected_date", date.today().strftime("%Y-%m-%d"))
    selected_exercise = request.form.get("selected_exercise", "")
    
    # Fetch user info
    user = cursor.execute("SELECT first_name, last_name FROM users WHERE id=?", (session["user_id"],)).fetchone()

    # Adjust query based on exercise selection
    if selected_exercise:
        stats = cursor.execute("SELECT exercise, reps, sets, weight, date FROM exercise_stats WHERE user_id=? AND date=? AND exercise=?", 
                               (session["user_id"], selected_date, selected_exercise)).fetchall()
    else:
        stats = cursor.execute("SELECT exercise, reps, sets, weight, date FROM exercise_stats WHERE user_id=? AND date=?", 
                               (session["user_id"], selected_date)).fetchall()

    exercises = cursor.execute("SELECT DISTINCT exercise FROM exercise_stats WHERE user_id=?", (session["user_id"],)).fetchall()


    conn.close()

    # Check if stats exist for the selected date
    has_data = bool(stats)

    return render_template("dashboard.html", first_name=user[0], last_name=user[1], stats=stats, has_data=has_data, selected_date=selected_date, selected_exercise=selected_exercise, exercises=exercises)

@app.route("/add_stats", methods=["POST"])
def add_stats():
    if "user_id" not in session:
        return redirect(url_for("login"))  # Ensure the user is logged in

    exercise = request.form["exercise"]
    reps = request.form["reps"]
    sets = request.form["sets"]
    weight = request.form["weight"]
    date = request.form["date"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO exercise_stats (user_id, exercise, reps, sets, weight, date) VALUES (?, ?, ?, ?, ?, ?)", 
                   (session["user_id"], exercise, reps, sets, weight, date))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))  # Redirect back to dashboard

print(app.url_map)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5500)