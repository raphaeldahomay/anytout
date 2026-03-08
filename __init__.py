from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash
import os

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "anytout.db"
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine) 

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

@app.route("/")
def home():

    db_session = SessionLocal()

    try:
        result = db_session.execute(
            text("""
                SELECT t.tout_id, c.username, t.thoughts, t.created_at, t.like_s
                FROM thoughts t
                JOIN credentials c
                ON t.user_id = c.user_id
                ORDER BY t.created_at DESC
            """)
        )

        thoughts = result.fetchall()

    finally:
        db_session.close()

    if not thoughts:
        thoughts = None

    return render_template("index.html", thoughts=thoughts)

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "POST":
        thought = request.form.get("thought", "").strip()
        user_id = session.get("user_id")

        if not thought:
            return render_template(
                "create_post.html",
                error="Thought cannot be empty."
            )

        db_session = SessionLocal()
        try:
            db_session.execute(
                text("INSERT INTO thoughts (user_id, thoughts) VALUES (:user_id, :thoughts)"),
                {
                    "user_id": user_id,
                    "thoughts": thought,
                },
            )
            db_session.commit()
        finally:
            db_session.close()

        return redirect(url_for("home"))

    return render_template("create_post.html")

@app.route("/like", methods=["POST"])
def like_thought():

    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    thought_id = request.form.get("thought_id")

    db_session = SessionLocal()

    try:
        result = db_session.execute(
            text("""
                SELECT 1
                FROM likes
                WHERE user_id = :uid AND tout_id = :tid
            """),
            {"uid": user_id, "tid": thought_id}
        )

        already_liked = result.fetchone()

        if not already_liked:
            db_session.execute(
                text("""
                    INSERT INTO likes (user_id, tout_id)
                    VALUES (:uid, :tid)
                """),
                {"uid": user_id, "tid": thought_id}
            )

            db_session.execute(
                text("""
                    UPDATE thoughts
                    SET like_s = like_s + 1
                    WHERE tout_id = :tid
                """),
                {"tid": thought_id}
            )

            db_session.commit()

    finally:
        db_session.close()

    return redirect(url_for("home"))