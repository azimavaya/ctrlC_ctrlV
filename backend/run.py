"""
run.py — Flask application entry point for Panther Cloud Air (PCA).
CSC 4710 Software Engineering, Spring 2026 — Team ctrlC+ctrlV.

Starts the development server on port 5000 with hot-reload enabled.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
