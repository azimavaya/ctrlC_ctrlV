# Flask entry point for Panther Cloud Air.
# Starts the dev server on port 5000 with hot-reload enabled.

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
