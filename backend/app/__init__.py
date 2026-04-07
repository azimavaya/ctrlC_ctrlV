"""
__init__.py — Application factory for Panther Cloud Air (PCA).

Creates and configures the Flask app, registers all blueprints,
and seeds the admin user and flight schedule on first startup.
"""
import datetime
import decimal
import time
import logging
from flask import Flask
from flask_cors import CORS
from flask.json.provider import DefaultJSONProvider
from .config import Config
from .db import init_db

log = logging.getLogger(__name__)


# ── Custom JSON serializer ──────────────────────────────────────────────────

class PCAJSONProvider(DefaultJSONProvider):
    """Handle MariaDB types that the default Flask serializer cannot encode."""
    def default(self, obj):
        if isinstance(obj, datetime.timedelta):
            total = int(obj.total_seconds())
            h, m = divmod(total, 3600)
            m, s = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def _seed_admin(app):
    """
    Create the admin user on first startup if they don't exist yet.
    Retries until the DB is ready (handles Docker startup race).
    """
    import os
    import mysql.connector

    # Only run in the main process — the reloader child should skip
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return

    from .services.auth_service import hash_password

    for attempt in range(10):
        try:
            conn = mysql.connector.connect(
                host=app.config["DB_HOST"],
                port=app.config["DB_PORT"],
                database=app.config["DB_NAME"],
                user=app.config["DB_USER"],
                password=app.config["DB_PASSWORD"],
            )
            cursor = conn.cursor(dictionary=True)

            # Get admin role_id
            cursor.execute("SELECT role_id FROM roles WHERE role_name = 'admin'")
            role = cursor.fetchone()
            if not role:
                cursor.close()
                conn.close()
                time.sleep(2)
                continue

            # Insert admin if not exists (IGNORE handles race conditions)
            cursor.execute(
                "INSERT IGNORE INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
                ("admin", hash_password(app.config["ADMIN_PASSWORD"]), role["role_id"])
            )
            conn.commit()
            if cursor.rowcount > 0:
                log.info("Admin user created successfully.")
            else:
                log.info("Admin user already exists.")

            cursor.close()
            conn.close()
            return

        except mysql.connector.Error as e:
            log.warning(f"DB not ready (attempt {attempt + 1}/10): {e}")
            time.sleep(3)

    log.error("Could not seed admin user — DB never became ready.")


# ── Application factory ─────────────────────────────────────────────────────

def create_app():
    """Build and return a fully configured Flask application instance."""
    app = Flask(__name__)
    app.json_provider_class = PCAJSONProvider
    app.json = PCAJSONProvider(app)
    app.config.from_object(Config)
    CORS(app, resources={
        r"/api/*": {"origins": app.config["CORS_ORIGINS"]},
    })

    # Register the DB connection teardown hook
    init_db(app)

    # ── Blueprint registration ──────────────────────────────────────────
    from .routes.airports   import airports_bp
    from .routes.aircraft   import aircraft_bp
    from .routes.flights    import flights_bp
    from .routes.passengers import passengers_bp
    from .routes.simulation import simulation_bp
    from .routes.auth       import auth_bp
    from .routes.admin      import admin_bp
    from .routes.bookings   import bookings_bp

    app.register_blueprint(airports_bp,   url_prefix="/api/airports")
    app.register_blueprint(aircraft_bp,   url_prefix="/api/aircraft")
    app.register_blueprint(flights_bp,    url_prefix="/api/flights")
    app.register_blueprint(passengers_bp, url_prefix="/api/passengers")
    app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
    app.register_blueprint(auth_bp,       url_prefix="/api/auth")
    app.register_blueprint(admin_bp,      url_prefix="/api/admin")
    app.register_blueprint(bookings_bp,   url_prefix="/api/bookings")

    @app.route("/api/health")
    def health():
        return {"status": "ok", "message": "Panther Cloud Air API running"}

    # ── Startup tasks ────────────────────────────────────────────────────
    # Seed admin synchronously so login works as soon as the app is up.
    # Schedule generation runs in a background thread (takes ~15 s).
    _seed_admin(app)
    import threading
    threading.Thread(target=_seed_schedule, args=(app,), daemon=True).start()

    return app


def _seed_schedule(app):
    """Generate the timetable if no flights exist yet.
    Uses GET_LOCK to prevent the Flask reloader from running this twice."""
    import mysql.connector
    import os

    # Skip in the reloader child process — only the main process should seed
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return

    # Wait for admin seed to finish and DB to be ready
    time.sleep(15)
    for attempt in range(10):
        try:
            conn = mysql.connector.connect(
                host=app.config["DB_HOST"],
                port=app.config["DB_PORT"],
                database=app.config["DB_NAME"],
                user=app.config["DB_USER"],
                password=app.config["DB_PASSWORD"],
            )
            cur = conn.cursor()

            # Advisory lock — only one process can hold it
            cur.execute("SELECT GET_LOCK('pca_schedule_gen', 0)")
            got_lock = cur.fetchone()[0]
            if not got_lock:
                log.info("Another process is generating the schedule — skipping.")
                cur.close()
                conn.close()
                return

            # Check for flights on the template date — not just any flights.
            # A stale DB volume may have old flights from a previous init.sql
            # that don't match the scheduler's TEMPLATE_DATE.
            cur.execute(
                "SELECT COUNT(*) FROM flights WHERE scheduled_departure >= %s AND scheduled_departure < %s",
                (app.config.get("TEMPLATE_RANGE_START", "2026-03-09 00:00:00"),
                 app.config.get("TEMPLATE_RANGE_END", "2026-03-11 00:00:00")),
            )
            count = cur.fetchone()[0]

            if count < 200:
                log.info(f"Only {count} flights on template date — generating timetable…")
                from .services.scheduler import generate_schedule
                total = generate_schedule(conn)
                log.info(f"Timetable generated: {total} template flights.")
            else:
                log.info(f"Template timetable OK ({count} flights) — skipping generation.")

            cur.execute("SELECT RELEASE_LOCK('pca_schedule_gen')")
            cur.fetchone()
            cur.close()
            conn.close()
            return
        except mysql.connector.Error as e:
            log.warning(f"Schedule seed DB not ready (attempt {attempt + 1}/10): {e}")
            time.sleep(5)

    log.error("Could not seed schedule — DB never became ready.")
