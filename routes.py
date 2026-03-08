from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db_connection


def register_routes(app):

    @app.route("/")
    def home():
        conn = get_db_connection()

        try:
            cursor = conn.execute("""
                SELECT t.tout_id, c.username, t.thoughts, t.created_at, t.like_s
                FROM thoughts t
                JOIN credentials c
                ON t.user_id = c.user_id
                ORDER BY t.created_at DESC
            """)
            thoughts = cursor.fetchall()

        finally:
            conn.close()

        if not thoughts:
            thoughts = None

        return render_template("index.html", thoughts=thoughts)

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            conn = get_db_connection()

            try:
                conn.execute(
                    """
                    INSERT INTO credentials (username, pwd_hash)
                    VALUES (?, ?)
                    """,
                    (username, generate_password_hash(password)),
                )
                conn.commit()

            except Exception:
                conn.rollback()
                flash("Username already exists.")
                return render_template("signup.html")

            finally:
                conn.close()

            return redirect(url_for("login"))

        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            error = None

            conn = get_db_connection()

            try:
                cursor = conn.execute(
                    """
                    SELECT user_id, username, pwd_hash
                    FROM credentials
                    WHERE username = ?
                    """,
                    (username,),
                )
                user = cursor.fetchone()

            finally:
                conn.close()

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

            conn = get_db_connection()

            try:
                conn.execute(
                    """
                    INSERT INTO thoughts (user_id, thoughts)
                    VALUES (?, ?)
                    """,
                    (user_id, thought),
                )
                conn.commit()

            finally:
                conn.close()

            return redirect(url_for("home"))

        return render_template("create_post.html")

    @app.route("/like", methods=["POST"])
    def like_thought():
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login"))

        thought_id = request.form.get("thought_id")

        conn = get_db_connection()

        try:
            cursor = conn.execute(
                """
                SELECT 1
                FROM likes
                WHERE user_id = ? AND tout_id = ?
                """,
                (user_id, thought_id),
            )
            already_liked = cursor.fetchone()

            if not already_liked:
                conn.execute(
                    """
                    INSERT INTO likes (user_id, tout_id)
                    VALUES (?, ?)
                    """,
                    (user_id, thought_id),
                )

                conn.execute(
                    """
                    UPDATE thoughts
                    SET like_s = like_s + 1
                    WHERE tout_id = ?
                    """,
                    (thought_id,),
                )

                conn.commit()

        finally:
            conn.close()

        return redirect(url_for("home"))