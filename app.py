import os
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

from services.db_service import init_db
from utils.logger import logger
from utils.error_handlers import register_error_handlers

from routes.chat_routes import chat_bp
from routes.complaint_routes import complaint_bp
from routes.visitor_routes import visitor_bp
from routes.room_routes import room_bp
from routes.leave_routes import leave_bp
from routes.info_routes import info_bp
from routes.student_routes import student_bp

def create_app():
    """Factory function to configure and initialize Flask Application."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Initialize Database Schema & Seed Data if not present
    init_db()

    # Register Error Handlers
    register_error_handlers(app)

    # Register Blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(visitor_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(info_bp)
    app.register_blueprint(student_bp)

    @app.route("/")
    def index():
        """Student Chat Interface Page"""
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        """Admin / Warden Management Dashboard Page"""
        return render_template("dashboard.html")

    return app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "t"]
    
    logger.info(f"Starting Smart Hostel Management System server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
