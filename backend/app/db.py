# Database connection management.
# Uses Flask's app-context (flask.g) to provide one connection per request
# and close it automatically on teardown.

import mysql.connector
from flask import g, current_app


def get_db():
    """Return the current request's DB connection, creating one if needed."""
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            database=current_app.config["DB_NAME"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
        )
    return g.db


def close_db(e=None):
    """Close the DB connection stored in flask.g (called on app context teardown)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Register the close_db teardown hook with the Flask app."""
    app.teardown_appcontext(close_db)
