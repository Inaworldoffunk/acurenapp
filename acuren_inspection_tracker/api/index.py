from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename
import numpy as np

# IMPORTANT: SQLite is not supported on Vercel for persistent storage.
# You need to replace this with an external database like PostgreSQL (Neon, Supabase, etc.)
# or a cloud-based NoSQL database.
# For demonstration, we'll comment out SQLite related parts that cause issues on Vercel.
# In a real application, you would configure your database connection here.

# app = Flask(__name__, static_folder=".") # Original line
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = "." # Vercel only allows writing to /tmp, but for static files, we'll assume they are pre-built
ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload directory exists (not strictly needed for Vercel, as /tmp is writable)
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization (COMMENTED OUT FOR VERCEL COMPATIBILITY)
# In a real scenario, you would connect to an external database here.
# def init_db():
#     conn = sqlite3.connect("inspection_tracker.db")
#     cursor = conn.cursor()
#     # ... (all table creation SQL statements)
#     conn.commit()
#     conn.close()

# Placeholder for database connection - REPLACE WITH YOUR ACTUAL DB CONNECTION
# For Vercel, you'd typically use environment variables for connection strings.
# Example for PostgreSQL with psycopg2:
# import psycopg2
# def get_db_connection():
#     conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
#     return conn

# For now, we'll use a dummy connection or mock data for Vercel deployment
# This will cause API routes to fail without a real database.
# The primary goal here is to get the Flask app to *start* without crashing.

def get_db_connection():
    # This is a placeholder. On Vercel, you cannot use local SQLite files.
    # You MUST replace this with a connection to an external database (e.g., PostgreSQL, MongoDB).
    # For local testing, you can uncomment the sqlite3 line and ensure inspection_tracker.db exists.
    # return sqlite3.connect("inspection_tracker.db")
    raise Exception("Database connection not configured for Vercel. Please use an external database.")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes

@app.route("/")
def index():
    # Vercel serves static files directly from the `static` folder defined in vercel.json
    # This route is typically not needed for serving the main index.html if it's a static site.
    # However, if you want Flask to serve it, ensure `static_folder` is configured correctly.
    return send_from_directory("static", "index.html")

@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# All other API routes will attempt to connect to the database
# and will fail until a proper external database is configured.

# Enhanced Dashboard Routes
@app.route("/api/dashboard/overview")
def dashboard_overview():
    conn = get_db_connection()
    # ... (rest of the dashboard_overview logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/analytics/process-performance")
def process_performance():
    conn = get_db_connection()
    # ... (rest of the process_performance logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/analytics/predictive-insights")
def predictive_insights():
    conn = get_db_connection()
    # ... (rest of the predictive_insights logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/scope/upload", methods=["POST"])
def upload_scope_enhanced():
    # ... (rest of the upload_scope_enhanced logic)
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/scope/review/<int:upload_id>", methods=["PUT"])
def review_scope(upload_id):
    # ... (rest of the review_scope logic)
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/tasks/assign", methods=["POST"])
def assign_task():
    # ... (rest of the assign_task logic)
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/reports/generate", methods=["POST"])
def generate_progress_report():
    # ... (rest of the generate_progress_report logic)
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    # ... (rest of the get_tasks logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    conn = get_db_connection()
    # ... (rest of the get_task logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/tasks/<int:task_id>/claim", methods=["POST"])
def claim_task(task_id):
    conn = get_db_connection()
    # ... (rest of the claim_task logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/tasks/<int:task_id>/update", methods=["PUT"])
def update_task(task_id):
    conn = get_db_connection()
    # ... (rest of the update_task logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/lookups/inspectors")
def get_inspectors():
    conn = get_db_connection()
    # ... (rest of the get_inspectors logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/lookups/sites")
def get_sites():
    conn = get_db_connection()
    # ... (rest of the get_sites logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/lookups/methods")
def get_methods():
    conn = get_db_connection()
    # ... (rest of the get_methods logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

@app.route("/api/lookups/status-types")
def get_status_types():
    conn = get_db_connection()
    # ... (rest of the get_status_types logic)
    conn.close()
    return jsonify({"error": "Database not configured for Vercel deployment."}), 500

# The `if __name__ == '__main__':` block is not executed in Vercel serverless functions.
# Vercel expects a `handler` or `app` object to be directly importable.
# init_db() # This line would cause a crash on Vercel due to SQLite.
# app.run(host='0.0.0.0', port=5000, debug=False)

# To make it work with Vercel, ensure your `vercel.json` points to `api/index.py`
# and Vercel will automatically find the `app` object.

