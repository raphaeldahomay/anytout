import os
from flask import Flask

from db import init_db
from routes import register_routes


def create_app():

    app = Flask(__name__)

    os.makedirs(app.instance_path, exist_ok=True)

    db_path = os.path.join(app.instance_path, "app.db")

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["DATABASE"] = db_path

    # create database if needed
    init_db(db_path)

    # register routes
    register_routes(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run()