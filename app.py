from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "change-this-secret-key-before-deployment"
)

DATABASE = "database.db"

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


STYLE = """
<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 25px;
    background: #f2f7f3;
    font-family: Arial, sans-serif;
    color: #17231f;
}

.container {
    max-width: 480px;
    margin: 50px auto;
    padding: 30px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 8px 30px #00000010;
}

h1, h2, h3 {
    color: #146b4d;
    text-align: center;
}

p {
    line-height: 1.7;
}

input, select {
    width: 100%;
    padding: 13px;
    margin: 10px 0 18px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 15px;
}

button {
    width: 100%;
    padding: 14px;
    background: #146b4d;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
}

button:hover {
    background: #0b4c37;
}

a {
    color: #146b4d;
    text-decoration: none;
}

.card {
    background: #f5faf6;
    padding: 18px;
    border-radius: 12px;
    margin: 15px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px 8px;
    border-bottom: 1px solid #ddd;
    text-align: left;
}

.message {
    padding: 12px;
    background: #e6f5e9;
    border-radius: 8px;
    margin-bottom: 15px;
}
</style>
"""


def page(title, content):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ha">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>{{ title }}</title>
        {{ style|safe }}
    </head>
    <body>
        <div class="container">
            {{ content|safe }}
        </div>
    </body>
    </html>
    """, title=title, content=content, style=STYLE)


@app.route("/")
def home():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    if session.get("username"):
        return redirect(url_for("rate_page"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 6:
            return page(
                "Register",
                "<h2>Yi Rajista</h2>"
                "<p>Username ya kasance aƙalla haruffa 3, "
                "password kuma haruffa 6.</p>"
                '<a href="/register">Sake gwadawa</a>'
            )

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) "
                    "VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return page(
                "Register",
                "<h2>Username ya riga ya kasance!</h2>"
                '<a href="/register">Sake gwadawa</a>'
            )

    content = """
    <h2>Yi Rajista</h2>
    <p>Ƙirƙiri account domin ka ba ni rating.</p>

    <form method="post">
        <label>Username</label>
        <input name="username" required minlength="3">

        <label>Password</label>
        <input name="password" type="password"
               required minlength="6">

        <button type="submit">Yi Rajista</button>
    </form>

    <p>Kana da account?
       <a href="/login">Shiga anan</a>
    </p>
    """

    return page("Register", content)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if user and check_password_hash(
            user["password_hash"], password
        ):
            session.clear()
            session["username"] = user["username"]
            return redirect(url_for("rate_page"))

        return page(
            "Login",
            "<h2>Shiga Account</h2>"
            "<p>Username ko password ba daidai ba ne.</p>"
            '<a href="/login">Sake gwadawa</a>'
        )

    content = """
    <h1>Pantami Junior</h1>
    <h2>Welcome Back!</h2>

    <p>Shiga account ɗinka domin ka ba ni rating.</p>

    <form method="post">
        <label>Username</label>
        <input name="username" required>

        <label>Password</label>
        <input name="password" type="password" required>

        <button type="submit">Shiga</button>
    </form>

    <p>Ba ka da account?
       <a href="/register">Yi rajista</a>
    </p>

    <hr>

    <p><a href="/admin/login">Admin Login</a></p>
    """

    return page("Pantami Junior Login", content)


@app.route("/rate", methods=["GET", "POST"])
@login_required
def rate_page():
    username = session["username"]

    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", ""))
        except ValueError:
            rating = 0

        if rating not in range(1, 6):
            return page(
                "Rating",
                "<h2>Rating ba daidai ba ne.</h2>"
                '<a href="/rate">Sake gwadawa</a>'
            )

        with get_db() as conn:
            conn.execute(
                "INSERT INTO ratings (username, rating) "
                "VALUES (?, ?)",
                (username, rating)
            )

        return page(
            "Thank You",
            f"<h2>Nagode ƙwarai, {username}!</h2>"
            f"<p>An karɓi rating ɗinka na taurari "
            f"{rating} ⭐.</p>"
            '<a href="/rate">Bada wani rating</a><br><br>'
            '<a href="/logout">Fita</a>'
        )

    content = f"""
    <h1>You're Welcome!</h1>
    <h2>Muhammad Abubakar Uba</h2>
    <h3>(Pantami Junior)</h3>

    <div class="card">
        <p>Barka da zuwa <b>{username}</b>!</p>
        <p>Don Allah ka ba ni rating.</p>
    </div>

    <form method="post">
        <label>Zaɓi Rating ɗinka</label>

        <select name="rating" required>
            <option value="5">⭐⭐⭐⭐⭐ 5 - Masha Allah</option>
            <option value="4">⭐⭐⭐⭐ 4 - Ya yi kyau</option>
            <option value="3">⭐⭐⭐ 3 - Matsakaici</option>
            <option value="2">⭐⭐ 2 - Yana buƙatar gyara</option>
            <option value="1">⭐ 1 - Bai gamsar ba</option>
        </select>

        <button type="submit">Aika Rating</button>
    </form>

    <p><a href="/logout">Fita (Logout)</a></p>
    """

    return page("Give a Rating", content)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        return page(
            "Admin Login",
            "<h2>Admin details ba daidai ba ne.</h2>"
            '<a href="/admin/login">Sake gwadawa</a>'
        )

    content = """
    <h2>Admin Login</h2>
    <p>Gidan sarrafa shafin Pantami Junior.</p>

    <form method="post">
        <label>Admin Username</label>
        <input name="username" required>

        <label>Admin Password</label>
        <input name="password" type="password" required>

        <button type="submit">Shiga Admin</button>
    </form>

    <p><a href="/login">Komawa Login</a></p>
    """

    return page("Admin Login", content)


@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db() as conn:
        ratings = conn.execute(
            "SELECT username, rating, created_at "
            "FROM ratings ORDER BY id DESC"
        ).fetchall()

        stats = conn.execute(
            "SELECT COUNT(*) AS total, AVG(rating) AS average "
            "FROM ratings"
        ).fetchone()

    total = stats["total"]
    average = round(stats["average"], 2) if total else 0

    rows = ""

    for item in ratings:
        rows += (
            "<tr>"
            f"<td>{item['username']}</td>"
            f"<td>{item['rating']} ⭐</td>"
            f"<td>{item['created_at']}</td>"
            "</tr>"
        )

    content = f"""
    <h2>Pantami Junior</h2>
    <h3>Admin Dashboard</h3>

    <div class="card">
        <p><b>Total Ratings:</b> {total}</p>
        <p><b>Average Rating:</b> {average} / 5 ⭐</p>
    </div>

    <h3>Rating Records</h3>

    <table>
        <tr>
            <th>Username</th>
            <th>Rating</th>
            <th>Date</th>
        </tr>
        {rows}
    </table>

    <br>
    <a href="/logout">Logout</a>
    """

    return page("Admin Dashboard", content)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=False)
