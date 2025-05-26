from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database initialization
def init_db():
    conn = sqlite3.connect("database.db")
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

        if password != confirm_password:
            return "Passwords do not match!"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)", 
                           (first_name, last_name, email, password))
            conn.commit()
            return redirect(url_for("login"))
        except:
            return "Email already registered!"
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
        user = cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect(url_for("dashboard"))
        return "Do you even lift, bro? Invalid credentials!"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    user = cursor.execute("SELECT first_name, last_name FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()

    return f"Welcome, {user[0]} {user[1]}! Here is your fitness dashboard."

print(app.url_map)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5500)