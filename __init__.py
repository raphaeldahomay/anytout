from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "anytout.db"
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine) 

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db_session = SessionLocal()
        try:
            db_session.execute(
                text("INSERT INTO credentials (username, pwd_hash) VALUES (:username, :pwd_hash)"),
                {
                    "username": username,
                    "pwd_hash": generate_password_hash(password),
                },
            )
            db_session.commit()
        finally:
            db_session.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        db_session = SessionLocal()
        try:
            user = db_session.execute(
                text("SELECT user_id, username, pwd_hash FROM credentials WHERE username = :username"),
                {"username": username},
            ).mappings().fetchone()
        finally:
            db_session.close()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["pwd_hash"], password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user["user_id"]
            return redirect(url_for("home"))

        flash(error)

    return render_template("login.html")